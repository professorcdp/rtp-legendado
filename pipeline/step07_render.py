#!/usr/bin/env python3
"""Step 7 - render index.html (and the CSV) from data/dataset.json.

The page is one self-contained file in the Claude Design look:
templates/page_head.html (fonts and CSS) + templates/page_body.html (markup with
{{...}} slots and the small script that filters rows and toggles English).
Rows, section chips and the stats band are written into the page as static
markup, so it reads fine even with JavaScript off. No build tooling, no runtime
dependencies.

    python step07_render.py --out site/index.html --csv site/rtp-play-legendado.csv

--site-url (or the SITE_URL environment variable, set in site.yml) stamps the
canonical URL and social-card tags for the deployed location. When it is a
custom domain rather than *.github.io, a CNAME file is written next to the page
(docs/decisions/0003-custom-domain.md).

After a full rebuild (when data/subtitles.json is present) the check date and
the number of programs checked are saved to data/build_info.json, so the page
can be re-rendered later from the committed dataset without contacting RTP.
"""
from __future__ import annotations

import argparse
import base64
import csv
import html
import os
import re
from datetime import date, timedelta
from pathlib import Path

from common import ROOT, load_json, log, save_json

# Page sections in display order: (section key, anchor id, heading, blurb).
SECTIONS = [
    ("series", "portuguese-tv-series", "Portuguese TV series",
     "The richest seam for comprehensible input: recurring characters, everyday speech and plenty of episodes."),
    ("film", "portuguese-films", "Portuguese films & TV films",
     "One-offs. Harder going than series — no recurring vocabulary to settle into — but the subtitles match the audio."),
    ("fun", "comedy-entertainment", "Comedy, game shows & entertainment",
     "Fast, colloquial and full of interruption. Good listening practice once the basics are in place."),
    ("lang", "language-literature", "Language & literature",
     "Programs about Portuguese itself, and about the books written in it."),
    ("stage", "theatre", "Theater",
     "Staged productions, recorded for television."),
    ("docs", "documentaries-portugal", "Documentaries: Portugal & the Lusophone world",
     "The largest group by far. Narration is scripted and clearly spoken — the easiest place to start listening."),
    ("nature", "nature-science", "Nature, science & environment",
     "Scripted narration again, with vocabulary that repeats across episodes."),
    ("mag", "magazines-reportage", "Magazines, reportage & interviews",
     "Unscripted speech from a wide range of speakers and accents."),
    ("food", "food", "Food",
     "Cooking and eating, mostly in the kitchen and at the table."),
    ("kids", "kids-animation", "Kids & animation",
     "Slow, simple and repetitive — which is exactly what makes it useful early on."),
    ("music", "music-concerts", "Music, concerts & musicals",
     "Performance, with the spoken sections subtitled."),
    ("intl", "international-documentaries", "International documentaries",
     "Foreign productions dubbed or narrated in Portuguese; the subtitles follow that track."),
    ("foreign", "foreign-language-fiction", "Foreign-language fiction",
     "Here the Portuguese subtitles translate another language rather than transcribe the audio — useful for reading, not for listening."),
]
NON_PORTUGUESE = {"intl", "foreign"}

# Section names used in the CSV (kept as published in September 2026).
CSV_LABELS = {
    "series": "Portuguese TV series", "film": "Portuguese films",
    "fun": "Comedy & entertainment", "lang": "Language & literature",
    "docs": "Documentaries (Portugal)", "nature": "Nature & science",
    "mag": "Magazines & reportage", "food": "Food", "kids": "Kids & animation",
    "music": "Music & concerts", "stage": "Theater",
    "intl": "International documentaries", "foreign": "Foreign-language fiction",
}

HEAD_META = """<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What on RTP Play has Portuguese subtitles?</title>
<meta name="description" content="The programs on RTP Play that carry a Portuguese subtitle track — a reference list for learners of European Portuguese.">
<link rel="canonical" href="{site}/">
<meta property="og:type" content="website">
<meta property="og:url" content="{site}/">
<meta property="og:title" content="What on RTP Play has Portuguese subtitles?">
<meta property="og:description" content="{n} programs on RTP Play with a Portuguese subtitle track, for learners of European Portuguese.">
<meta property="og:image" content="{site}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{site}/og.png">
"""

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def esc(s) -> str:
    return html.escape(str(s or ""), quote=False).replace('"', "&quot;")


def eps_label(r) -> str:
    if r["s"] == "film":
        return "film"
    if not r["e"]:
        return "special"
    return f"{'12+' if r['e'] >= 12 else r['e']} ep{'' if r['e'] == 1 else 's'}"


def row_html(r) -> str:
    search = " ".join(x for x in (r["n"], r.get("ne", ""), r["x"], r.get("xe", "")) if x).lower()
    flag = (f'<span class="flag tag">{esc(r["tag"])}</span>' if r.get("tag") else "") + \
           ('<span class="flag">Portugal-only license</span>' if r.get("pt") else "")
    out = [f'<article class="row" data-blocked="{1 if r.get("pt") else 0}" data-s="{esc(search)}">',
           '<div class="rowhead"><div class="rowtitle">',
           f'<a href="{esc(r["u"])}" target="_blank" rel="noopener">{esc(r["n"])}</a>{flag}</div>',
           f'<div class="rowmeta">{eps_label(r)} · {esc(r["d"])}</div></div>']
    if r.get("ne"):
        out.append(f'<div class="en entitle">{esc(r["ne"])}</div>')
    if r["x"]:
        out.append(f'<p class="desc">{esc(r["x"])}</p>')
    if r.get("xe"):
        out.append(f'<p class="en endesc">{esc(r["xe"])}</p>')
    out.append("</article>")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site/index.html")
    ap.add_argument("--csv", default="site/rtp-play-legendado.csv")
    ap.add_argument("--site-url", default=os.environ.get("SITE_URL") or "https://legendado.professorcdp.com")
    ap.add_argument("--checked-on", help="date shown on the page, e.g. '11 Sep 2026' (default: today)")
    args = ap.parse_args()

    rows = load_json("dataset.json")
    if not rows:
        raise SystemExit("run steps 1-6 first")

    today = date.today()
    subtitles = load_json("subtitles.json") or {}
    if subtitles:                                  # fresh rebuild: record when and how much
        checked_on = args.checked_on or f"{today.day:02d} {MONTHS_EN[today.month - 1]} {today.year}"
        checked_n = len(subtitles)
        save_json("build_info.json", {"checked_on": checked_on, "checked_n": checked_n})
    else:                                          # re-render of the committed dataset
        info = load_json("build_info.json") or {}
        checked_on = args.checked_on or info.get("checked_on") or "11 Sep 2026"
        checked_n = info.get("checked_n") or 6268

    portuguese = [r for r in rows if r["s"] not in NON_PORTUGUESE]
    year_ago = (today - timedelta(days=365)).strftime("%Y%m%d")
    pt_only_n = sum(1 for r in rows if r.get("pt"))
    stats = [(f"{checked_n:,}", "TV programs checked"),
             (f"{len(rows):,}", "with a subtitle track"),
             (f"{pt_only_n:,}", "Portugal-only license"),
             (f"{sum(1 for r in portuguese if r['dk'] >= year_ago):,}", "updated in the last year")]

    chips, sections = [], []
    for key, anchor, title, blurb in SECTIONS:
        sec_rows = [r for r in rows if r["s"] == key]
        if not sec_rows:
            continue
        chips.append(f'<a class="chip" href="#{anchor}">{esc(title)}<b>{len(sec_rows)}</b></a>')
        sections.append(
            f'  <section id="{anchor}" data-total="{len(sec_rows)}"><h2>{esc(title)}</h2>'
            f'<p class="blurb">{esc(blurb)}</p>'
            f'<p class="range"><span class="shown">{len(sec_rows)}</span> of {len(sec_rows)} titles</p>'
            + "".join(row_html(r) for r in sec_rows) + "</section>")
    unplaced = [r["n"] for r in rows if r["s"] not in {s[0] for s in SECTIONS}]
    if unplaced:
        raise SystemExit(f"rows in an unknown section: {unplaced[:5]}")

    head = (ROOT / "templates" / "page_head.html").read_text(encoding="utf-8")
    font = base64.b64encode((ROOT / "templates" / "fonts" / "inter-latin.woff2").read_bytes()).decode()
    head = head.replace("{{INTER_WOFF2}}", font)
    body = (ROOT / "templates" / "page_body.html").read_text(encoding="utf-8")
    fills = {
        "CHECKED_ON": checked_on,
        "YEAR": str(today.year),             # copyright year, from the build date
        "CHECKED_N": f"{checked_n:,}",
        "STATS": "".join(f'<div class="stat"><b>{b}</b><span>{esc(s)}</span></div>' for b, s in stats),
        "PT_ONLY_N": f"{pt_only_n:,}",
        "CHIPS": "".join(chips),
        "SECTIONS": "\n".join(sections),
    }
    for k, v in fills.items():
        body = body.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", body)
    if left:
        raise SystemExit(f"template slots left unfilled: {left}")

    doc = ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
           + HEAD_META.format(site=args.site_url.rstrip("/"), n=len(rows))
           + head + "</head>\n<body>\n\n" + body + "</body>\n</html>\n")
    doc = doc.replace("�", "")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    log(f"wrote {out} ({len(doc):,} bytes, {len(rows)} rows)")

    host = re.sub(r"^https?://", "", args.site_url).split("/")[0]
    if not host.endswith(".github.io"):              # custom domain: keep it with every deploy
        (out.parent / "CNAME").write_text(host + "\n", encoding="utf-8")
        log(f"wrote {out.parent / 'CNAME'} ({host})")

    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    order = {s[0]: i for i, s in enumerate(SECTIONS)}
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Section", "Program", "English title", "Episodes", "Latest episode",
                    "Portugal-only license", "Note", "Description (PT)", "Description (EN)", "Link"])
        for r in sorted(rows, key=lambda r: order[r["s"]]):
            eps = "film" if r["s"] == "film" else (("12+" if r["e"] >= 12 else r["e"]) if r["e"] else "special")
            w.writerow([CSV_LABELS.get(r["s"], r["s"]), r["n"], r.get("ne", ""), eps, r["d"],
                        "yes" if r.get("pt") else "no", r.get("tag", ""), r["x"], r.get("xe", ""), r["u"]])
    log(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
