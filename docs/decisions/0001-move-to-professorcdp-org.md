# 1. Move the repo to the professorcdp organization

**Date:** 2026-10-09
**Status:** accepted

## Context
RTP Play Legendado was first published from Jim's personal GitHub account (jamminalley/rtp-legendado), with its website at https://jamminalley.github.io/rtp-legendado/. It's a business project, and business projects live in the professorcdp GitHub organization. The old website link has already been shared with students, so it has to keep working.

## Decision
Transfer the repo to professorcdp/rtp-legendado and serve the site from https://professorcdp.github.io/rtp-legendado/. Create a small public repo at jamminalley/rtp-legendado whose only job is to forward visitors from the old address to the new one, keeping any path, query and #anchor.

## Alternatives considered
- **Leave it under jamminalley.** No disruption, but it breaks the rule that business work lives in the org.
- **Move without a forwarding site.** Simpler, but every link already given to students would break. GitHub forwards the repo page after a transfer, but not the github.io website.

## Consequences
- Business work is all in one place, under the org.
- There's an extra repo (the forwarding site) to keep. We'll need to decide how long to keep it.
- The repo is public, so CLAUDE.md, PROJECT.md and docs/ are visible to anyone. Keep anything private out of them.
