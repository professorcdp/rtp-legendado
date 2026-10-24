#!/usr/bin/env python3
"""Build data/seen.json from the lists already in git history (one-off, decision 0008).

The grace period (step06b_grace.py) needs to know when each title was last seen
with captions. Rather than starting everyone at "today", replay the
data/dataset.json files committed by actual rebuilds ("Weekly rebuild of the
list (YYYY-MM-DD)" commits, not hand edits) from the last 28 days, oldest first,
taking each day's last one and dating it by the date in that message. Titles that dropped out recently
then get their real last-seen date.

Run from the pipeline folder, inside the git checkout:

    python tools/seed_seen.py                # writes data/seen.json
    python tools/seed_seen.py --dry-run      # just report
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import save_json  # noqa: E402
from step06b_grace import GRACE_DAYS, update  # noqa: E402

PATH = "pipeline/data/dataset.json"


ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                      check=True, cwd=Path(__file__).resolve().parent).stdout.strip()


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=ROOT).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    since = (date.fromisoformat(args.today) - timedelta(days=GRACE_DAYS)).isoformat()
    per_day = {}
    for line in git("log", "--format=%H %s", f"--since={since}", "--grep=^Weekly rebuild of the list (", "--", PATH).splitlines():
        sha, subject = line.split(" ", 1)
        day = subject.rsplit("(", 1)[1].rstrip(")")
        per_day.setdefault(day, sha)                 # git log is newest first: keep the day's last rebuild

    seen: dict = {}
    for day in sorted(per_day):
        rows = [r for r in json.loads(git("show", f"{per_day[day]}:{PATH}")) if not r.get("grace")]
        grace = update(seen, rows, day)
        print(f"{day} {per_day[day][:7]}: {len(rows)} with captions, {len(grace)} in grace")
    if not args.dry_run:
        save_json("seen.json", {"_comment": "Last run that found each title with captions; see step06b_grace.py.",
                                "rows": seen})
        print(f"wrote data/seen.json ({len(seen)} titles)")


if __name__ == "__main__":
    main()
