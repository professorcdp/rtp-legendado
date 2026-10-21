# 7. Restyle in the "azulejo" palette, shared with NúmerosPT

**Date:** 2026-10-20
**Status:** accepted

## Context
The page used the dark purple-grey Claude Design look from September, with Inter. It worked,
but it looked generic, and it had no light scheme. Jim's other project, NúmerosPT, already has a
deliberately Portuguese visual identity: the colours of azulejo tiles (cobalt glaze on cream,
with a gold accent), defined in its DesignTokens.swift, with Space Grotesk and Instrument Serif.

## Decision
- Use the NúmerosPT tokens exactly. **Light** = cream tile with cobalt lettering; **dark** =
  cobalt glaze with cream lettering; **gold** is the constant accent.
  - paper #F1ECE0 / #0C1D6B; raised #FAF6EC / #16277F; sunk #E8E1D2 / #081546;
    ink #0A1755 / #F4F0E6, with soft, faint and hairline inks at 72/50/18 % (light) and
    70/45/20 % (dark); accent #0C1D6B (cobalt) / #F2C829 (gold); text on accent #F4F0E6 / #0A1755.
  - The accent is deliberately asymmetric, and the faded-ink percentages differ per scheme on
    purpose; they are not to be "tidied" into symmetry.
  - In light, gold is only an outline (on cream it would be 1.36:1), except on the cobalt
    stats band, where gold labels on cobalt are 9.3:1.
- **Scheme:** follow the device (prefers-color-scheme); a sun/moon button in the control bar
  switches it, the choice is remembered in the browser, and a tiny script in `<head>` applies it
  before the page first paints, so there's no flash of the wrong scheme.
- **Fonts:** Space Grotesk for all UI and body text, Instrument Serif for the page title and the
  section headings only. Both OFL, Latin subsets, embedded in the page (no outside requests);
  Inter removed.
- **Mapping:** rows are raised tiles with hairline borders; inactive chips are outlined in
  hairline with ink text, the active chip is filled with the accent; tags are outlined, never
  filled (cobalt outline in light, gold in dark); the search box is recessed (sunk); the phone
  Sections drop-down is a raised panel with a hairline edge.
- The social card (`og.png`, drawn by `pipeline/tools/make_og.py`) uses the dark scheme:
  cobalt, cream and gold, in the same fonts.

## Alternatives considered
- **Keep the Claude Design look.** No light scheme, and nothing about it says Portugal.
- **Light scheme only.** The dark cobalt glaze is half of the azulejo look, and many readers
  browse with dark mode on.

## Consequences
- The page reads as recognizably Portuguese and as part of the same family as NúmerosPT.
- Every text/background pair measures 6.0:1 or better in both schemes (checked in a browser
  on 2026-10-20; the lowest is the search placeholder in light). Ink on paper is 14.1:1 / 13.1:1,
  and cobalt text on the gold accent is 10.3:1.
- The page got slightly smaller (792 KB → 782 KB), because the two new fonts are smaller
  together than Inter was.
- Changes to the palette should be made in NúmerosPT's tokens first, then copied here, so the
  two projects stay in step.
