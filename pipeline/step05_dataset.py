#!/usr/bin/env python3
"""Step 5 - assign sections, merge seasons, fold in rights and synopses.

Produces the dataset the page is rendered from. Two things happen here.

1. SECTIONS. RTP's own category (`cats`), channel (`keywords`) and collection
   tags ("Séries nacionais", "Cinema Português", "Cinema Internacional",
   "Teatro", "Documentários de Ciência e Natureza"...) drive a rule cascade.
   RTP tags every subtitle track "Português adaptado" whether it is SDH on
   Portuguese audio or a translation of a foreign film, so foreign-language
   fiction and acquired international documentaries cannot be detected from
   the track - they are listed by hand in config/overrides.json.

2. MERGING. A show with several seasons appears as several programme ids
   ("Água de Mar" has three). Entries are merged by normalised title, keeping
   every season's link; films stay separate from series of the same name. The
   row's main link prefers a season without a Portugal-only licence.

PORTUGAL-ONLY LICENCE. Files licensed for Portugal only sit under a `/pt/` path
segment in the player's fileKey. Unlike the rights service's answer, that flag
doesn't depend on where the rebuild runs, so it is what the page publishes
(`pt`: 1 when every season of a row is Portugal-only). The rights answer from
the build machine is kept as `r`/`ok` for reference.

Run it once before step 4 to produce data/dataset_draft.json (which tells step 4
which programmes need a show-level description), then again afterwards.

Output: data/dataset_draft.json and data/dataset.json
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import re
from collections import Counter
from pathlib import Path

from common import DATA, date_key, load_json, log, save_json

CONFIG = Path(__file__).resolve().parent / "config" / "overrides.json"

# Section order used when the same title lands in two sections after merging.
PRIORITY = ["foreign", "series", "lang", "fun", "food", "music", "stage",
            "kids", "nature", "intl", "docs", "mag"]


def channel_of(keywords: str, name: str) -> str:
    """Channel from the episode page's keywords.

    September 2026: "RTP1|Ficção, ...". October 2026: "Title, RTP2, Cultura, date, ...".
    """
    parts = [p.strip() for p in (keywords or "").split(",")]
    if "|" in parts[0]:
        return parts[0].split("|")[0].strip()
    if len(parts) > 1 and parts[0].lower() == name.lower():
        return parts[1]
    return parts[0]


def section_for(pid: str, name: str, cats, keywords: str, collections, episodes: int, ov) -> str:
    cols = "|".join(collections)
    kw = keywords or ""
    if pid in ov["foreign_fiction"]:
        return "foreign"
    if pid in ov["language_and_literature"]:
        return "lang"
    if "infantis-e-juvenis" in cats:
        return "kids"
    if "ficcao" in cats and ("Teatro" in cols or "Teatr" in kw):
        return "stage"
    if "ficcao" in cats:
        is_film = (any(t in cols for t in ("Cinema Português", "Filmes Portugueses", "Cinema Internacional"))
                   or (episodes <= 2 and "Séries" not in cols and "Minissérie" not in name))
        return "film" if is_film else "series"
    if pid in ov["international_documentary"]:
        return "intl"
    if ("musica" in cats or "Musicais" in kw or "Música" in kw or "Concertos" in cols
            or ("artes" in cats and "Musicais" in kw)):
        return "music"
    if "Teatro" in cols:
        return "stage"
    if "humor" in cats or "entretenimento" in cats:
        return "fun"
    if "gastronomia" in cats:
        return "food"
    if ("ciencia-e-natureza" in cats
            or re.search(r"Ciência e Natureza|Ecologia|Ciência, Tecnologia", cols)
            or re.search(r"Biosfera", name)):
        return "nature"
    if (any(c in cats for c in ("informacao", "entrevista-opiniao-e-debate", "institucionais", "saude"))
            or ("outros" in cats and episodes >= 8)):
        return "mag"
    return "docs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-only", action="store_true",
                    help="write dataset_draft.json only (run before step 4)")
    args = ap.parse_args()

    ov = json.loads(CONFIG.read_text(encoding="utf-8"))
    ov = {k: (set(v) if isinstance(v, list) else v) for k, v in ov.items()}
    excl = re.compile(ov["exclude_title_pattern"], re.I)

    catalogue = load_json("catalogue.json") or {}
    subs = load_json("subtitles.json") or {}
    rights = load_json("rights.json", {}) or {}
    synopses = load_json("synopses.json", {}) or {}
    if not subs:
        raise SystemExit("run steps 1-2 first")

    pid_section, groups = {}, {}
    for pid, s in subs.items():
        if not s.get("has_subs"):
            continue
        stats = s.get("vtt_stats") or [0]
        if isinstance(stats[0], int) and stats[0] < ov["min_subtitle_lines"]:
            continue                                   # empty or stub subtitle file
        cat = catalogue.get(pid, {})
        name = htmllib.unescape(htmllib.unescape(s.get("program_title") or cat.get("title", ""))).strip()
        if not name or excl.search(name):
            continue
        name = ov["rename"].get(pid, name)
        episodes = int(s.get("episodes") or 0)
        sec = section_for(pid, name, cat.get("cats", []), s.get("keywords", ""),
                          s.get("collections", []), episodes, ov)
        pid_section[pid] = {"section": sec, "episodes": episodes, "name": name}

        # merge by normalised title; films stay separate from series
        key = ("film" if sec == "film" else "x", re.sub(r"\s+", " ", name.lower()).strip())
        g = groups.setdefault(key, {"section": sec, "name": name, "items": []})
        if key[0] == "x" and PRIORITY.index(sec) < PRIORITY.index(g["section"]):
            g["section"] = sec
        date = ""
        m = re.search(r"\d{2} \w{3}\.? \d{4}$", cat.get("meta", ""))
        if m:
            date = m.group(0)
        desc = synopses.get(pid) or htmllib.unescape(s.get("desc", ""))[:160]
        g["items"].append({
            "pid": pid,
            "url": "https://www.rtp.pt" + cat.get("url", f"/play/p{pid}/"),
            "date": date,
            "eps": episodes,
            "channel": channel_of(s.get("keywords", ""), name),
            "desc": re.sub(r"\s+", " ", desc),
            "show_level": pid in synopses,
            "rights": (rights.get(pid) or {}).get("rights"),
            "pt_only": "/pt/" in (s.get("file_key") or ""),
            "note": ov["notes"].get(pid, ""),
            "tag": ov.get("page_notes", {}).get(pid, ""),
        })

    if args.draft_only:
        save_json("dataset_draft.json", {"pid_section": pid_section})
        log(f"draft: {len(pid_section)} subtitled programmes, "
            f"{Counter(v['section'] for v in pid_section.values())}")
        return

    rows = []
    for g in groups.values():
        g["items"].sort(key=lambda i: date_key(i["date"]), reverse=True)
        main_item = g["items"][0]
        # prefer a season without a Portugal-only licence as the row's main link
        if main_item["pt_only"]:
            for i, it in enumerate(g["items"]):
                if not it["pt_only"]:
                    g["items"][0], g["items"][i] = it, main_item
                    main_item = it
                    break
        rows.append({
            "s": g["section"],
            "n": g["name"],
            "u": main_item["url"],
            "d": main_item["date"],
            "dk": "%04d%02d%02d" % date_key(main_item["date"]),
            "e": max(i["eps"] for i in g["items"]),
            "c": main_item["channel"],
            "x": main_item["desc"],
            "xs": 1 if main_item["show_level"] else 0,
            "note": next((i["note"] for i in g["items"] if i["note"]), ""),
            "tag": next((i["tag"] for i in g["items"] if i["tag"]), ""),
            "r": main_item["rights"],
            "ok": 1 if any(i["rights"] == 1 for i in g["items"]) else 0,
            "pt": 1 if all(i["pt_only"] for i in g["items"]) else 0,
            "more": [{"u": i["url"], "d": i["date"], "r": i["rights"], "pt": 1 if i["pt_only"] else 0}
                     for i in g["items"][1:]],
        })

    rows.sort(key=lambda o: (o["s"], -int(o["dk"])))
    save_json("dataset_draft.json", {"pid_section": pid_section})
    save_json("dataset.json", rows)
    log(f"dataset: {len(rows)} rows, {sum(r['pt'] for r in rows)} with a Portugal-only licence, "
        f"{sum(r['ok'] for r in rows)} playable from the build machine")
    log("  " + ", ".join(f"{k}:{v}" for k, v in sorted(Counter(r["s"] for r in rows).items())))


if __name__ == "__main__":
    main()
