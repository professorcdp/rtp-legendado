#!/usr/bin/env python3
"""Seed `first_seen` in data/seen.json from the lists already published (one-off, issue #68).

Replays the September snapshot (the first published list, 11 Sep 2026) and then
every data/dataset.json committed by an actual rebuild ("Weekly rebuild of the
list (YYYY-MM-DD)" commits, not hand edits), oldest first, dated by the date in
the commit message. Each programme id gets the date of the first list that
included it, so a title that dropped off and came back keeps its original date.
Then stamps `fs` on the rows of the current data/dataset.json.

Run from the pipeline folder, inside the git checkout:

    python tools/seed_first_seen.py                    # writes data/seen.json and data/dataset.json
    python tools/seed_first_seen.py --until 2026-11-16 # only history up to that day (for testing)
    python tools/seed_first_seen.py --dry-run          # just report
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import load_json, save_json  # noqa: E402
from step06b_grace import SEEN_COMMENT, pids, stamp_first_seen  # noqa: E402

PATH = "pipeline/data/dataset.json"
SNAPSHOT = ("2026-09-11", Path(__file__).resolve().parent.parent / "snapshot" / "dataset-2026-09-11.json")
ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                      check=True, cwd=Path(__file__).resolve().parent).stdout.strip()


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=ROOT).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", default="9999-12-31", help="ignore rebuilds after this day (YYYY-MM-DD)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lists = [(SNAPSHOT[0], "snapshot", json.loads(SNAPSHOT[1].read_text(encoding="utf-8")))]
    for line in reversed(git("log", "--format=%H %s", "--grep=^Weekly rebuild of the list (", "--", PATH).splitlines()):
        sha, subject = line.split(" ", 1)
        day = subject.rsplit("(", 1)[1].rstrip(")")
        if day <= args.until:
            lists.append((day, sha[:7], json.loads(git("show", f"{sha}:{PATH}"))))

    first_seen: dict = {}
    for day, label, rows in lists:
        before = len(first_seen)
        for r in rows:
            for p in pids(r):
                first_seen.setdefault(p, day)
        print(f"{day} {label}: {len(rows)} rows, {len(first_seen) - before} new ids")
    if args.dry_run:
        return
    stored = load_json("seen.json") or {}
    rows = load_json("dataset.json") or []
    stamp_first_seen(rows, first_seen, lists[-1][0])
    save_json("dataset.json", rows)
    save_json("seen.json", {"_comment": SEEN_COMMENT, "rows": stored.get("rows", {}),
                            "first_seen": dict(sorted(first_seen.items(), key=lambda kv: int(kv[0])))})
    print(f"wrote data/seen.json ({len(first_seen)} ids) and stamped {len(rows)} rows in data/dataset.json")


if __name__ == "__main__":
    main()
