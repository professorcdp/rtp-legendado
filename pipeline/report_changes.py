#!/usr/bin/env python3
"""Compare this run's list with the previous run's, for the weekly workflow.

    python report_changes.py PREVIOUS.json --out changes.md

Reads data/dataset.json (this run) and PREVIOUS.json (the dataset committed by
the last run, or the September snapshot the first time). Writes a Markdown
summary of added and removed titles, with a reminder to check new titles for
foreign-language ones, and prints `changed=true|false` for GitHub Actions.

Exits with an error if this run's list is much shorter than the previous one
(under --min-ratio of it), which usually means RTP had a bad day rather than
that half the catalogue vanished. Also exits with an error if more than
--max-same-desc titles share one description, which means a scraping step has
picked up page furniture (in October 2026 RTP's menu text landed on 200 rows).
The workflow then stops before publishing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from common import DATA

SECTION_NAMES = {
    "series": "Portuguese TV series", "film": "Portuguese films", "fun": "Comedy & entertainment",
    "lang": "Language & literature", "stage": "Theatre", "docs": "Documentaries (Portugal)",
    "nature": "Nature & science", "mag": "Magazines & reportage", "food": "Food",
    "kids": "Kids & animation", "music": "Music & concerts",
    "intl": "International documentaries", "foreign": "Foreign-language fiction",
}
# Sections where a foreign-language title could be hiding (see GOTCHAS.md)
CHECK_SECTIONS = {"series", "film", "docs", "nature"}


def pid(url: str) -> str:
    m = re.search(r"/play/p(\d+)/", url)
    return m.group(1) if m else "?"


def line(r) -> str:
    return f"- **{r['n']}** ({SECTION_NAMES.get(r['s'], r['s'])}, pid `{pid(r['u'])}`): {r['u']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("previous")
    ap.add_argument("--out", default="changes.md")
    ap.add_argument("--min-ratio", type=float, default=0.7)
    ap.add_argument("--max-same-desc", type=int, default=15)
    args = ap.parse_args()

    new = json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))
    old = json.loads(Path(args.previous).read_text(encoding="utf-8"))
    if len(new) < args.min_ratio * len(old):
        raise SystemExit(f"this run found {len(new)} titles, against {len(old)} last time; "
                         f"too big a drop to publish (limit {args.min_ratio:.0%})")

    desc, n = (Counter(r["x"] for r in new if r["x"]).most_common(1) or [("", 0)])[0]
    if n > args.max_same_desc:
        raise SystemExit(f"{n} titles share the same description ({desc[:80]!r}…); "
                         f"a scraping step is probably broken, so not publishing")

    old_names, new_names = {r["n"] for r in old}, {r["n"] for r in new}
    added = sorted((r for r in new if r["n"] not in old_names), key=lambda r: (r["s"], r["n"]))
    removed = sorted((r for r in old if r["n"] not in new_names), key=lambda r: (r["s"], r["n"]))

    md = [f"Weekly rebuild on {date.today().isoformat()}: {len(old)} → {len(new)} titles, "
          f"{len(added)} added, {len(removed)} removed.", ""]
    to_check = [r for r in added if r["s"] in CHECK_SECTIONS]
    if added:
        md += ["### Please check for foreign-language titles", "",
               "New titles are already published. RTP labels every subtitle track the same way, so "
               "foreign-language fiction and international documentaries can't be told apart automatically. "
               f"Look through the {len(to_check)} new title(s) in Portuguese series, films, documentaries and "
               "nature below. For any that aren't Portuguese-made, add the pid to `foreign_fiction` or "
               "`international_documentary` in `pipeline/config/overrides.json`. The next weekly run "
               "(or a manual run of the workflow) moves them to the right section.", "",
               f"### Added ({len(added)})", ""] + [line(r) for r in added] + [""]
    if removed:
        md += [f"### Removed ({len(removed)})", ""] + [line(r) for r in removed] + [""]
    Path(args.out).write_text("\n".join(md), encoding="utf-8")

    print(md[0], file=sys.stderr)
    print(f"changed={'true' if (added or removed) else 'false'}")


if __name__ == "__main__":
    main()
