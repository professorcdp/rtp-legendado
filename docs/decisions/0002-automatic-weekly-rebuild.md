# 2. Rebuild the list automatically every week

**Date:** 2026-10-09
**Status:** accepted

## Context
The list was built once, by hand, on 11 September 2026, and RTP's catalogue changes constantly. The tool that built it (now in `pipeline/`) can rebuild it, but four things stood in the way of an automatic rebuild:

- The "plays outside Portugal" answer depends on the machine that asks. The September check ran from a connection RTP placed in Spain. A rebuild running somewhere else gives a different answer.
- The live page was restyled in Claude Design and isn't produced by the pipeline.
- Foreign-language titles can't be detected automatically. They're listed by hand in `pipeline/config/overrides.json`.
- The pipeline's working files only ever grow. Step 1 adds to the catalogue and never removes anything, and steps 2 to 4 skip any programme they've already checked. If those files were kept from one week to the next, programmes RTP removed would stay on the list, and existing ones would never be re-checked.

## Decision
- **Where and when:** GitHub Actions, once a week. A smoke test on 2026-10-09 showed RTP answers GitHub's machines normally (issue #4).
- **Portugal-only licence instead of "plays outside Portugal":** the page publishes the location-independent `pt_only` flag (the `/pt/` path segment in the player's fileKey). In a check of 718 links it agreed with September's Spain results 93.6% of the time, and it hadn't changed for any title since September (issue #5). Titles without the flag usually play abroad but not always (about 1 in 12 were still blocked from Spain), and the page says so.
- **New titles are published automatically.** Each run that adds or removes titles opens a GitHub issue listing them, so foreign-language ones can be added to `config/overrides.json` afterwards.
- **Translations:** made through the Anthropic API (model `claude-sonnet-5-5`), with the key stored only as a GitHub Actions secret, `ANTHROPIC_API_KEY`, which Jim adds himself. Until it's there, the run uses `--no-translate` rather than failing, and rows whose text hasn't changed keep their existing English from the translation cache.
- **Jim's design is kept:** the Claude Design look is ported into `pipeline/templates/`, so the pipeline produces the page from then on.
- **Fresh state every week:** the weekly run starts from a fresh checkout and rebuilds every step from scratch. The working files (`catalogue.json`, `subtitles.json`, `rights.json`, `synopses.json`, `dataset_draft.json`) are never committed; `pipeline/.gitignore` excludes them. Only two files carry over:
  - `data/dataset.json`, the published list, so the next run can compare against it;
  - `data/translations.json`, which is keyed by a hash of the source text and so can't go stale.

  The HTTP cache may be restored between runs, but its 24-hour expiry means a weekly run fetches everything again. We chose this over running with `--redo`, which would need adding to every step and is easy to forget when running a step by hand.
- **Politeness:** no more than 4 requests to RTP at a time (`RTP_WORKERS` 4 or below), because RTP slows down silently under load (see `pipeline/GOTCHAS.md`).

## Alternatives considered
- **Run it on Jim's Mac.** That keeps the check's location fixed, but depends on the Mac being on. It's the fallback if RTP ever blocks GitHub.
- **Keep publishing "plays outside Portugal" from the build machine.** The answer would change with wherever GitHub's machine happens to be, which isn't a stable thing to tell students.
- **Hold new titles for review before publishing.** Safer for the foreign-language split, but the list would go stale whenever the review slipped.
- **Keep working state between runs and use `--redo`.** See above.

## Consequences
- The list stays current without manual work, apart from reviewing new titles for foreign-language ones.
- A full rebuild every week takes about 2 hours of mostly waiting on GitHub's machines, which costs nothing for a public repo.
- About 40 titles that were hidden as "won't play where you are" now show, because they're blocked from Spain but aren't stored as Portugal-only.
- Until the API key is added, new or reworded descriptions appear without English.
- RTP can change its page layout without warning, and the scraping then fails silently (it happened before the first automated run; see pipeline/GOTCHAS.md). The weekly run therefore refuses to publish when the list shrinks below 70% of the previous one or when more than 15 titles share one description. The weekly review issue is the other early warning.
