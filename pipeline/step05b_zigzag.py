#!/usr/bin/env python3
"""Step 5b - link the kids section to RTP Play Zig Zag.

RTP Play Zig Zag (https://www.rtp.pt/play/zigzag/) is RTP's children's front
door to the same catalogue: a programme has the same id there, at
/play/zigzag/p<pid>/e<eid>/<slug> as well as /play/p<pid>/e<eid>/<slug>. The
Zig Zag page is the child-friendly one, so rows in the kids section link there
(main link and "Also:" seasons; the CSV uses the same links).

Each Zig Zag address is fetched first (politely, cached for a day) and only
used if that page carries the Portuguese caption track itself; otherwise the row
keeps its /play/ link. (Zig Zag answers 200 even for a programme that doesn't
exist, so a status check alone proves nothing.) Issue #34.

Reads and rewrites data/dataset.json.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

from common import WORKERS, fetch, load_json, log, save_json, subtitle_track

PLAY = "https://www.rtp.pt/play/"
ZIGZAG = "https://www.rtp.pt/play/zigzag/"


def zigzag_url(url: str) -> str | None:
    """The Zig Zag address for a /play/p<pid>/... link, if it works."""
    m = re.match(re.escape(PLAY) + r"(p(\d+)/.*)$", url)
    if not m or url.startswith(ZIGZAG):
        return None
    zz = ZIGZAG + m.group(1)
    try:
        page = fetch(zz)
    except Exception:                             # noqa: BLE001 - 404 or unreachable: keep /play/
        return None
    return zz if subtitle_track(page) else None


def main():
    rows = load_json("dataset.json")
    if not rows:
        raise SystemExit("run step05_dataset.py first")
    kids = [r for r in rows if r["s"] == "kids"]
    links = sorted({r["u"] for r in kids} | {m["u"] for r in kids for m in r.get("more", [])})
    log(f"checking {len(links)} Zig Zag addresses for {len(kids)} kids rows")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        found = dict(zip(links, ex.map(zigzag_url, links)))

    for r in kids:
        r["u"] = found.get(r["u"]) or r["u"]
        for m in r.get("more", []):
            m["u"] = found.get(m["u"]) or m["u"]
    save_json("dataset.json", rows)
    ok = sum(1 for v in found.values() if v)
    log(f"done: {ok} of {len(links)} kids links now point to Zig Zag; "
        f"{len(links) - ok} keep the /play/ address")


if __name__ == "__main__":
    main()
