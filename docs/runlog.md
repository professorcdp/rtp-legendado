# Runlog

Newest entries at the bottom. One entry per working session.

Format:
## YYYY-MM-DD
- **Did:** what changed
- **Issues:** #numbers touched, opened, or closed
- **Next:** what the next session should pick up
- **Notes:** anything surprising, blocked, or worth remembering

---

## 2026-10-09
- **Did:** Adopted the 2nd brain workflow. Moved the repo from jamminalley/rtp-legendado to the professorcdp org (Jim ran the transfer himself, because Claude Code's safety check blocked it). The site now lives at https://professorcdp.github.io/rtp-legendado/. Created a public forwarding repo at jamminalley/rtp-legendado (index.html and 404.html redirect to the new address, keeping path, query and #anchor) so the link already shared with students keeps working. Connected this folder to the moved repo. Filled in PROJECT.md from the README, created the issue labels, and recorded decision 0001.
- **Issues:** opened #3 (how long to keep the forwarding site)
- **Next:** Decide how and how often to refresh the list. The build process isn't in the repo yet.
- **Notes:** The repo is public, so CLAUDE.md, PROJECT.md and docs/ are visible to anyone. Keep anything private out of them.

## 2026-10-09 (weekly rebuild, in progress)
- **Did:** Copied the rebuild pipeline from rtp-legendado-pipeline.zip into `pipeline/`. Smoke test on GitHub Actions passed: RTP answers GitHub's machines and placed them in Spain; all 765 September links were re-read with 0 errors (#4, closed). Portugal-only flag vs the September Spain check: 93.6% agreement, flag unchanged since September (#5). Ported the Claude Design look into `pipeline/templates/` and rewrote `step07_render.py` to produce it; step 5 now records the Portugal-only flag. Showed Jim a side-by-side preview built from September data.
- **Issues:** opened #4–#9 (one per step); closed #4.
- **Next:** Jim's OK on the rebuilt page, then publishing from GitHub Actions (#7) and the weekly workflow (#8).
- **Notes:** The zip's workflow ran its smoke test before step 1, so it would always have failed; the new smoke test runs step 1 on one small category first. Without an API key, step 6 would have blanked every English translation; the plan is to seed the translation cache from the September snapshot.

## 2026-10-09 (review)
- **Reviewed:** d8738fe..e8e638b plus uncommitted template and step05/step07 changes (latest commit e8e638b)
- **Verdict:** Mostly sound. Nothing must be fixed now; two things to settle before the weekly rebuild is built.
- **Findings (by rank):**
  - Should fix:
    - a) Weekly rebuild would never drop vanished programmes or re-check existing ones if data/*.json state files are committed between runs (step01 only adds; step02/step03 skip "done" entries). Also pipeline/data/dataset.json is an untracked hand-made file that git add -A would commit.
    - b) Template footer claims "The list is rebuilt every week" before any weekly workflow exists (templates/page_body.html line 37).
    - c) Docs out of sync: issue #4 references docs/decisions/0002-automatic-weekly-rebuild.md, which doesn't exist; runlog has no entry for the pipeline session; PROJECT.md still says the build process isn't in the repo.
    - d) gh is logged in as jamminalley (personal account per decision 0001) on a business-stamped project; confirm this is intended and note it in PROJECT.md.
    - e) No automated tests; suggest a small test running steps 5 and 7 against snapshot/dataset-2026-09-11.json and checking row/section/pt counts.
  - Could fix:
    - f) Hard-coded "1 in 12" in page_body.html line 35 and the 6268 fallback in step07_render.py line 128 will go stale.
    - g) Port lost accent-insensitive search (page_body.html lines 48-52) and the rule hiding English titles identical to the Portuguese one (step07_render.py lines 104-105).
    - h) smoke.yml lines 64-65 re-run the one-off check_pt_only.py comparison on every smoke test (765+ requests to RTP each time).
- **Fixed:**
  - a) Decided the weekly run starts from fresh state: `pipeline/.gitignore` now excludes every `data/*.json` except `dataset.json` (the published list, for comparison) and `translations.json` (keyed by content hash). Recorded in decision 0002. Deleted the hand-made `pipeline/data/dataset.json` (it was preview data built from the September snapshot, not step 5 output).
  - b) Footer reverted to "Treat this as a snapshot."; #8 notes to restore the weekly wording once the schedule is live.
  - c) Wrote docs/decisions/0002-automatic-weekly-rebuild.md, added this session's runlog entry, and updated PROJECT.md.
  - d) Noted in PROJECT.md that the professorcdp org owns the repo and work is done as jamminalley, an org admin. Marked as inferred; Jim to confirm.
  - h) Removed check_pt_only.py from smoke.yml; the script is now marked as a one-off to run by hand.
- **Deferred:** e) #10 (chore, priority: next); f) #11 (chore, priority: later); g) #12 (chore, priority: later).

## 2026-10-10 (weekly rebuild goes live)
- **Did:** Jim approved the rebuilt page. Switched GitHub Pages to publish from GitHub Actions (`.github/workflows/site.yml`); a watcher polling every 3s across the switch saw no downtime, and the first deploy was byte-identical to the old site. Built the weekly workflow (Mondays 04:17 UTC): compares with the previous run's committed list, opens a review issue when titles change, uses claude-sonnet-5-5 or `--no-translate` without a key, RTP_WORKERS 4. Seeded translations from the September snapshot. First manual run (no translations) published broken descriptions on 200 rows and mis-sectioned 49 nature titles because RTP's pages changed (SVG `<path>` matched the paragraph pattern; collection heading now uses `&uacute;`; keywords format changed). Jim chose not to roll back (only two people know the URL). Fixed step02/04/05, added publish guards (no publishing if more than 15 titles share a description or the list shrinks below 70%), re-ran: 664 titles live, 61 nature, 241 Portugal-only, 612 English titles, 562 English descriptions. Restored the "rebuilt every week" footer line.
- **Issues:** closed #5, #6, #7, #8, #9; #13 opened by the workflow (52 added, 37 removed titles to review for foreign-language ones).
- **Next:** Jim adds the `ANTHROPIC_API_KEY` Actions secret (then run the workflow by hand to translate the 101 missing descriptions). Review #13. Then #10 (tests).
- **Notes:** A full rebuild took 31 minutes, not the ~2 hours the pipeline docs predicted. The HTTP cache made the same-day re-run take 7 minutes. RTP placed GitHub's machine in Spain both times.

## 2026-10-10 (translations on)
- **Did:** Jim added the `ANTHROPIC_API_KEY` Actions secret. Ran the workflow by hand with translations: 101 titles and descriptions translated (claude-sonnet-5-5); live page now has English on all 664 titles and all 663 descriptions. Spot-checked new translations; they read well.
- **Issues:** none opened or closed.
- **Next:** Review #13 for foreign-language titles. Then #10 (tests).

## 2026-10-10 (review)
- **Reviewed:** e8e638b..5d25b91 (latest commit 5d25b91)
- **Verdict:** Sound overall; nothing must be fixed now, but two silent-failure gaps should be closed before the first scheduled Monday run.
- **Findings (by rank):**
  - Should fix:
    - a) No guard for the Portugal-only flag collapsing to zero if RTP changes the fileKey markup (pipeline/step05_dataset.py line 150; guards in pipeline/report_changes.py lines 60-66 don't cover it).
    - b) Translation API failures are swallowed (pipeline/step06_translate.py lines 121-122); new titles publish without English and the workflow stays green.
    - c) Page loads the Inter font from Google (pipeline/templates/page_head.html lines 3-5) while the colophon (page_body.html line 39) and PROJECT.md say "no dependencies, no tracking". Pre-dates this range.
    - d) Repo root is stale: root index.html and rtp-play-legendado.csv are the September files; README.md lines 11-17 describe the September list and the removed "SEM DIREITOS" filter; site.yml lines 139-140 fallback is dead code.
  - Could fix:
    - e) gh issue create (site.yml line 108) failing would block the deploy job even though the list is already committed.
    - f) "about 2 hours" is stale in site.yml lines 3 and 18, docs/decisions/0002 line 35 and run_all.py line 14 (real time about 31 minutes).
    - g) GitHub disables scheduled workflows after 60 days of repo inactivity; unclear whether bot commits count. Note it in GOTCHAS.md.
- **Fixed:**
  - a) report_changes.py refuses to publish if the Portugal-only count is 0 or under 50% of the previous list's. Tested: with every row's flag zeroed, it exits with an error; normal runs pass.
  - b) step06 counts failed batches and prints a `::warning::`; report_changes.py outputs the untranslated count and adds it to the review issue; site.yml warns when rows lack English after a run with a key, and opens the review issue in that case even if no titles changed. Tested with a deliberately invalid key on a scratch copy.
  - e) The review-issue step now has `continue-on-error`, so a failure there can't block publishing.
  - f) Timing updated to about 30 minutes in site.yml, decision 0002, run_all.py, pipeline/README.md and GOTCHAS.md.
  - g) GOTCHAS.md notes the 60-day rule and how to re-enable the schedule.
- **Deferred:** c) #14 (chore, priority: next); d) #15 (chore, priority: next).
- Also noted: no automated tests (#10 still open); the reviewer could not run the pipeline locally (requests not installed).

## 2026-10-10 (new-title review)
- **Did:** Reviewed the 28 new titles from #13 in series/films/documentaries/nature with Jim, using RTP's collection tags, descriptions and episode slugs (the .vtt sound-cue counts were near zero for everything, Portuguese-made included, so not a useful signal any more). Jim confirmed all: added 4 to `foreign_fiction` (Dalíland, O Caloiro, Cry Macho, A Febre), 11 to `international_documentary`, and a Brazilian Portuguese note for Bye Bye Brasil. Re-ran the workflow; the live page shows all 16 in the right sections.
- **Issues:** closed #13; opened #16 (per-title notes such as "Brazilian Portuguese" are in the data but never shown on the page or in the CSV).
- **Next:** #14 (Google font vs "no tracking") and #15 (stale repo root), both waiting on Jim's choice; #16; #10 (tests).

## 2026-10-11 (notes, font, tidy-up)
- **Did:** #16: added `page_notes` to overrides.json (Jim approved: Brazilian Portuguese ×3, Much Crioulo, Partly in English); shown as a lavender tag beside the title and in a new CSV "Note" column; the two daily soap/sitcom notes stay data-only. #14: embedded Inter (variable, Latin subset, OFL) in the page instead of loading it from Google; page 726 KB → 796 KB; checked in a browser that Inter loads and nothing outside the page is requested. #15: removed the September root index.html and CSV, removed the dead fallback in site.yml, rewrote README.md, updated METHOD.md and PROJECT.md. Ran the rebuild; live page checked (tags, font, CSV Note column, og.png, old jamminalley link).
- **Issues:** closed #14, #15, #16. The rebuild opened #17 (4 new titles to review).
- **Next:** Review #17. Then #10 (tests), #11, #12 when convenient.

## 2026-10-11 (new-title review)
- **Did:** Closed #17: Catatuas-Negras em Risco de Vida (17264) added to `international_documentary` (RTP2 nature doc about Western Australia); Uma Abelha na Chuva (9155) stays Portuguese. Rebuilt; live page shows it under International documentaries.

## 2026-10-14 (new-title review)
- **Did:** Closed #18: Beautiful Wedding (17253) → `foreign_fiction`, Expedição Quebeque-Labrador (16492) → `international_documentary`, A Ferro e Fogo (17310) stays Portuguese. Rebuilt; live page shows both in their new sections. The rebuild found further changes and opened #19.

## 2026-10-15 (compare by pid)
- **Did:** Fixed #20: `pipeline/report_changes.py` now matches this week's and last week's rows by RTP programme id (any shared pid, including merged seasons) instead of by title, and lists title changes under "Renamed" (renames alone don't open a review issue). Tested on the 12 Oct vs 14 Oct lists (c96be96 → b3ddaf7): A Minha Lancheira (17159) now shows as renamed; 1 added, 7 removed, 1 renamed.
- **Issues:** closed #20. Open: #21 (grace period, needs Jim's decision), #10, #11, #12, #3.

## 2026-10-15 (phone layout)
- **Did:** Fixed #22: on screens up to 640px the pinned bar is now one row (search + "Sections ▾"); the chips and the two checkboxes drop down as a panel that closes on a chip, a tap outside or Escape; section headings land just below the bar. Desktop unchanged (measured against the previous page). Jim approved phone-width screenshots; published with the workflow's publish mode and tested on the live site with a scripted Chrome at 412px.
- **Issues:** closed #22.
- **Next:** Jim to try it on his Pixel 8. Open: #21 (needs Jim's decision), #10, #11, #12, #3.

## 2026-10-17 (spelling, copyright, custom domain prep)
- **Did:** #23: American spelling in reader-facing text (page template, section labels, CSV header now "Program" and "Portugal-only license", review-issue text, README, PROJECT): program(s), license, catalog, Theater, labeling. The `#theatre` anchor id is unchanged so existing links keep working; step05/METHOD/GOTCHAS left as internal. #24: footer now reads "© {year} Jim Ranalli / Professor CDP. Program descriptions © RTP – Rádio e Televisão de Portugal; this page only links to their pages." with the year from the build date. #25: made the site address one setting (`SITE_URL` in site.yml, read by step07, which also writes a CNAME file for a custom domain); decision 0003 records the switch-over order.
- **Not done, deliberately:** did not set the custom domain on Pages or repoint the jamminalley forwarding site. Setting it makes GitHub redirect the current address to legendado.professorcdp.com straight away, which would take the site offline until the DNS record exists. No workflow run: the spelling and copyright changes go live with the next run (scheduled Monday 19 Oct), which still uses the github.io address.
- **Issues:** opened #23, #24, #25; closed #23, #24. #25 waits on Jim's DNS record.
- **Next:** Jim adds DNS (CNAME, host `legendado`, value `professorcdp.github.io`); then follow the steps in decision 0003.

## 2026-10-18 (custom domain live)
- **Did:** Jim added the DNS record in Squarespace Domains (professorcdp.com is managed there, reached from the Workspace Admin console via Manage domains → View details; Google's name servers): CNAME `legendado` → `professorcdp.github.io`. It resolved within a minute. Followed decision 0003: set the custom domain on Pages, switched `SITE_URL` to https://legendado.professorcdp.com and published (this also put #23's spelling and #24's copyright line live), certificate issued straight away, turned on Enforce HTTPS, and pointed the jamminalley forwarding site straight at the new domain. Checked in a browser: jamminalley.github.io/rtp-legendado (with query and #anchor), professorcdp.github.io/rtp-legendado and http:// all land on https://legendado.professorcdp.com/; the old jamminalley CSV link downloads the current CSV from the new address.
- **Issues:** closed #25.
- **Next:** Open: #21 (needs Jim's decision), #10, #11, #12, #3.

## 2026-10-18 (American spelling in translations)
- **Did:** Fixed #26: the translation prompt now asks for American spelling, and `americanize()` in step06 converts new, cached and September-seeded translations (whole words, case kept; the official name "Centre for Ecology, Evolution and Environmental Changes" is left alone). Converted the saved translations without re-translating: 95 of 761 cache entries, 82 rows of dataset.json. "dialogue" and "archaeology" left as they are (standard in American English too). Published (render only); live page has no programme/licence/catalogue in any English text.
- **Issues:** closed #26.

## 2026-10-18 (review)
- **Reviewed:** 5d25b91..9b6977d (latest commit 9b6977d)
- **Verdict:** Sound. Nothing must be fixed; two things worth tidying before building further on the spelling converter and the comparison logic.
- **Findings (by rank):**
  - Should fix:
    - a) americanize() in pipeline/step06_translate.py lines 81-97 rewrites proper names ("Labour Party" → "Labor Party", "Lincoln Centre" → "Lincoln Center"); only one name is protected. No damage found in today's 660 rows.
    - b) No automated tests for report_changes.py (added/removed/renamed and the three guards) or americanize(); verified by hand only.
  - Could fix:
    - c) Site address duplicated: SITE_URL in .github/workflows/site.yml line 31 and the fallback default in pipeline/step07_render.py line 128, though decision 0003 calls it one setting.
    - d) report_changes.py pid() returns "?" for a link without an id, and two such rows would be treated as the same programme; every current row has an id.
    - e) CSV "Note" column was inserted mid-row (step07_render.py lines 208-214), shifting the description columns for anyone using the September column order.
  - Tests run by the reviewer: report_changes.py against b3ddaf7's list (0/0/0, untranslated 0), against a doctored list (1 added, 1 removed, 1 renamed as expected), and with the Portugal-only guard tripped (refused to publish); step07 renders 660 rows with no leftover placeholders and no outside hosts; last six workflow runs succeeded; git history clean of real keys. Phone "Sections" panel not re-checked in a browser this session.
- **Fixed:** none in this session (no Must-fix items).
- **Deferred:** a) #27 (bug, priority: next); b) test cases added as a comment on #10 (no new issue); c) #28 (chore, priority: later); d) #29 (chore, priority: later); e) #30 (chore, priority: later).

## 2026-10-20 (captions, not subtitles)
- **Did:** Fixed #32 and recorded the rule in decision 0004: the page says captions / caption track / captioned for Portuguese-language shows, and keeps subtitles for International documentaries and Foreign-language fiction (translations); the lede explains "captions (same-language subtitles, what RTP calls Português adaptado)"; meta and og:description use both words for search. Also updated the stat label, section blurbs, the review-issue text, README and PROJECT. Published (render only); live page checked: every remaining "subtitle" is one of the allowed uses.
- **Issues:** closed #32; opened #33 (og.png social card still shows the September design and wording).
- **Next:** #27 (spelling converter and proper names), #33, #10.

## 2026-10-20 (titles, social card, Zig Zag, filter default)
- **Did:** #31: with Jim, Beleza Colateral and Sobretudo de Noite (Spanish: *Sobre todo de noche*, not Portuguese as expected) → `foreign_fiction`; Estátua da Liberdade, Vivam os Micróbios!, Austrália Tropical Original, Sozinho num Atol Secreto → `international_documentary`. #33: new og.png drawn by `pipeline/tools/make_og.py` (Claude Design colours, Inter, captions headline, no numbers); Jim approved it. Full rebuild published both. #34: new step `step05b_zigzag.py` links kids rows to RTP Play Zig Zag when the Zig Zag page has its own caption track (Zig Zag returns 200 even for made-up addresses, so a status check isn't enough); 53 of 53 kids rows now link there. #35: Zig Zag's 171 TV programs are all in the weekly sweep; nothing missed. #36: Portugal-only filter unticked by default with a new label (decision 0005); all 662 titles show on load.
- **Issues:** closed #31, #33, #34, #35, #36. The weekly rebuild opened #37 (2026-10-20 review).
- **Next:** #37, then #27.

## 2026-10-20 (section filters, sort, search)
- **Did:** #38: section chips now filter the list to one section, with an "All" chip first, the active chip highlighted, re-tap = All, search always covering every section (with a brief "Searching all sections" note), and the section in the URL hash (#portuguese-tv-series or #series; old section links open that section). Decision 0006. #39: "Newest first | A–Z" switch (A–Z ignores accents, case and a leading article), remembered in localStorage. #12: accent-lenient search; English title line hidden when it repeats the Portuguese (66 rows). Tested locally and on the live site with a scripted Chrome at 1280px and 412px. Published (render only).
- **Issues:** closed #38, #39, #12.
- **Next:** Jim to run /second-opinion in a new chat. Open: #37 (2026-10-20 review), #27, #21, #10, #11, #28, #29, #30, #3.
