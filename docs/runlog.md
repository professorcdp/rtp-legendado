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
