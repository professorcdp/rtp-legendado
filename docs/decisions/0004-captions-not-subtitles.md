# 4. Say "captions" for Portuguese-language shows, "subtitles" for translations

**Date:** 2026-10-20
**Status:** accepted

## Context
The page called RTP's *Português adaptado* track "subtitles" everywhere. In American usage,
which the site follows (decision on spelling, issue #23), **captions** are same-language text
(what's spoken, plus sound cues), and **subtitles** are a translation into another language.
For most of the list, the Portuguese text is captions of Portuguese audio. Only in two
sections (International documentaries and Foreign-language fiction) is it a translation.
Using one word for both blurred the distinction the page most wants learners to notice.

## Decision
- Portuguese-language sections, and the page in general: **captions**, **caption track**,
  **captioned**. The headline is "What on RTP Play has Portuguese captions?".
- International documentaries and Foreign-language fiction: keep **subtitles**, because there
  the Portuguese text translates another language. The blurbs and the caveat make the
  contrast explicit: captions transcribe, subtitles translate.
- The lede explains the word once, where it first appears: "captions (same-language subtitles,
  what RTP calls *Português adaptado*)". The "press CC" instruction stays.
- The meta description and og:description use both words ("Portuguese captions (same-language
  subtitles)") so searches for "Portuguese subtitles RTP Play" still find the page.
- Unchanged: "Legendado" in the project name, the domain and the CSV filename; internal docs
  (METHOD.md, GOTCHAS.md) and code names (`subtitles.json`, `step02_subtitles.py`).

## Alternatives considered
- **Keep "subtitles" throughout.** Matches what most people type into a search box, but loses
  the distinction between transcription and translation that matters for listening practice.
- **"Captions" everywhere, including the foreign sections.** Wrong: there the text is a
  translation.

## Consequences
- The wording now carries the page's key advice by itself: captioned shows are for listening
  practice, subtitled ones for reading.
- The social-card image (og.png) still says "subtitles"; redrawing it is issue #33.
