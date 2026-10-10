# rtp-legendado — pipeline

Rebuilds the list of RTP Play programmes that carry a Portuguese subtitle track,
and renders it as a single self-contained HTML page.

Published page: https://professorcdp.github.io/rtp-legendado/

- **[METHOD.md](METHOD.md)** — what the pipeline does, in plain terms: the exact
  addresses fetched, how subtitles are detected, how "plays outside Portugal" is
  checked, how sections are assigned, how the translations are made.
- **[GOTCHAS.md](GOTCHAS.md)** — rate limits, decoys, hand-maintained bits, and
  the things that will bite a scheduled rebuild.
- **[ORIGINAL_SNIPPETS.md](ORIGINAL_SNIPPETS.md)** — the original ad-hoc browser
  and Python code from the September 2026 build, for the record.

## Quick start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # only needed for the translation step

python step02_subtitles.py --limit 20      # smoke test: does RTP answer us at all?
python run_all.py                          # full rebuild (~30 min on GitHub Actions, mostly waiting)
python run_all.py --no-translate           # same, but skip the API step
```

Output lands in `site/`: `index.html` and `rtp-play-legendado.csv`.

## Steps

| | script | what it does | output |
|---|---|---|---|
| 1 | `step01_catalogue.py` | enumerate every programme via RTP's listing endpoint | `data/catalogue.json` |
| 2 | `step02_subtitles.py` | check each TV programme's latest episode for a `vtt:` track; record metadata and subtitle-file stats | `data/subtitles.json` |
| 3 | `step03_rights.py` | ask RTP's rights service whether each subtitled title plays from here | `data/rights.json` |
| 5a | `step05_dataset.py --draft-only` | assign sections (tells step 4 what to fetch) | `data/dataset_draft.json` |
| 4 | `step04_synopses.py` | show-level descriptions for series and recurring strands | `data/synopses.json` |
| 5b | `step05_dataset.py` | merge seasons, fold in rights and synopses | `data/dataset.json` |
| 6 | `step06_translate.py` | English titles and descriptions (cached by content hash) | `data/translations.json` |
| 7 | `step07_render.py` | render the page and the CSV | `site/` |

`run_all.py` runs them in that order; `--from <step>` resumes partway.

Every step is resumable, caches HTTP responses under `data/cache/`, and can be
re-run safely. Re-running after RTP adds a few programmes costs minutes.

## Settings

Environment variables, all optional:

| variable | default | meaning |
|---|---|---|
| `RTP_WORKERS` | 5 | concurrent requests — **do not raise**, see GOTCHAS (the weekly workflow uses 4) |
| `RTP_DELAY` | 0.15 | seconds between requests, globally |
| `RTP_CACHE_TTL` | 86400 | seconds before a cached response is refetched; 0 disables the cache |
| `RTP_TIMEOUT` | 45 | per-request timeout |
| `RTP_TRANSLATE_MODEL` | claude-sonnet-5-5 | model for step 6 |
| `ANTHROPIC_API_KEY` | — | required by step 6 unless `--no-api` |

## The two things a rebuild can't do by itself

1. **`config/overrides.json`.** RTP labels every subtitle track *Português
   adaptado*, whether it's captions on Portuguese audio or a translation of an
   English-language film, so foreign-language fiction and acquired international
   documentaries are listed by hand. After a rebuild, skim the new rows in
   `series`, `film`, `docs` and `nature` and add any that aren't
   Portuguese-made. Diff `data/dataset.json` against the previous run to see
   what's new.
2. **The rights check reflects the machine it runs on.** The published figures
   were taken from a connection RTP geolocated to Spain. A GitHub Actions runner
   will give a different blocked set. Either run the rebuild somewhere
   representative of your readers, or publish the location-independent `pt_only`
   flag, or state on the page where the check was made.

## Scheduled rebuilds

`.github/workflows/site.yml` (at the top of the repo) runs the pipeline every
Monday, commits `data/dataset.json`, `data/translations.json` and
`data/build_info.json`, opens an issue listing added and removed titles, and
publishes `site/` to GitHub Pages. Translations need `ANTHROPIC_API_KEY` in the
repo's Actions secrets; without it the run uses `--no-translate`. The page
publishes the location-independent Portugal-only flag, not the runner's rights
answer. See `docs/decisions/0002-automatic-weekly-rebuild.md`.

## Relationship to the published page

`templates/page_head.html` + `templates/page_body.html` are the page as this
pipeline renders it: data embedded as JSON, rows and filters built by ~60 lines
of vanilla JS.

The page currently live at jamminalley.github.io/rtp-legendado was restyled
separately in Claude Design, which emitted static markup instead of rendering
from the data block — so it does **not** regenerate from this pipeline. To get
automatic rebuilds, port that styling into `templates/page_head.html` (and any
markup changes into `page_body.html`) and let step 7 own the page from then on.

A snapshot of the September 2026 data is in `snapshot/` for comparison.

## Provenance and manners

Public pages only; no login, no paywall, no DRM, no CAPTCHA; no video or
subtitle files redistributed. `robots.txt` disallows only `/play/pesquisa`,
which this pipeline never requests. Keep the request rate low, keep every row
linking back to RTP, and keep the attribution visible on the page: the
descriptions are RTP's text.
