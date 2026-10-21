#!/usr/bin/env python3
"""Draw og.png, the 1200x630 social-card image shown when the page is shared.

The card is laid out as HTML in the page's own look (the dark "azulejo" scheme
from templates/page_head.html: cobalt, cream and gold; Instrument Serif and Space
Grotesk from templates/fonts/) and photographed with a headless Chrome. It carries no
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
FONTS = PIPELINE / "templates" / "fonts"

HEADLINE = "What on RTP Play has Portuguese captions?"
KICKER = "European Portuguese · comprehensible input"
LINE = "A reference list for learners of European Portuguese, rebuilt weekly"
ADDRESS = "legendado.professorcdp.com"

# Dark azulejo colours from templates/page_head.html: paper #0C1D6B, sunk #081546,
# ink #F4F0E6, gold #F2C829.
CARD = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:"Space Grotesk";font-weight:300 700;src:url(data:font/woff2;base64,{grotesk}) format("woff2")}}
@font-face{{font-family:"Instrument Serif";font-weight:400;src:url(data:font/woff2;base64,{serif}) format("woff2")}}
*{{box-sizing:border-box;margin:0}}
html,body{{width:1200px;height:630px}}
body{{background:#0C1D6B;color:#F4F0E6;font-family:"Space Grotesk",sans-serif;-webkit-font-smoothing:antialiased;
  display:flex;flex-direction:column;padding:68px 84px 0;position:relative;overflow:hidden}}
body::before{{content:"";position:absolute;inset:22px;border:2px solid #F2C829;border-radius:6px;pointer-events:none}}
.kicker{{font-size:20px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#F2C829;margin-bottom:26px}}
h1{{font-family:"Instrument Serif",serif;font-size:104px;font-weight:400;line-height:.98;letter-spacing:-.01em;max-width:11em;margin-bottom:28px}}
p{{font-size:30px;line-height:1.4;color:rgba(244,240,230,.78);max-width:28em}}
.foot{{position:absolute;left:24px;right:24px;bottom:24px;height:88px;background:#081546;display:flex;align-items:center;
  padding:0 60px;justify-content:space-between;border-radius:0 0 4px 4px}}
.foot b{{font-size:26px;font-weight:500;color:#F4F0E6;letter-spacing:-.01em}}
.foot span{{font-size:17px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#F2C829}}
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

    b64 = lambda name: base64.b64encode((FONTS / name).read_bytes()).decode()
    page_html = CARD.format(grotesk=b64("space-grotesk-latin.woff2"), serif=b64("instrument-serif-latin.woff2"), kicker=KICKER,
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
