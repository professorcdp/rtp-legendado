# 5. Show Portugal-only titles by default

**Date:** 2026-10-20
**Status:** accepted

## Context
Since September the page has had a "Hide programs with a Portugal-only license" checkbox, ticked
by default, so about 240 of the 664 titles were hidden until a reader unticked it. The idea was
to spare readers outside Portugal titles that wouldn't play for them.

In practice the default hid titles from people who could watch them: Jim himself missed one,
readers in Portugal never see a "won't play" problem, and teachers browsing the full catalog
lost about a third of it without noticing. Each Portugal-only row already carries a
"Portugal-only license" label, so nothing is lost by showing them.

## Decision
- The checkbox is **unticked by default**: every title shows until the reader chooses to hide the
  Portugal-only ones.
- Its label reads "Hide the N programs with a Portugal-only license", which makes sense whether
  the box is ticked or not.
- The per-row "Portugal-only license" label stays.

## Alternatives considered
- **Keep the default ticked.** Right for readers abroad on a first visit, but the cost (titles
  silently missing for everyone else) turned out to be the bigger problem.
- **Tick it automatically for visitors outside Portugal.** Would need a location lookup, which
  the page avoids (no outside requests, no tracking).
- **Remember each reader's choice.** Possible later with the browser's local storage; not needed
  to fix the problem.

## Consequences
- Readers abroad see some titles they can't play, clearly labeled, and can hide them in one tap.
- The stats band ("Portugal-only license" count) and the CSV column are unchanged.
