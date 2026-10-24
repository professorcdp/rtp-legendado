#!/usr/bin/env python3
"""Step 6b - keep titles for 28 days after their captions were last seen.

Only each programme's latest episode is checked, so a show drops off the list
whenever RTP posts a new episode without captions, and comes back a week later
(O Leonel das Moscas, Petit, Mouk, Jones in October 2026). To stop readers
losing shows for no good reason, a title stays on the list for GRACE_DAYS after
the last run that found a caption track on it, marked "captions last confirmed
<date>" and linking to that last captioned episode. After that it drops as
before. Decision 0008, issue #21.

data/seen.json (committed by the weekly workflow) remembers, per row, the date
of the last run that found it with captions and the row itself as published
then (link, translations and all). Rows are matched across runs by RTP
programme id: a stored row and a current row are the same programme if they
share any pid (main link or merged seasons), as in report_changes.py.

Runs after step 6 (so stored rows carry their English) and before step 7.
Reads and rewrites data/dataset.json; writes data/seen.json.

    python step06b_grace.py                    # today's run
    python step06b_grace.py --date 2026-10-22  # pretend the run happened that day
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import date, timedelta
from pathlib import Path

from common import load_json, log, save_json
from step06_translate import americanize

GRACE_DAYS = 28
CONFIG = Path(__file__).resolve().parent / "config" / "overrides.json"


def pid(url: str) -> str | None:
    m = re.search(r"/play/(?:zigzag/)?p(\d+)/", url or "")
    return m.group(1) if m else None


def pids(row) -> set[str]:
    return {p for p in (pid(u) for u in [row["u"]] + [m["u"] for m in row.get("more", [])]) if p}


def update(seen: dict, rows: list, day: str) -> list:
    """Record today's captioned rows in `seen`; return the rows still in their grace period.

    `seen` maps a row key (its main pid) to {"last_seen": "YYYY-MM-DD", "row": {...}}.
    Entries older than GRACE_DAYS are dropped from `seen`.
    """
    today = date.fromisoformat(day)
    current = set().union(*(pids(r) for r in rows)) if rows else set()
    for key in [k for k, e in seen.items() if pids(e["row"]) & current]:
        del seen[key]
    for r in rows:
        clean = {k: v for k, v in r.items() if k != "grace"}
        seen[pid(r["u"]) or r["n"]] = {"last_seen": day, "row": copy.deepcopy(clean)}

    grace = []
    for key in list(seen):
        e = seen[key]
        if e["last_seen"] == day:
            continue
        if today - date.fromisoformat(e["last_seen"]) > timedelta(days=GRACE_DAYS):
            del seen[key]
            continue
        grace.append({**copy.deepcopy(e["row"]), "grace": e["last_seen"]})
    return grace


def freshen(row: dict, ov: dict) -> dict:
    """Bring a stored row up to today's conventions (fields added since it was stored)."""
    for k, v in (("tag", ""), ("note", ""), ("pt", 0), ("more", []), ("ne", ""), ("xe", ""), ("xs", 0)):
        row.setdefault(k, v)
    row["ne"], row["xe"] = americanize(row["ne"]), americanize(row["xe"])
    if not row["tag"]:
        row["tag"] = next((ov.get("page_notes", {}).get(p, "") for p in sorted(pids(row))
                           if ov.get("page_notes", {}).get(p)), "")
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat(), help="run date, YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    rows = [r for r in (load_json("dataset.json") or []) if not r.get("grace")]
    if not rows:
        raise SystemExit("run steps 1-6 first")
    seen = (load_json("seen.json") or {}).get("rows", {})
    ov = json.loads(CONFIG.read_text(encoding="utf-8"))

    grace = [freshen(r, ov) for r in update(seen, rows, args.date)]
    out = rows + grace
    out.sort(key=lambda o: (o["s"], -int(o["dk"] or 0)))
    save_json("dataset.json", out)
    save_json("seen.json", {"_comment": "Last run that found each title with captions; see step06b_grace.py.",
                            "rows": seen})
    log(f"grace: {len(rows)} titles with captions now, {len(grace)} kept from the last {GRACE_DAYS} days "
        f"({', '.join(sorted(r['n'] for r in grace)[:8])}{'…' if len(grace) > 8 else ''})")


if __name__ == "__main__":
    main()
