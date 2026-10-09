# Method, in plain terms

Everything the pipeline does, in the order it does it, with the exact addresses,
parameters and patterns involved. This is the description to read if you want to
verify or re-implement the work rather than run the scripts.

Snapshot the published page was built from: **11 September 2026** — 6,268 TV
programmes checked, 649 with a Portuguese subtitle track, 281 of those blocked
from outside Portugal.

---

## 0. What we are looking for

RTP Play exposes nothing about subtitles in its listings. But every **episode**
page embeds the video player's configuration inline in the HTML, and when a
subtitle file exists that configuration contains a line of this shape:

```js
vtt: [['PT','Português adaptado','https://cdn-ondemand.rtp.pt/nas2.share/legendas/video/web/p16438/p16438_1_20260523084741e010t7883d.vtt']],
```

Presence of that line is the whole detection method. No playback, no sign-in, no
video or subtitle file is redistributed.

Two traps:

- The same page contains a **commented-out example block** that mentions `vtt`
  and a `seekBarThumbnailsLoc` that ends in `.vtt` (preview thumbnails, not
  subtitles). Match the full `vtt: [['..','..','..']]` shape, not the string
  `vtt`.
- RTP's accessibility site publishes daily *legendagem em teletexto* schedules.
  Those are **broadcast** captions on the TV channels and do not reliably carry
  over to the on-demand catalogue. The Play page's own player config is the only
  authority.

## 1. Enumerate the catalogue

The programme listings are loaded by AJAX, not server-rendered, so the browse
pages look empty to a scraper. The endpoint behind them is:

```
GET https://www.rtp.pt/play/bg_l_pg/
    ?listDate=&listQuery=&listProgram=
    &listcategory=<category id>
    &listchannel=
    &listtype=recent
    &page=<1..n>
    &type=tv
```

It returns an HTML fragment of `<article>` blocks, 12 per page; an empty
response means the end of that category. Walk pages until empty, for each of the
17 categories:

| slug | id | | slug | id |
|---|---|---|---|---|
| informacao | 1 | | entretenimento | 10 |
| cultura | 2 | | ciencia-e-natureza | 11 |
| humor | 3 | | entrevista-opiniao-e-debate | 12 |
| musica | 4 | | gastronomia | 13 |
| desporto | 5 | | artes | 14 |
| infantis-e-juvenis | 6 | | religiosos-e-reflexao | 15 |
| institucionais | 7 | | saude | 16 |
| outros | 8 | | especiais | 17 |
| ficcao | 9 | | | |

(The ids come from `currentHPListCategory` on each `/play/programas/<slug>/canal`
page; `step01_catalogue.py --refresh-categories` re-reads them.)

From each `<article>` take:

- the link `/play/p<pid>/e<eid>/<slug>` — the programme's **latest episode**
- `title="Aceder a …"` — the title
- the icon class: `fa-volume-down` marks a **radio** programme, `fa-play` a TV one
- the hidden `<meta content="Title Ep. 8 11 set. 2026">` — episode number and date

`type=tv` does **not** actually exclude radio, hence the icon check. September
2026 figures: 7,779 programmes total, **6,268** of them television.

Note that this is a per-programme listing keyed on the latest episode, which is
what makes the next step affordable — one page per programme rather than one per
episode.

## 2. Check every programme for subtitles

For each of the 6,268 TV programmes, fetch the latest-episode URL from step 1
and look for the `vtt:` line. While the page is open, also take:

- `fileKey` — needed for the rights check (see step 3). It is obfuscated as
  `fileKey: atob(decodeURIComponent(["aHR0cH","M6Ly9z",…].join("")))`, so join
  the chunks, percent-decode, base64-decode.
- `<meta name="keywords">` — channel and genre (`RTP1|Ficção`, `Originais RTP Play|Ficção`,
  `RTP Zig Zag|Infantis e Juvenis`)
- `<meta name="description">` — the latest episode's description
- `<meta property="og:title">` — the programme's own name (the listing title is
  sometimes the episode title)
- every `Este conteúdo faz parte de X` heading — RTP's collections
  (*Séries nacionais*, *Cinema Português*, *Cinema Internacional*,
  *Exclusivas RTP Play*, *RTP Lab*…), which drive the genre rules later
- how many `/play/p<pid>/e<id>` links the page carries — an episode count that
  saturates around 12–13 because the page only lists a carousel's worth

Result: **649** programmes with a Portuguese subtitle track, about one in ten.

### Is it a caption or a translation?

Every track is labelled *Português adaptado*, whether it is SDH on Portuguese
audio or a Portuguese translation of an English-language film, so the label
alone is useless. Two things help:

1. **RTP's own tags.** *Cinema Internacional*, *Séries Estrangeiras* and (in
   practice) *Originais RTP Play* mark acquired foreign material; *Séries
   nacionais*, *Cinema Português*, *RTP Lab* mark Portuguese production.
2. **The subtitle file itself.** Download the `.vtt` and count all-caps sound
   cues (`RISOS`, `MÚSICA`, `GEME`, `MIAR AGRESSIVO`, `NARRADORA:`). They appear
   in SDH written for Portuguese audio and are largely absent from translation
   subtitles. Useful as a signal, not a verdict — plenty of Portuguese drama has
   few cues.

Neither is conclusive, so the final foreign/Portuguese split is a hand-kept list
in `config/overrides.json`. That file is the part a rebuild has to maintain.

The `.vtt` download doubles as a sanity check: a handful of programmes have a
subtitle track whose file is empty or a stub. Anything under 30 subtitle lines is
dropped.

## 3. Does it play outside Portugal?

The *SEM DIREITOS DE TRANSMISSÃO ONLINE* screen is decided client-side. The
player asks:

```
GET https://www.rtp.pt/services/rtpplay/?v=5&file=<fileKey>
```

and gets back a small JSON object:

```json
{"country":"ES","rights":1,"video":{"streamer":"h2e.rtp.pt","file":"nas2.share/…"},
 "timeout":10800,"live":1,"cachefile":"STATIC"}
```

`rights: 0` means the player is replaced by RTP's rights poster. `country` is
how RTP geolocated the requesting IP — so **the answer describes the machine
running the check**, which is why the page says "when I ran the check" rather
than "where you are". In September 2026, from a connection RTP placed in Spain:
**281 of 649 blocked**, 368 playable.

Incidental finding: files licensed for Portugal only sit under a `/pt/` path
segment inside the fileKey (`/nas2.share/pt/h264/512x384/p16438/…`), so the
restriction is visible in the path independently of where you ask from. The
pipeline records both.

## 4. Show-level descriptions

For a series, the latest episode's description ("Bela descobre a verdade sobre a
morte da mãe…") tells a learner nothing about the show. So for series and
recurring strands, fetch the **programme** page `/play/p<pid>/` and take the
longer of:

- `<meta name="description">` — a one-line tagline
- the longest `<p>` in the body — usually a fuller synopsis

skipping credit lists (`Intérpretes:`, `Autoria:`, `Realização…`). Cap at 400
characters; if RTP's own text is cut off mid-sentence, end with `…`.

Applied to 240 programmes: all 72 series, plus entertainment, kids, magazines,
food, the language strands, and any documentary strand with ≥ 8 episodes.
One-off films and documentaries keep their own description, which is already
about the title itself. Two programmes (*Desliga a Televisão*, *Dicas.ANACOM*)
have no usable blurb and keep the episode text.

## 5. Sections and merging

Sections are a rule cascade over RTP's own category, channel and collection
tags — in order, first match wins:

1. pid in `foreign_fiction` override → **foreign**
2. pid in `language_and_literature` override → **lang**
3. category `infantis-e-juvenis` → **kids**
4. fiction + `Teatro` → **stage**
5. fiction → **film** if tagged *Cinema Português* / *Filmes Portugueses* /
   *Cinema Internacional*, or if it has ≤ 2 episodes and is not tagged as a
   series; otherwise **series**
6. pid in `international_documentary` override → **intl**
7. music category, `Musicais`/`Música` channel, or *Concertos* → **music**
8. `Teatro` collection → **stage**
9. humour or entertainment category → **fun**
10. gastronomy → **food**
11. science/nature category, or a *Ciência e Natureza* / *Ecologia* /
    *Ciência, Tecnologia* collection → **nature**
12. news, interview, institutional, health categories, or `outros` with ≥ 8
    episodes → **mag**
13. everything else → **docs**

Then **merge seasons**: one show often has several programme ids (*Água de Mar*
has three, *Salto de Fé* three). Rows are merged on the normalised title, with
films kept separate from a series of the same name; the extra seasons appear as
"Also:" links. The row's main link prefers a season that actually plays, so a
blocked newest season doesn't hide a watchable older one. A row counts as
playable if any of its seasons does.

Dropped: titles matching `Mensagem de Natal|Trailer|^Remo$` (one-off
institutional items and trailers).

## 6. English translations

Every title and every description is translated by an LLM in batches, with
instructions to translate titles meaningfully (*Bem-vindos a Beirais* → "Welcome
to Beirais"), leave proper names alone, repeat titles that are already English
or are just a name, and preserve the trailing `…` where RTP's text was cut off.
`step06_translate.py` carries the exact prompt and caches by a hash of the source
text, so a rebuild only pays for rows whose text changed.

Quality: produced in bulk and spot-checked, not proofread line by line. Puns
flatten — *Música de Graça* ("free music" / "Graça's music") comes out as
"Graça's Music".

## 7. The page

`step07_render.py` concatenates `templates/page_head.html` (title, Google Fonts
link, CSS with light/dark tokens) and `templates/page_body.html` (markup plus the
~60 lines of vanilla JS that render the rows, the search box, the "hide blocked"
and "show English" checkboxes), substituting the dataset JSON for the `__DATA__`
placeholder, and wraps it in a `<head>` carrying the canonical URL and the
social-card tags. The result is one self-contained HTML file with no runtime
dependencies, deployable by copying it to GitHub Pages.

`og.png` (1200×630 social card) is in the repo and is referenced by `og:image`.

**Note on the live page:** the page currently published at
jamminalley.github.io/rtp-legendado was restyled afterwards in Claude Design,
which emitted static markup for the rows rather than rendering them from a data
block. That file is not produced by this pipeline. Either keep the Design file
and treat this pipeline as the data source (re-applying the design to each
rebuild), or adopt `templates/` as the canonical page and port the Design
styling into `page_head.html`. The second is what makes a scheduled rebuild
actually automatic — see README.
