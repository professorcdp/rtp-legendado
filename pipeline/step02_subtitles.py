#!/usr/bin/env python3
"""Step 2 - check each TV programme's latest episode for a Portuguese subtitle track.

For every TV programme in data/catalogue.json, fetch the latest episode page and
look for the player's `vtt:` line. Also record the fileKey (needed by step 3),
the page's own metadata (keywords, description, collections) and the number of
episodes the page links to.

A second, optional pass downloads each .vtt file and counts SDH sound cues
(`RISOS`, `MÚSICA`, `GEME`, `NARRADORA:`), which helps tell same-language
captions from translation subtitles, and catches empty subtitle files.

Output: data/subtitles.json {pid: {...}}  - resumable, re-run to fill gaps.
"""
from __future__ import annotations

import argparse
import html as htmllib
import re
from concurrent.futures import ThreadPoolExecutor

from common import (WORKERS, fetch, file_key, load_json, log, save_json,
                    subtitle_track)

EPISODE_RE_TMPL = r"/play/p{pid}/e(\d+)"
KEYWORDS_RE = re.compile(r'<meta name="keywords" content="([^"]*)"')
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
OGTITLE_RE = re.compile(r'<meta property="og:title" content="([^"]*)"')
# RTP writes this heading with the accent as an HTML entity since October 2026
# ("Este conte&uacute;do faz parte de ..."), so accept both spellings.
COLLECTION_RE = re.compile(r"Este conte(?:ú|&uacute;)do faz parte de ([^<]{1,80})")

# Sound cues typical of SDH (captions for deaf viewers) - near-absent in
# translation subtitles for foreign-language audio.
CUE_RE = re.compile(
    r"^(?:[-– ]*)(M[ÚU]SICA|RISOS?|RI|RIEM|SUSPIRA|GEME|GEMIDOS?|TOSSE|APLAUSOS|CHORA|GRITA|"
    r"ARFA|BATE|CAMPAINHA|TELEFONE|PASSOS|RESPIRA|NARRADORA?|VOZ OFF|OFF|CANTA|SIL[ÊE]NCIO|"
    r"RU[ÍI]DO|BARULHO|ESTRONDO|C[ÃA]O|LADRA|PORTA)\b")
CAPS_RE = re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇÀ ,:.!?'-]{3,}$")


def analyse_vtt(url: str):
    """Return (n_lines, n_sound_cues, n_all_caps_lines) for a .vtt file."""
    try:
        text = fetch(url)
    except Exception as e:                        # noqa: BLE001
        return ("err", str(e)[:80], 0)
    lines = [s.strip() for s in text.split("\n")]
    lines = [s for s in lines if s and not re.search(r"-->|^\d+$|WEBVTT", s)]
    cues = sum(1 for s in lines if CUE_RE.match(s))
    caps = sum(1 for s in lines if CAPS_RE.match(s))
    return (len(lines), cues, caps)


def check_one(rec: dict, want_vtt_stats: bool) -> dict:
    pid = rec["pid"]
    out = {"pid": pid}
    try:
        page = fetch(rec["url"])
    except Exception as e:                        # noqa: BLE001
        return {**out, "error": str(e)[:120]}

    track = subtitle_track(page)
    out["has_subs"] = bool(track)
    if track:
        out["label"], out["vtt"] = track
    out["file_key"] = file_key(page)

    kw = KEYWORDS_RE.search(page)
    desc = DESC_RE.search(page)
    og = OGTITLE_RE.search(page)
    out["keywords"] = htmllib.unescape(kw.group(1)) if kw else ""
    out["desc"] = htmllib.unescape(desc.group(1))[:240] if desc else ""
    out["program_title"] = htmllib.unescape(og.group(1)) if og else rec["title"]
    out["collections"] = [htmllib.unescape(c).strip()
                          for c in COLLECTION_RE.findall(page)][:6]
    out["episodes"] = len(set(re.findall(EPISODE_RE_TMPL.format(pid=pid), page)))

    if track and want_vtt_stats:
        out["vtt_stats"] = analyse_vtt(track[1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="check only the first N programmes (smoke test)")
    ap.add_argument("--no-vtt-stats", action="store_true", help="skip downloading .vtt files")
    ap.add_argument("--redo", action="store_true", help="ignore existing results")
    args = ap.parse_args()

    catalogue = load_json("catalogue.json") or {}
    if not catalogue:
        raise SystemExit("run step01_catalogue.py first")
    done = {} if args.redo else (load_json("subtitles.json", {}) or {})

    todo = [r for r in catalogue.values() if not r["radio"] and r["pid"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    log(f"checking {len(todo)} programmes ({len(done)} already done), {WORKERS} workers")

    n = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for res in ex.map(lambda r: check_one(r, not args.no_vtt_stats), todo):
            done[res["pid"]] = res
            n += 1
            if n % 100 == 0:
                save_json("subtitles.json", done)
                hits = sum(1 for v in done.values() if v.get("has_subs"))
                log(f"  {n}/{len(todo)} checked, {hits} with subtitles")

    save_json("subtitles.json", done)
    hits = [v for v in done.values() if v.get("has_subs")]
    log(f"done: {len(done)} checked, {len(hits)} with a Portuguese subtitle track")


if __name__ == "__main__":
    main()
