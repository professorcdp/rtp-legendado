# 9. Review issues list everything since the last review, not since the last run

**Date:** 2026-10-27
**Status:** accepted

## Context
Each rebuild compared its list with the previous run's and opened a review issue for titles
that were new since then. When several rebuilds happened between reviews (manual runs, the
scheduled run, reruns after a fix), a title appeared in only one of the issues. On 26 October,
#51 was closed as superseded by a later issue and its three new titles (Jogos de Traições,
Motel Destino, Floresta Selvagem) were never reviewed; one was a US film sitting in
"Portuguese films".

## Decision
- `pipeline/data/reviewed.json` is the baseline: the programme ids already reviewed for
  language. It started on 2026-10-27 with every title then listed (all had been reviewed,
  including the three above).
- Each review issue's "Added" list is **every published title whose id is not in the baseline**,
  however many rebuilds ago it appeared. Removed and renamed titles are still compared with
  the previous run.
- The baseline changes **only in the review commit**, the one that closes a review issue, by
  running `python tools/mark_reviewed.py --issue N` (from `pipeline/`). That adds the ids in
  that issue's Added list (and merged older seasons of the same rows). Rebuilds never touch it.
- Because unreviewed titles stay in every new review issue, an older review issue can be
  closed in favour of a newer one without losing anything; the closing comment names the
  newer issue. A review issue is never closed as superseded unless its titles appear in the
  newer one.

## Alternatives considered
- **Comment on the open review issue instead of opening a new one.** Fewer issues, but the
  workflow would need to find and edit the right issue, and a closed-by-mistake issue would
  still lose titles.
- **Mark titles reviewed automatically when an issue is closed.** Closing an issue doesn't say
  whether its titles were actually looked at; an explicit step in the review commit does.

## Consequences
- No title can slip through between reviews.
- While a title is unreviewed, every rebuild opens a review issue listing it; older ones are
  closed in favour of the newest.
- `reviewed.json` is a hand-maintained file (via the tool) that the rebuild reads but never writes.
