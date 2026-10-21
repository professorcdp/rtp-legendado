# RTP Play Legendado

**Stamp:** business
(Says which Claude Max account meters this work and which GitHub account owns the repo. The Claude side is enforced by the `.claude-account` marker file in this folder, written by `claude-stamp`; keep the two in agreement.)
**Started:** 2026-10-09
**GitHub:** the repo is owned by the professorcdp organization (business). Work is done while signed in as jamminalley, Jim's own GitHub login, which is an admin of that organization. That is intended (confirmed by Jim, 2026-10-09; see docs/decisions/0001-move-to-professorcdp-org.md).

## Overview
A reference list of the programs on [RTP Play](https://www.rtp.pt/play/) that carry Portuguese captions (same-language subtitles). It's for learners of European Portuguese who want to watch while reading along. The first version was published on 12 September 2026 and has already been shared with students.

## Expected output
A single self-contained web page (no external requests, no tracking) served from GitHub Pages at https://legendado.professorcdp.com/, plus the same data as a spreadsheet (`rtp-play-legendado.csv`). Both are rebuilt every week from `pipeline/` by `.github/workflows/site.yml`.

## Requirements
### Must have
- List of RTP Play programs with Portuguese captions, grouped by genre, with foreign-language material at the bottom
- English translations of every title and description, which can be hidden
- A filter that hides titles RTP won't play outside Portugal
- A link to each program on RTP Play
- Already-shared links keep working
### Nice to have
- Weekly automatic rebuild of the list (done, see docs/decisions/0002-automatic-weekly-rebuild.md)

## Assumptions
- Checking only the latest episode of each program is a good enough guide to whether a show has captions.
- RTP keeps labeling the caption track *Português adaptado* and keeps its rights-check service available, so the list can be rebuilt the same way.
- Linking to RTP's pages (not hosting their content) is acceptable use.

## Out of scope
- Hosting or downloading RTP's videos or caption files; the page only links to RTP.
- Tracking or analytics on the page.

## Open questions
- How long should the old jamminalley.github.io forwarding site be kept?

## Current status
Live at https://legendado.professorcdp.com/ since 18 Oct 2026 (the old professorcdp.github.io and jamminalley.github.io addresses forward there). The list rebuilds itself every Monday on GitHub Actions, translates anything new and publishes: about 660 titles in the azulejo look (light and dark, shared with NúmerosPT), American spelling, Portugal-only license labels, learner notes, English for every title and description, an embedded font (no outside requests) and a phone-friendly pinned bar. Each run that adds or removes titles opens a review issue.
