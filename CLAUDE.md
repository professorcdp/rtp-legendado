# Working agreement for Claude

This file tells Claude how to work on this project. PROJECT.md says *what* we're building; this file says *how* we work.

(How Claude should talk to Jim, in plain language and with a "Where:" line before every command, lives in his personal file at `~/.claude/CLAUDE.md`, which applies to every project.)

## At the start of every session
0. Open by stating this project's stamp in one line, e.g. "This is a BUSINESS project." Read it from the `.claude-account` marker file in this folder (that marker is what routes the folder to the right Claude Max account) and check it agrees with PROJECT.md. If they disagree or the marker is missing, tell Jim and fix it with `claude-stamp personal .` or `claude-stamp business .` (**Where:** VS Code terminal, in the project folder), then ask him to reload the VS Code window before continuing.
1. Read PROJECT.md, the latest 3 entries in docs/runlog.md, and any files in docs/decisions/.
2. Check open issues: `gh issue list`
3. Give Jim a short summary of where things stand and propose the next step (usually the top "priority: now" issue). Wait for his go-ahead before starting large changes.

## Task tracking (GitHub Issues)
- All work is tracked as GitHub Issues. Use the `gh` command-line tool.
- Labels:
  - Type: `feature`, `bug`, `chore`, `question`
  - Priority: `priority: now`, `priority: next`, `priority: later`
- Reference the issue in commit messages (e.g. "Add login screen (#12)"; use "Fixes #12" when a commit completes it).
- Close an issue when its work is done and committed.
- If you discover new work along the way, create a new issue for it rather than quietly expanding the current task.

## At the end of every session
1. Add an entry to docs/runlog.md (date, what changed, issues touched, what's next).
2. Update "Current status" in PROJECT.md if it changed.
3. If a significant decision was made (tech choice, architecture, a trade-off), record it as a new file in docs/decisions/ using the template there.
4. Commit and push.

## Working alongside the advisor chat
Jim usually runs a second, read-only Claude chat for this folder, started with /advisor. It plans, weighs options and writes the instruction blocks Jim pastes here. It reads docs/runlog.md, git log, git status, git diff and `gh issue list` directly, so the handoff to it IS the runlog entry plus the commit and push. When Jim says "hand off", "I'm done" or similar: do the end-of-session steps, then reply with at most three lines (what was done, what's open, anything only Jim can do). Never write a summary for Jim to copy into the advisor chat. If you need a decision from Jim, ask it in one short question; if it's a planning or priority question, say "that's one for the advisor chat" and stop.

## Code reviews
When Jim pastes a fix-it block from `/second-opinion`:
1. Fix the **Must-fix** items first, before touching anything else in the block.
2. Record the review's findings in docs/runlog.md: what was flagged, what was fixed, and what was deferred.
3. Open a GitHub Issue for each deferred item, with a type and priority label, so nothing gets lost.

## Rules
- Never commit secrets: API keys, passwords, certificates, .p8 keys, .env files.
- Before creating issues or pushing to GitHub, check `gh auth status` matches the project's stamp in PROJECT.md (business work uses the business GitHub account; personal uses personal).

## Project-specific notes
Filled in during setup: language/framework, how to build and run, how to test, anything unusual.
-
