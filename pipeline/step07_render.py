#!/usr/bin/env python3
"""Step 7 - render index.html (and the CSV) from data/dataset.json.

The page is one self-contained file: templates/page_head.html (title, fonts,
CSS) + templates/page_body.html (markup and the small script that renders rows,
filters and the two checkboxes) with the dataset injected in place of the
__DATA__ placeholder. No build tooling, no runtime dependencies.

    python step07_render.py --out site/index.html --csv site/rtp-play-legendado.csv

Pass --site-url to stamp canonical/og:url/og:image for the deployed location.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from common import ROOT, load_json, log

SECTION_LABELS = {
    "series": "Portuguese TV series", "film": "Portuguese films",
    "fun": "Comedy & entertainment", "lang": "Language & literature",
    "docs": "Documentaries (Portugal & Lusophone world)", "nature": "Nature & science",
    "mag": "Magazines & reportage", "food": "Food", "kids": "Kids & animation",
    "music": "Music & concerts", "stage": "Theatre",
    "intl": "International documentaries", "foreign": "Foreign-language fiction",
}

HEAD_EXTRA = """<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Every programme on RTP Play with a Portuguese subtitle track, with English translations - a reference for learners of European Portuguese.">
<meta property="og:title" content="RTP Play Legendado - what has Portuguese subtitles">
<meta property="og:description" content="{n} RTP Play programmes with Portuguese subtitles, searchable, with English translations and a filter for titles blocked outside Portugal.">
<meta property="og:type" content="website">
<link rel="canonical" href="{site}/">
<meta property="og:url" content="{site}/">
<meta property="og:image" content="{site}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{site}/og.png">
<style>body{{margin:0;font:14px system-ui}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site/index.html")
    ap.add_argument("--csv", default="site/rtp-play-legendado.csv")
    ap.add_argument("--site-url", default="https://professorcdp.github.io/rtp-legendado")
    ap.add_argument("--checked-on", default=date.today().strftime("%d %b %Y"))
    args = ap.parse_args()

    rows = load_json("dataset.json")
    if not rows:
        raise SystemExit("run steps 1-6 first")

    head = (ROOT / "templates" / "page_head.html").read_text(encoding="utf-8")
    body = (ROOT / "templates" / "page_body.html").read_text(encoding="utf-8")

    checked = sum(1 for _ in (load_json("subtitles.json") or {}))
    body = body.replace("6,268", f"{checked:,}").replace("checked 11 Sep 2026",
                                                         f"checked {args.checked_on}")
    data = json.dumps(rows, ensure_ascii=False).replace("�", "")
    body = body.replace("__DATA__", data.replace("</", "<\\/"))

    doc = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
           + HEAD_EXTRA.format(site=args.site_url.rstrip("/"), n=len(rows))
           + head + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    log(f"wrote {out} ({len(doc):,} bytes, {len(rows)} rows)")

    csv_path = Path(args.csv)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Section", "Programme", "English title", "Episodes", "Latest episode",
                    "Plays from build location", "Description (PT)", "Description (EN)", "Link"])
        for r in rows:
            eps = "film" if r["s"] == "film" else (("12+" if r["e"] >= 12 else r["e"]) if r["e"] else "special")
            w.writerow([SECTION_LABELS.get(r["s"], r["s"]), r["n"], r.get("ne", ""), eps, r["d"],
                        "yes" if r["ok"] else "no", r["x"], r.get("xe", ""), r["u"]])
    log(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
