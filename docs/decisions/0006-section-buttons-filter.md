# 6. Section buttons filter the list instead of jumping to it

**Date:** 2026-10-20
**Status:** accepted

## Context
The section buttons ("chips") under the search box were links that scrolled to a section
further down the page. With about 660 titles in one long list, that still left readers
scrolling past other sections, and on a phone it was easy to lose track of where a section
ended. Readers usually want one kind of program at a time (series, kids, films).

## Decision
- Tapping a chip **shows only that section** (heading, blurb and rows) and hides the rest.
  The chosen chip is highlighted. An **All** chip, first, with the total count, shows
  everything again; tapping the active chip again does the same.
- The counts on the chips stay as they are (the size of each section).
- **Search always covers every section.** Typing in the search box switches back to All and
  says so briefly ("Searching all sections"); clearing the search stays on All.
- The chosen section goes in the address (`#portuguese-tv-series`, or the short key such as
  `#series`), so a shared link opens on that section. Links shared before this change used the
  same section anchors, so they now open on that section instead of scrolling to it.
- On phones, choosing a chip closes the Sections drop-down and scrolls to the top of the list.
- Alongside: a "Newest first | A–Z" sort switch (remembered in the browser), accent-lenient
  search ("preco" finds "Preço"), and no English title line when it repeats the Portuguese.

## Alternatives considered
- **Keep the jump links.** Simple, but doesn't solve the long-scroll problem.
- **Jump and highlight**, leaving other sections visible. Still long on a phone.
- **Tabs replacing the chips.** Thirteen tabs don't fit on a phone; the chips already wrap.

## Consequences
- The page feels like a set of shorter lists, one per kind of program.
- A reader who arrives from an old section link sees only that section, with "All" one tap away.
- Filtering, sorting and search all run in the page's own small script; no library, still no
  outside requests.
