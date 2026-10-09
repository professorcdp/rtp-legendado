#!/usr/bin/env python3
"""Step 4 - fetch show-level descriptions for series and recurring programmes.

An episode blurb for episode 15 of a sitcom tells a learner nothing about the
sitcom. For anything that is a series or a recurring strand, the programme page
at /play/p<pid>/ carries a description of the show itself:

  - <meta name="description"> - a one-line tagline
  - the longest <p> in the body - usually a fuller synopsis

Credit lists ("Intérpretes:", "Autoria:", "Realização...") are skipped. The
longer of the two surviving candidates wins, capped at 400 characters.

Which programmes get this treatment is decided in step 5's sections, so this
step takes the set from data/dataset_draft.json if present, otherwise applies
the same rule directly: series + recurring programmes (>= 8 episodes) +
entertainment, kids, magazines, food and language strands.

Output: data/synopses.json {pid: "..."}
"""
from __future__ import annotations

import argparse
import html as htmllib
import re
from concurrent.futures import ThreadPoolExecutor

from common import fetch, load_json, log, save_json, WORKERS

CREDITS_RE = re.compile(r"^(Intérpretes|Autoria|Realiza|Argumento|Elenco|Produção|Ficha)", re.I)
META_RE = re.compile(r'<meta name="description" content="([^"]*)"')
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
SECTIONS_WITH_SYNOPSIS = {"series", "fun", "kids", "mag", "food", "lang"}
RECURRING_MIN_EPISODES = 8


def clean(s: str) -> str:
    s = htmllib.unescape(TAG_RE.sub(" ", s))
    return re.sub(r"\s+", " ", s).strip()


def synopsis_for(pid: str):
    try:
        page = fetch(f"/play/p{pid}/")
    except Exception as e:                        # noqa: BLE001
        return pid, ""
    meta = clean(META_RE.search(page).group(1)) if META_RE.search(page) else ""
    paras = [clean(p) for p in P_RE.findall(page)]
    paras = [p for p in paras
             if len(p) > 60 and not CREDITS_RE.match(p) and "cookies" not in p.lower()]
    best = max([meta, *paras], key=len) if (meta or paras) else ""
    best = re.sub(r"&[a-zA-Z]{1,6};?$", "", best).strip()[:400]
    if best and not re.search(r"[.!?…]$", best):   # RTP truncates its own blurbs
        best = best.rstrip(" ,;:-") + "…"
    return pid, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()

    draft = load_json("dataset_draft.json")
    subs = load_json("subtitles.json") or {}
    if draft:
        wanted = {pid for pid, rec in draft["pid_section"].items()
                  if rec["section"] in SECTIONS_WITH_SYNOPSIS
                  or (rec["section"] in {"docs", "nature", "intl"} and rec["episodes"] >= RECURRING_MIN_EPISODES)}
    else:
        wanted = {v["pid"] for v in subs.values()
                  if v.get("has_subs") and v.get("episodes", 0) >= RECURRING_MIN_EPISODES}

    done = {} if args.redo else (load_json("synopses.json", {}) or {})
    todo = sorted(wanted - set(done))
    log(f"fetching {len(todo)} programme pages for show-level descriptions")

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for pid, text in ex.map(synopsis_for, todo):
            if len(text) >= 30:                   # anything shorter is not a description
                done[pid] = text

    save_json("synopses.json", done)
    log(f"done: {len(done)} show-level descriptions")


if __name__ == "__main__":
    main()
