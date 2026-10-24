# 8. Keep titles for four weeks after their captions were last seen

**Date:** 2026-10-23
**Status:** accepted

## Context
The weekly rebuild checks only each programme's latest episode. When RTP posts a new episode
without captions, the title drops off the list, and it comes back a week later when a captioned
episode appears. In October 2026 this happened to O Leonel das Moscas, Petit, Mouk and Jones,
among others. Readers who bookmarked a show lost it for no good reason, and the weekly review
reported the same titles as removed and then added again.

## Decision
- A title stays on the list for **28 days** after the last rebuild that found a caption track
  on it. After that it drops off as before.
- While it's kept, the row shows a small muted line, **"captions last confirmed 15 Oct"** (the
  date of that rebuild), and links to that last captioned episode, not the newest uncaptioned
  one. The CSV's Note column carries the same text.
- A new step, `pipeline/step06b_grace.py`, runs after translation and before the page is built.
  It keeps `pipeline/data/seen.json`, committed by the weekly workflow, with the date of the
  last captioned sighting of each title and the row as it was published then. Titles are
  matched across weeks by RTP programme id (any shared id, including merged seasons).
- The weekly review lists kept titles separately, under "Not seen with captions since …", and
  counts a title as removed only when it actually drops. Kept titles are never counted as
  added. The publish guards (shrinking list, repeated descriptions, Portugal-only count) see the
  published list, kept titles included.
- The "with a caption track" figure in the stats band counts only titles with captions right
  now; the section counts include kept titles, since they are on the page.
- **Seeding:** `seen.json` was first built by `pipeline/tools/seed_seen.py` from the lists
  committed by real rebuilds over the previous 28 days, each dated by its rebuild, so no title
  was marked "last confirmed today" unless today's run found it.

## Alternatives considered
- **Check several recent episodes of each programme** instead of only the latest. More accurate,
  but multiplies the requests to RTP (see GOTCHAS on rate limits) and the run time.
- **Keep titles indefinitely.** The list would fill with shows that no longer have captions or
  have left RTP Play.
- **A shorter grace period (two weeks).** Some shows go more than a week between captioned
  episodes; four weeks covers the patterns seen so far.

## Consequences
- Bookmarked shows stay put through a single uncaptioned episode.
- A kept title may occasionally point to an episode RTP has since removed; it drops within four
  weeks at most.
- `seen.json` is a new file the workflow must commit each week; if it's lost, the next run
  starts fresh (everything found that day is "seen today", and nothing is kept).
