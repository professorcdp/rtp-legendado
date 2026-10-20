#!/usr/bin/env python3
"""Draw og.png, the 1200x630 social-card image shown when the page is shared.

The card is laid out as HTML in the page's own look (the Claude Design colours
from templates/page_head.html and the embedded Inter font from
templates/fonts/) and photographed with a headless Chrome. It carries no
numbers, so it doesn't go stale when the list changes (issue #33).

Run by hand, from the pipeline folder, when the wording or look changes:

    pip install playwright          # once; uses the installed Google Chrome
    python tools/make_og.py         # writes ../og.png (the repo root)
    python tools/make_og.py --out /tmp/og.png

If Google Chrome isn't installed, run `playwright install chromium` and pass
--browser chromium.
"""
from __future__ import annotations

import argparse
import base64
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent.parent
FONT = PIPELINE / "templates" / "fonts" / "inter-latin.woff2"

HEADLINE = "What on RTP Play has Portuguese captions?"
KICKER = "European Portuguese · comprehensible input"
LINE = "A reference list for learners of European Portuguese, rebuilt weekly"
ADDRESS = "legendado.professorcdp.com"

# Colours from templates/page_head.html (:root)
CARD = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Inter;font-weight:100 900;src:url(data:font/woff2;base64,{font}) format("woff2")}}
*{{box-sizing:border-box;margin:0}}
html,body{{width:1200px;height:630px}}
body{{background:#161826;color:#e9e9ed;font-family:Inter,sans-serif;-webkit-font-smoothing:antialiased;
  display:flex;flex-direction:column;padding:72px 84px 0;position:relative;overflow:hidden}}
.kicker{{font-size:20px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#b5abfc;margin-bottom:34px}}
h1{{font-size:84px;font-weight:500;line-height:1.04;letter-spacing:-.035em;max-width:13em;margin-bottom:34px}}
p{{font-size:31px;line-height:1.4;color:#cfd3e5;max-width:28em}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:96px;background:#262a60;display:flex;align-items:center;
  padding:0 84px;justify-content:space-between}}
.foot b{{font-size:26px;font-weight:500;color:#e7e5fe;letter-spacing:-.01em}}
.foot span{{font-size:18px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#d2cefd}}
</style></head><body>
<div class="kicker">{kicker}</div>
<h1>{headline}</h1>
<p>{line}</p>
<div class="foot"><b>{address}</b><span>RTP Play · Português adaptado</span></div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(PIPELINE.parent / "og.png"))
    ap.add_argument("--browser", default="chrome", help="'chrome' (installed Google Chrome) or 'chromium'")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    page_html = CARD.format(font=base64.b64encode(FONT.read_bytes()).decode(), kicker=KICKER,
                            headline=HEADLINE, line=LINE, address=ADDRESS)
    with sync_playwright() as p:
        browser = (p.chromium.launch(channel="chrome") if args.browser == "chrome" else p.chromium.launch())
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        page.set_content(page_html)
        page.evaluate("document.fonts.ready")
        page.screenshot(path=args.out, clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        browser.close()
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
