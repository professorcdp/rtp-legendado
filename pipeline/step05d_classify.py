#!/usr/bin/env python3
"""Step 5d - suggest whether each title is a Portuguese production (issue #58).

RTP labels every subtitle track the same way, so foreign films and international
documentaries end up in the Portuguese sections until a person moves them (the
weekly review). This step asks Claude, for each title in the Portuguese series,
films, documentaries and nature sections: is it a Portuguese production, a
foreign production, or unsure? Given the title, English title, link slug,
description, channel and RTP's collection tags, it returns a verdict and a
one-line reason.

It never changes a section. Suggestions are cached in data/classify.json, keyed by
programme id plus a hash of the description, so a title is asked about once
unless its description changes. The weekly review shows them next to each new
title; a person still decides.

    python step05d_classify.py                 # classify titles not yet in the cache
    python step05d_classify.py --suspects FILE # also write a Markdown table of foreign/unsure titles

Needs ANTHROPIC_API_KEY. Collection tags come from data/subtitles.json when a full
rebuild has just run; otherwise each title's episode page is fetched for them.
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

from common import WORKERS, fetch, load_json, log, save_json

MODEL = os.environ.get("RTP_CLASSIFY_MODEL", "claude-sonnet-5-5")
BATCH = 20
SECTIONS = {"series", "film", "docs", "nature"}
COLLECTION_RE = re.compile(r"Este conte(?:ú|&uacute;)do faz parte de ([^<]{1,80})")
KEYWORDS_RE = re.compile(r'<meta name="keywords" content="([^"]*)"')

SYSTEM = """You help maintain a list of RTP Play (Portuguese public TV) programmes with Portuguese captions, for learners of European Portuguese. RTP labels every Portuguese text track the same way, so foreign films and series (where the Portuguese text is a translation) and documentaries made abroad must be told apart from Portuguese productions.

For each item decide where it was produced:
- "portuguese": made in Portugal (or a Portuguese-led co-production), so the audio is mainly European Portuguese. Brazilian or other Lusophone productions also count as "portuguese" here, but say so in the reason (e.g. "Brazilian film").
- "foreign": made outside the Portuguese-speaking world (e.g. a US, French, Spanish or German film or series, or a documentary acquired from another broadcaster); the audio is another language or dubbed.
- "unsure": the evidence doesn't settle it.

Use everything given: the Portuguese title and its English translation (a well-known foreign title is a strong sign), the link slug (foreign originals often keep their original title, e.g. "le-nouveau", "collateral-beauty"), the description (places, people, subject), the channel and RTP's collection tags ("Cinema Internacional", "Séries Estrangeiras" point to foreign; "Séries nacionais", "Cinema Português", "RTP Lab" point to Portuguese; a documentary about a foreign place or subject is usually acquired). Don't guess: if the signals conflict or are thin, answer "unsure".

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
    args = ap.parse_args()

    rows = [r for r in (load_json("dataset.json") or []) if r["s"] in SECTIONS and not r.get("grace")]
    subs = load_json("subtitles.json") or {}
    cache = load_json("classify.json") or {}
    todo = [r for r in rows if pid_of(r["u"]) and cache_key(pid_of(r["u"]), r["x"]) not in cache]
    log(f"classify: {len(rows)} titles in series/films/docs/nature, {len(todo)} not yet classified")

    if todo:
        import anthropic
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit("set ANTHROPIC_API_KEY")
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            tags = list(ex.map(lambda r: tags_for(r, subs), todo))
        items = [{"pid": pid_of(r["u"]), "title": r["n"], "english_title": r.get("ne", ""),
                  "slug": r["u"].rstrip("/").rsplit("/", 1)[-1], "description": r["x"],
                  "channel_and_genre": kw, "rtp_collections": cols}
                 for r, (kw, cols) in zip(todo, tags)]
        client = anthropic.Anthropic()
        spent = {"in": 0, "out": 0}
        by_pid = {it["pid"]: r for it, r in zip(items, todo)}
        for start in range(0, len(items), BATCH):
            chunk = items[start:start + BATCH]
            try:
                out, use = classify(client, chunk)
            except Exception as e:                # noqa: BLE001 - leave these for the next run
                log(f"  batch {start // BATCH} failed: {e}")
                continue
            spent = {k: spent[k] + use[k] for k in spent}
            for o in out:
                r = by_pid.get(o["pid"])
                if r:
                    cache[cache_key(o["pid"], r["x"])] = {"pid": o["pid"], "n": r["n"], "verdict": o["verdict"],
                                                          "reason": o["reason"], "model": MODEL,
                                                          "date": date.today().isoformat()}
            save_json("classify.json", cache)
            log(f"  classified {min(start + BATCH, len(items))}/{len(items)}")
        cost = spent["in"] / 1e6 * 2.00 + spent["out"] / 1e6 * 10.00   # claude-sonnet-5-5: $2 / $10 per MTok
        log(f"classify: {spent['in']:,} input + {spent['out']:,} output tokens ≈ ${cost:.2f}")
        print(f"tokens_in={spent['in']}\ntokens_out={spent['out']}\ncost_usd={cost:.2f}")

    if args.suspects:
        names = {"series": "Portuguese TV series", "film": "Portuguese films", "docs": "Documentaries (Portugal)",
                 "nature": "Nature & science"}
        sus = []
        for r in rows:
            c = cache.get(cache_key(pid_of(r["u"]) or "", r["x"]))
            if c and c["verdict"] != "portuguese":
                sus.append((c["verdict"], names[r["s"]], r, c))
        sus.sort(key=lambda t: (t[0] != "foreign", t[1], t[2]["n"]))
        md = [f"| # | Title | Now in | pid | Suggestion | Reason |", "|---|---|---|---|---|---|"]
        for i, (v, sec, r, c) in enumerate(sus, 1):
            md.append(f"| {i} | [{r['n']}]({r['u']}) | {sec} | {pid_of(r['u'])} | **{v}** | {c['reason']} |")
        open(args.suspects, "w", encoding="utf-8").write("\n".join(md) + "\n")
        log(f"suspects: {sum(1 for s in sus if s[0] == 'foreign')} foreign, {sum(1 for s in sus if s[0] == 'unsure')} unsure")


if __name__ == "__main__":
    main()
