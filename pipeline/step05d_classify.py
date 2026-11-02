#!/usr/bin/env python3
"""Step 5d - suggest whether each title is a Portuguese production (issue #58).

RTP labels every subtitle track the same way, so foreign films and international
documentaries end up in the Portuguese sections until a person moves them (the
weekly review). This step asks Claude, for each title in the Portuguese series,
films and documentaries sections: is it a Portuguese production, a foreign
production, or unsure? Given the title, English title, link slug, description,
channel, RTP's collection tags and the credits on the programme page (Produção,
Realização, Intérpretes...), it returns a verdict and a one-line reason.

Nature & science is a deliberate mix of Portuguese-made and acquired
documentaries, so it is not checked (decision 0010). Titles in
`confirmed_portuguese` in config/overrides.json are never asked about.

It never changes a section. Suggestions are cached in data/classify.json, keyed by
programme id plus a hash of the description, so a title is asked about once
unless its description changes. The weekly review shows them next to each new
title; a person still decides.

    python step05d_classify.py                 # classify titles not yet in the cache
    python step05d_classify.py --suspects FILE # also write a Markdown table of foreign/unsure titles
    python step05d_classify.py --recheck-unsure --suspects FILE
                                               # ask again about "unsure" titles from before credits were used
    python step05d_classify.py --optional      # weekly run: skip quietly without an API key

Needs ANTHROPIC_API_KEY. Collection tags come from data/subtitles.json when a full
rebuild has just run; otherwise each title's episode page is fetched for them.
Credits come from the programme page, /play/p<pid>/.
"""
from __future__ import annotations

import argparse
import hashlib
import html as htmllib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from common import WORKERS, fetch, load_json, log, save_json

MODEL = os.environ.get("RTP_CLASSIFY_MODEL", "claude-sonnet-5-5")
BATCH = 20
SECTIONS = {"series", "film", "docs"}          # not "nature": a mixed section by design (decision 0010)
CONFIG = Path(__file__).resolve().parent / "config" / "overrides.json"
COLLECTION_RE = re.compile(r"Este conte(?:ú|&uacute;)do faz parte de ([^<]{1,80})")
KEYWORDS_RE = re.compile(r'<meta name="keywords" content="([^"]*)"')
CREDIT_RE = re.compile(r'<p class="technical[^"]*">\s*<b>([^<]{1,40})</b>\s*([^<]{1,300})</p')
STAMP_RE = re.compile(r'<span class="stamp">([^<]{1,60})</span>')

SYSTEM = """You help maintain a list of RTP Play (Portuguese public TV) programmes with Portuguese captions, for learners of European Portuguese. RTP labels every Portuguese text track the same way, so foreign films and series (where the Portuguese text is a translation) and documentaries made abroad must be told apart from Portuguese productions.

For each item decide where it was produced:
- "portuguese": made in Portugal (or a Portuguese-led co-production), so the audio is mainly European Portuguese. Brazilian or other Lusophone productions also count as "portuguese" here, but say so in the reason (e.g. "Brazilian film").
- "foreign": made outside the Portuguese-speaking world (e.g. a US, French, Spanish or German film or series, or a documentary acquired from another broadcaster); the audio is another language or dubbed.
- "unsure": the evidence doesn't settle it.

Use everything given: the Portuguese title and its English translation (a well-known foreign title is a strong sign), the link slug (foreign originals often keep their original title, e.g. "le-nouveau", "collateral-beauty"), the description (places, people, subject), the channel and RTP's collection tags ("Cinema Internacional", "Séries Estrangeiras" point to foreign; "Séries nacionais", "Cinema Português", "RTP Lab" point to Portuguese; a documentary about a foreign place or subject is usually acquired), and the credits from RTP's programme page when given (production company, director, cast: Portuguese companies and names point to Portuguese; a foreign broadcaster or studio, or foreign names, point to foreign). Don't guess: if the signals conflict or are thin, answer "unsure".

Give a one-line reason (under 20 words) naming the deciding clue."""

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pid": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["portuguese", "foreign", "unsure"]},
                    "reason": {"type": "string"},
                },
                "required": ["pid", "verdict", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


def pid_of(url: str) -> str | None:
    m = re.search(r"/play/(?:zigzag/)?p(\d+)/", url or "")
    return m.group(1) if m else None


def cache_key(pid: str, desc: str) -> str:
    return f"{pid}:{hashlib.sha256((desc or '').encode()).hexdigest()[:12]}"


def tags_for(row: dict, subs: dict) -> tuple[str, list[str]]:
    """(channel and genre keywords, collection tags) for a row."""
    s = subs.get(pid_of(row["u"]) or "")
    if s:
        return s.get("keywords", ""), s.get("collections", [])
    try:
        page = fetch(row["u"].replace("/play/zigzag/", "/play/"))
    except Exception:                             # noqa: BLE001
        return row.get("c", ""), []
    kw = KEYWORDS_RE.search(page)
    return (htmllib.unescape(kw.group(1)) if kw else row.get("c", ""),
            [htmllib.unescape(c).strip() for c in COLLECTION_RE.findall(page)][:6])


def credits_for(pid: str) -> str:
    """The programme page's credits and RTP's labels, as one line of evidence."""
    try:
        page = fetch(f"/play/p{pid}/")
    except Exception:                             # noqa: BLE001
        return ""
    parts = [f"{htmllib.unescape(k).strip().rstrip(':')}: {htmllib.unescape(v).strip()}"
             for k, v in CREDIT_RE.findall(page)]
    stamps = [htmllib.unescape(t).strip() for t in STAMP_RE.findall(page)]
    stamps = [t for t in stamps if not re.fullmatch(r"\d+AP|M/?\d+|\w", t)]   # drop age ratings, "S"
    cols = [htmllib.unescape(c).strip() for c in COLLECTION_RE.findall(page)]
    if stamps:
        parts.append("RTP labels: " + ", ".join(dict.fromkeys(stamps)))
    if cols:
        parts.append("Part of: " + ", ".join(dict.fromkeys(cols)))
    return "; ".join(parts)[:400]


def classify(client, items: list[dict]) -> tuple[list[dict], dict]:
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",                        # re-run on a fallback model if this one declines
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(items, ensure_ascii=False)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("declined")
    text = next(b.text for b in response.content if b.type == "text")
    u = response.usage
    return json.loads(text)["items"], {"in": u.input_tokens, "out": u.output_tokens}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suspects", help="write a Markdown table of foreign/unsure titles to this file")
    ap.add_argument("--recheck-unsure", action="store_true",
                    help="ask again, with the programme page's credits, about titles answered 'unsure' without them")
    ap.add_argument("--optional", action="store_true", help="skip quietly when there is no API key (weekly run)")
    ap.add_argument("--no-api", action="store_true", help="don't call the API at all")
    args = ap.parse_args()

    confirmed = json.loads(CONFIG.read_text(encoding="utf-8")).get("confirmed_portuguese", {})
    rows = [r for r in (load_json("dataset.json") or []) if r["s"] in SECTIONS and not r.get("grace")
            and pid_of(r["u"]) and pid_of(r["u"]) not in confirmed]
    subs = load_json("subtitles.json") or {}
    cache = load_json("classify.json") or {}
    if args.recheck_unsure:
        todo = [r for r in rows if (c := cache.get(cache_key(pid_of(r["u"]), r["x"])))
                and c["verdict"] == "unsure" and not c.get("evidence")]
    else:
        todo = [r for r in rows if cache_key(pid_of(r["u"]), r["x"]) not in cache]
    log(f"classify: {len(rows)} titles in series/films/docs (not yet confirmed), {len(todo)} to ask about"
        + (" again with credits" if args.recheck_unsure else ""))

    if todo and (args.no_api or not os.environ.get("ANTHROPIC_API_KEY")):
        if args.no_api or args.optional:
            log("classify: no API key (or --no-api); skipping")
            todo = []
        else:
            raise SystemExit("set ANTHROPIC_API_KEY")
    if todo:
        import anthropic
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            tags = list(ex.map(lambda r: tags_for(r, subs), todo))
            credits = list(ex.map(lambda r: credits_for(pid_of(r["u"])), todo))
        items = [{"pid": pid_of(r["u"]), "title": r["n"], "english_title": r.get("ne", ""),
                  "slug": r["u"].rstrip("/").rsplit("/", 1)[-1], "description": r["x"],
                  "channel_and_genre": kw, "rtp_collections": cols, "credits": cr}
                 for r, (kw, cols), cr in zip(todo, tags, credits)]
        client = anthropic.Anthropic()
        spent = {"in": 0, "out": 0}
        by_pid = {it["pid"]: (r, it) for it, r in zip(items, todo)}
        for start in range(0, len(items), BATCH):
            chunk = items[start:start + BATCH]
            try:
                out, use = classify(client, chunk)
            except Exception as e:                # noqa: BLE001 - leave these for the next run
                log(f"  batch {start // BATCH} failed: {e}")
                continue
            spent = {k: spent[k] + use[k] for k in spent}
            for o in out:
                if o["pid"] in by_pid:
                    r, it = by_pid[o["pid"]]
                    key = cache_key(o["pid"], r["x"])
                    cache[key] = {"pid": o["pid"], "n": r["n"], "verdict": o["verdict"], "reason": o["reason"],
                                  "evidence": it["credits"], "model": MODEL, "date": date.today().isoformat(),
                                  **({"was": cache[key]["verdict"]} if args.recheck_unsure and key in cache else {})}
            save_json("classify.json", cache)
            log(f"  classified {min(start + BATCH, len(items))}/{len(items)}")
        cost = spent["in"] / 1e6 * 2.00 + spent["out"] / 1e6 * 10.00   # claude-sonnet-5-5: $2 / $10 per MTok
        log(f"classify: {spent['in']:,} input + {spent['out']:,} output tokens ≈ ${cost:.2f}")
        print(f"tokens_in={spent['in']}\ntokens_out={spent['out']}\ncost_usd={cost:.2f}")

    if args.suspects:
        names = {"series": "Portuguese TV series", "film": "Portuguese films", "docs": "Documentaries (Portugal)"}
        asked = {pid_of(r["u"]) for r in todo} if args.recheck_unsure else None
        sus, resolved = [], []
        for r in rows:
            p = pid_of(r["u"])
            c = cache.get(cache_key(p, r["x"]))
            if not c or (asked is not None and p not in asked):
                continue
            if c["verdict"] != "portuguese":
                sus.append((c["verdict"], names[r["s"]], r, c))
            elif asked is not None:
                resolved.append((r, c))
        sus.sort(key=lambda t: (t[0] != "foreign", t[1], t[2]["n"]))
        md = ["| # | Title | Now in | pid | Suggestion | Reason | Evidence from RTP's page |",
              "|---|---|---|---|---|---|---|"]
        for i, (v, sec, r, c) in enumerate(sus, 1):
            md.append(f"| {i} | [{r['n']}]({r['u']}) | {sec} | {pid_of(r['u'])} | **{v}** | {c['reason']} | "
                      f"{(c.get('evidence') or '(none found)').replace('|', '/')} |")
        if resolved:
            md += ["", f"Resolved as Portuguese by this pass ({len(resolved)}), to add to `confirmed_portuguese`:", ""]
            md += [f"- {r['n']} (pid `{pid_of(r['u'])}`): {c['reason']}" for r, c in resolved]
        open(args.suspects, "w", encoding="utf-8").write("\n".join(md) + "\n")
        log(f"suspects: {sum(1 for s in sus if s[0] == 'foreign')} foreign, "
            f"{sum(1 for s in sus if s[0] == 'unsure')} unsure, {len(resolved)} resolved as Portuguese")


if __name__ == "__main__":
    main()
