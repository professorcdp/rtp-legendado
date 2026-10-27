#!/usr/bin/env python3
"""Compare this run's list with the previous run's, for the weekly workflow.

    python report_changes.py PREVIOUS.json --out changes.md

Reads data/dataset.json (this run) and PREVIOUS.json (the dataset committed by
the last run, or the September snapshot the first time). Writes a Markdown
summary of added, removed and renamed titles, with a reminder to check new
titles for foreign-language ones, and prints `changed=true|false` for GitHub
Actions (renames alone don't count as a change).

Rows are matched by RTP program id (pid), not by title: a row matches if it
shares any pid (its main link or a merged season) with a row in the other list.
The title shown is often the latest episode's, so it can change from week to
week while the program stays the same (issue #20).

Exits with an error if this run's list is much shorter than the previous one
(under --min-ratio of it), which usually means RTP had a bad day rather than
that half the catalog vanished. Also exits with an error if more than
--max-same-desc titles share one description, which means a scraping step has
picked up page furniture (in October 2026 RTP's menu text landed on 200 rows),
or if the Portugal-only count is zero or under --min-pt-ratio of the previous
list's, which means the fileKey markup has probably changed. The workflow then
stops before publishing.

Also prints `untranslated=N` (rows missing an English title or description)
and adds that count to the summary.
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
    "lang": "Language & literature", "stage": "Theater", "docs": "Documentaries (Portugal)",
    "nature": "Nature & science", "mag": "Magazines & reportage", "food": "Food",
    "kids": "Kids & animation", "music": "Music & concerts",
    "intl": "International documentaries", "foreign": "Foreign-language fiction",
}
# Sections where a foreign-language title could be hiding (see GOTCHAS.md)
CHECK_SECTIONS = {"series", "film", "docs", "nature"}


def pid(url: str) -> str:
    m = re.search(r"/play/(?:zigzag/)?p(\d+)/", url)
    return m.group(1) if m else "?"


def pids(r) -> set[str]:
    return {pid(u) for u in [r["u"]] + [m["u"] for m in r.get("more", [])]}


def match(rows, others) -> dict[int, dict]:
    """For each row (by index), the row in `others` sharing a pid with it, if any."""
    by_pid = {p: o for o in others for p in pids(o)}
    out = {}
    for i, r in enumerate(rows):
        hit = next((by_pid[p] for p in sorted(pids(r)) if p in by_pid), None)
        if hit is not None:
            out[i] = hit
    return out


def line(r) -> str:
    return f"- **{r['n']}** ({SECTION_NAMES.get(r['s'], r['s'])}, pid `{pid(r['u'])}`): {r['u']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("previous")
    ap.add_argument("--out", default="changes.md")
    ap.add_argument("--min-ratio", type=float, default=0.7)
    ap.add_argument("--max-same-desc", type=int, default=15)
    ap.add_argument("--min-pt-ratio", type=float, default=0.5)
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

    new_pt = sum(1 for r in new if r.get("pt"))
    old_pt = sum(1 for r in old if r.get("pt"))          # 0 for the September snapshot (no `pt` field)
    if new_pt == 0 or (old_pt and new_pt < args.min_pt_ratio * old_pt):
        raise SystemExit(f"{new_pt} titles have a Portugal-only license, against {old_pt} last time; "
                         f"the fileKey check is probably broken, so not publishing")

    untranslated = sum(1 for r in new if not r.get("ne") or (r["x"] and not r.get("xe")))

    new_to_old, old_to_new = match(new, old), match(old, new)
    # a row kept in its grace period is never new; it is listed under "Not seen with captions" instead
    added = sorted((r for i, r in enumerate(new) if i not in new_to_old and not r.get("grace")),
                   key=lambda r: (r["s"], r["n"]))
    # titles step 6b found pulled by RTP (empty video key, no episodes listed; #50)
    pulled_pids = {pid(r["u"]) for r in json.loads((DATA / "pulled.json").read_text(encoding="utf-8"))} \
        if (DATA / "pulled.json").exists() else set()
    gone = [r for i, r in enumerate(old) if i not in old_to_new]
    by_rtp = sorted((r for r in gone if pids(r) & pulled_pids), key=lambda r: (r["s"], r["n"]))
    removed = sorted((r for r in gone if not pids(r) & pulled_pids), key=lambda r: (r["s"], r["n"]))
    renamed = sorted(((o, r) for i, r in enumerate(new) if (o := new_to_old.get(i)) and o["n"] != r["n"]),
                     key=lambda t: (t[1]["s"], t[1]["n"]))
    # Titles kept for 28 days after their captions were last seen (step06b_grace.py, #21). They
    # are still published, so they count in the totals and the guards above, and only count as
    # removed once they actually drop.
    grace = sorted((r for r in new if r.get("grace")), key=lambda r: (r["grace"], r["s"], r["n"]))
    newly_grace = [r for i, r in enumerate(new) if r.get("grace") and not (new_to_old.get(i) or {}).get("grace")]

    md = [f"Weekly rebuild on {date.today().isoformat()}: {len(old)} → {len(new)} titles, "
          f"{len(added)} added, {len(removed)} removed, {len(by_rtp)} removed by RTP, {len(renamed)} renamed, "
          f"{len(grace)} kept without captions this week. "
          f"{untranslated} title(s) still without English.", ""]
    if untranslated:
        md += [f"**{untranslated} title(s) have no English yet.** If the run had an API key, the "
               "translation step failed for them (see the run's log); they are retried next run.", ""]
    to_check = [r for r in added if r["s"] in CHECK_SECTIONS]
    if added:
        md += [f"### Added ({len(added)}): please check for foreign-language titles", "",
               "New titles are already published. RTP labels every Portuguese text track the same way (captions and translated subtitles alike), so "
               "foreign-language fiction and international documentaries can't be told apart automatically. "
               f"Look through the {len(to_check)} new title(s) in Portuguese series, films, documentaries and "
               "nature below. For any that aren't Portuguese-made, add the pid to `foreign_fiction` or "
               "`international_documentary` in `pipeline/config/overrides.json`. The next weekly run "
               "(or a manual run of the workflow) moves them to the right section.", ""] + \
              [line(r) for r in added] + [""]
    if removed:
        md += [f"### Removed ({len(removed)})", ""] + [line(r) for r in removed] + [""]
    if by_rtp:
        md += [f"### Removed by RTP ({len(by_rtp)})", "",
               "RTP has pulled these: the player has no video and the program page lists no episodes. "
               "Dropped at once rather than kept in the grace period. No action needed.", ""] + \
              [line(r) for r in by_rtp] + [""]
    if grace:
        md += [f"### Not seen with captions since … ({len(grace)})", "",
               "Still listed, marked \"captions last confirmed <date>\": their newest episode has no captions. "
               "Each drops off 28 days after that date unless captions come back. No action needed.", ""] + \
              [f"- **{r['n']}** ({SECTION_NAMES.get(r['s'], r['s'])}): not seen with captions since {r['grace']}"
               + (" (new this week)" if r in newly_grace else "") for r in grace] + [""]
    if renamed:
        md += [f"### Renamed ({len(renamed)})", "",
               "Same program, new title (usually the latest episode's). No action needed.", ""] + \
              [f"- renamed: **{o['n']}** → **{r['n']}** ({SECTION_NAMES.get(r['s'], r['s'])}, "
               f"pid `{pid(r['u'])}`): {r['u']}" for o, r in renamed] + [""]
    Path(args.out).write_text("\n".join(md), encoding="utf-8")

    print(md[0], file=sys.stderr)
    print(f"changed={'true' if (added or removed or by_rtp or newly_grace) else 'false'}")
    print(f"untranslated={untranslated}")


if __name__ == "__main__":
    main()
