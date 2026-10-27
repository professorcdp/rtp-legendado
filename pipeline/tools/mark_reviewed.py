#!/usr/bin/env python3
"""Update data/reviewed.json, the baseline of titles already reviewed (decision 0009).

Each weekly review issue lists every published title whose programme id is not
in this baseline, so titles are never lost when several rebuilds happen between
reviews or an older review issue is closed in favour of a newer one. The
baseline changes only here, in the commit that closes a review issue.

Run from the pipeline folder:

    python tools/mark_reviewed.py --issue 54       # add the titles listed in review issue #54
    python tools/mark_reviewed.py --all-current    # baseline = every title listed now (setup)

--issue reads the issue with the `gh` command line tool and takes the pids from
its "Added" list (lines like `- **Title** (Section, pid `12345`): URL`). Merged
older seasons of the same row are added too.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import load_json, save_json  # noqa: E402

PID_RE = re.compile(r"/play/(?:zigzag/)?p(\d+)/")


def row_pids(r) -> set[str]:
    return {m.group(1) for u in [r["u"]] + [x["u"] for x in r.get("more", [])] if (m := PID_RE.search(u))}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--issue", type=int, help="review issue number whose Added titles are now reviewed")
    g.add_argument("--all-current", action="store_true", help="mark every title in data/dataset.json as reviewed")
    args = ap.parse_args()

    base = load_json("reviewed.json") or {"pids": [], "log": []}
    pids = set(base["pids"])
    rows = load_json("dataset.json") or []
    if args.all_current:
        new = set().union(*(row_pids(r) for r in rows))
        note = "all titles listed on " + date.today().isoformat()
    else:
        body = subprocess.run(["gh", "issue", "view", str(args.issue), "--json", "body", "--jq", ".body"],
                              capture_output=True, text=True, check=True).stdout
        added = body.split("### Added", 1)[1].split("\n### ", 1)[0] if "### Added" in body else ""
        listed = set(re.findall(r"pid `(\d+)`", added))
        new = set(listed)
        for r in rows:                              # include merged seasons of the same row
            if row_pids(r) & listed:
                new |= row_pids(r)
        note = f"review issue #{args.issue}: {len(listed)} title(s)"
    added_now = new - pids
    base["pids"] = sorted(pids | new, key=int)
    base["log"].append({"date": date.today().isoformat(), "what": note, "added": len(added_now)})
    base["_comment"] = ("Programme ids already reviewed for language (decision 0009). Updated only by "
                        "tools/mark_reviewed.py in the commit that closes a review issue.")
    save_json("reviewed.json", {"_comment": base["_comment"], "pids": base["pids"], "log": base["log"]})
    print(f"reviewed.json: {len(added_now)} id(s) added ({note}); {len(base['pids'])} in the baseline")


if __name__ == "__main__":
    main()
