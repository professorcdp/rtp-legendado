# RTP Play Legendado

**Stamp:** business
(Says which Claude Max account meters this work and which GitHub account owns the repo. The Claude side is enforced by the `.claude-account` marker file in this folder, written by `claude-stamp`; keep the two in agreement.)
**Started:** 2026-10-09

## Overview
A reference list of the programmes on [RTP Play](https://www.rtp.pt/play/) that carry a Portuguese subtitle track. It's for learners of European Portuguese who want comprehensible input: shows they can watch while reading along in Portuguese. The first version was published on 12 September 2026 and has already been shared with students.

## Expected output
A single self-contained web page (`index.html`, no build step, no dependencies, no tracking) served from GitHub Pages at https://professorcdp.github.io/rtp-legendado/, plus the same data as a spreadsheet (`rtp-play-legendado.csv`).

## Requirements
### Must have
- List of RTP Play programmes with a Portuguese subtitle track, grouped by genre, with foreign-language material at the bottom
- English translations of every title and description, which can be hidden
- A filter that hides titles RTP won't play outside Portugal
- A link to each programme on RTP Play
- Already-shared links keep working
### Nice to have
- Periodic refresh of the list as RTP's catalogue changes (inferred)

## Assumptions
- Checking only the latest episode of each programme is a good enough guide to whether a show has subtitles.
- RTP keeps labelling the subtitle track *Português adaptado* and keeps its rights-check service available, so the list can be rebuilt the same way.
- Linking to RTP's pages (not hosting their content) is acceptable use.

## Out of scope
- Hosting or downloading RTP's videos or subtitle files; the page only links to RTP.
- Tracking or analytics on the page.

## Open questions
- How often should the list be refreshed, and how will the refresh be done? (The build process isn't in the repo yet.)
- How long should the old jamminalley.github.io forwarding site be kept?

## Current status
Live list of 649 subtitled programmes (snapshot from 11 Sept 2026). Moving the repo from jamminalley to the professorcdp org, with a forwarding site at the old address.
