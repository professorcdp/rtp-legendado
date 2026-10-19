# RTP Play Legendado

**https://legendado.professorcdp.com/**

A reference list of the programs on [RTP Play](https://www.rtp.pt/play/) that carry a Portuguese
subtitle track, for learners of European Portuguese who want comprehensible input.

## What's on the page

- Every RTP Play TV program whose latest episode has a Portuguese subtitle track (the one RTP
  calls *Português adaptado*), grouped by genre. Portuguese-language shows come first;
  international documentaries and foreign-language fiction, where the subtitles are a
  translation, are at the bottom.
- **English translations** of every title and description, which can be hidden to read the
  Portuguese cold first.
- A **Portugal-only license** label and filter, for titles RTP licenses for Portugal only.
- Short notes where they matter to a learner, such as *Brazilian Portuguese*.
- The same data as a spreadsheet: [rtp-play-legendado.csv](https://legendado.professorcdp.com/rtp-play-legendado.csv).

The page is one self-contained HTML file. It embeds its font and data, makes no requests to
anyone else, and has no tracking.

## How it's built

The list rebuilds itself every Monday. A GitHub Actions workflow
([.github/workflows/site.yml](.github/workflows/site.yml)) runs the pipeline in
[pipeline/](pipeline/), which:

1. lists every TV program in the RTP Play catalog;
2. checks each one's latest episode for a subtitle track;
3. sorts the titles into sections, using RTP's own tags plus a hand-kept list;
4. translates new or changed text into English (through the Anthropic API);
5. renders the page and the CSV, and publishes them to GitHub Pages.

Each run compares itself with the previous week's list, and refuses to publish if something
looks broken (the list shrinking sharply, many titles sharing one description, or the
Portugal-only labels disappearing).

- **How it works, step by step:** [pipeline/METHOD.md](pipeline/METHOD.md)
- **What has gone wrong before, and what to watch for:** [pipeline/GOTCHAS.md](pipeline/GOTCHAS.md)
- **Running it by hand:** [pipeline/README.md](pipeline/README.md)
- **Why it's set up this way:** [docs/decisions/](docs/decisions/)

## The weekly review

RTP labels every subtitle track the same way, whether it's captions for Portuguese audio or a
translation of a foreign film. So foreign-language titles can't be detected automatically.

When a weekly run adds or removes titles, it opens a GitHub issue listing them. Go through the
new titles in the Portuguese series, films, documentaries and nature sections, and add any that
aren't Portuguese-made to [pipeline/config/overrides.json](pipeline/config/overrides.json):

- `foreign_fiction`: films and series in another language;
- `international_documentary`: documentaries made abroad;
- `notes` and `page_notes`: background, and a short label shown on the page (for example,
  Brazilian Portuguese titles stay in the Portuguese sections with a *Brazilian Portuguese* label).

The next weekly run, or a manual run of the workflow from the Actions tab, moves them.

## Caveats

- Only the latest episode of each program is checked, so a show may have subtitles on some
  episodes and not others.
- Titles without the Portugal-only label usually play outside Portugal, but not always, and
  rights change over time.
- For foreign-language films and series the Portuguese subtitles are a translation, not a
  transcription of the audio: useful for reading, not for listening.
- RTP's catalog changes constantly; treat the list as a weekly snapshot.

Data belongs to RTP – Rádio e Televisão de Portugal. The page only links to their pages and
quotes their program descriptions, with attribution. The Inter font is used under the SIL Open
Font License (see [pipeline/templates/fonts/](pipeline/templates/fonts/)).
