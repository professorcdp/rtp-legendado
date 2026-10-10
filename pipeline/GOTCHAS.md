# What went wrong, and what to watch for

Everything in this list actually happened during the September 2026 build. Most
of it is encoded in the scripts; it's here so the next person (or the next you)
knows why the code is shaped the way it is.

## Rate limiting is real and silent

Running the 6,268-page sweep with two overlapping sets of workers (~24
concurrent requests) slowed RTP's responses from **0.4 s to 38 s per page** —
no error, no 429, just molasses. Dropping back to 5–6 concurrent restored
normal speed immediately.

Consequences baked in:

- `common.py` defaults to `RTP_WORKERS=5` and a 0.15 s global gap between
  requests. Raising it is the fastest way to make a rebuild slower.
- Every step is resumable and caches responses on disk, so a bad run costs
  minutes, not hours.
- A full cold run is roughly 2 hours, almost all of it waiting.

## The listings are AJAX, and `type=tv` doesn't filter radio

The `/play/programas/...` pages look nearly empty to a fetcher: the listings
come from `/play/bg_l_pg/`. And despite `type=tv`, radio programmes come back
too (1,511 of 7,779 in September). They're identifiable only by the icon class
in the markup (`fa-volume-down` vs `fa-play`).

## The subtitle marker has a decoy

Episode pages contain a commented-out example player block that mentions `vtt`,
plus `seekBarThumbnailsLoc: '…_preview.vtt'` for the scrubber thumbnails. A bare
search for `vtt` gives false positives on nearly every page. Match the full
`vtt: [['PT','Português adaptado','…']]` shape.

## Programme pages don't carry the player

The `vtt:` line is on **episode** pages (`/play/p<pid>/e<eid>/<slug>`), not on
programme pages (`/play/p<pid>/`). Checking programme pages finds nothing.

## fileKey is obfuscated

`fileKey: atob(decodeURIComponent(["aHR0cH","M6Ly9z",...].join("")))`. Join,
percent-decode, base64-decode. A minority of pages use a plain string instead,
so both forms are handled.

## The rights answer depends on where you ask from

`/services/rtpplay/?v=5&file=…` reports the requesting IP's country. The
published figures were taken from a connection RTP geolocated to **Spain** — not
Portugal, not the US. A rebuild running on GitHub Actions will report whatever
country the runner sits in (usually the US), which is a *different* blocked set.
Decide deliberately:

- run the rebuild from a machine in the country your readers are in, or
- publish the `pt_only` flag (derived from the `/pt/` path segment) instead,
  which is location-independent, or
- say plainly on the page which location the check was made from.

## Captions and translations are labelled identically

Every track says *Português adaptado*. Foreign-language fiction and acquired
documentaries can't be separated from the track metadata, so they live in
`config/overrides.json` as hand-kept pid lists (33 foreign fiction, 42
international documentaries as of September 2026). **This is the maintenance
burden of the project.** After each rebuild, review new rows in the `series`,
`film`, `docs` and `nature` sections for things that are obviously not
Portuguese-made, and add their pids.

Helper signals the scripts record for you: RTP's collection tags, the channel
(`Originais RTP Play` is overwhelmingly acquired), the episode slug (foreign
originals often keep the original title: `esto-no-es-suecia`, `the-couple-next-door`,
`les-derniers-secrets-de-la-humanite`), and the sound-cue counts from the `.vtt`.

## Empty subtitle files

A handful of programmes advertise a track whose `.vtt` is empty or two lines
long (*Sociedade Civil*, *Janela Indiscreta*, *Biosfera* among them in
September). Rows with fewer than 30 subtitle lines are dropped —
`min_subtitle_lines` in the overrides file.

## Listing titles are often episode titles

The catalogue listing gives "Taskmaster - Miguel Vital" or "Pôr do Sol -
Episódio Especial Bloopers". The programme's real name is in
`<meta property="og:title">` on the episode page. One programme came through with
the title "Uma " (RTP's own truncation) and is renamed by hand in the overrides.

## One show, several programme ids

Seasons get separate ids (*Água de Mar* ×3, *Bem-vindos a Beirais* ×3,
*Salto de Fé* ×3, *O Alto* ×2). Without merging you get duplicate-looking rows;
with naive merging you lose the older seasons' links, which matters because the
newest season is often the blocked one. Hence merge-with-"Also:"-links, and
prefer a playable season for the main link.

## Episode counts saturate

The programme page lists a carousel of episodes, around 12–13, so "12+" is as
precise as this method gets. Don't read it as a season length.

## Encoding noise

RTP's meta descriptions occasionally contain mojibake and truncated HTML
entities (`&i`, a stray U+FFFD). The scripts unescape twice, strip trailing
partial entities and drop replacement characters before rendering; otherwise the
JSON embedded in the page carries them through to the browser.

## RTP changes its pages (October 2026)

The first automated rebuild, on 10 October 2026, found three changes since September:

- RTP's menu gained SVG icons. `<path ...>` elements matched the old `<p[^>]*>`
  pattern, so the "longest paragraph" on 200 programme pages became the
  navigation menu. The pattern now insists on `<p` followed by space or `>`.
- The collection heading is now written `Este conte&uacute;do faz parte de`,
  so collection tags silently stopped matching and 49 nature titles fell into
  Portugal documentaries. Both spellings are accepted now.
- `<meta name="keywords">` changed from `RTP1|Ficção, ...` to
  `Title, RTP2, Cultura, date, ...`. The channel is read from either form.

Failures like these are silent: every step "succeeds". `report_changes.py`
now refuses to publish when more than 15 titles share one description or the
list shrinks below 70% of the previous run. When a weekly review issue shows
odd section moves, suspect RTP's markup first.

## Things done by hand that a rebuild should re-check

- the `config/overrides.json` lists above;
- two programmes with no usable programme-level blurb (*Desliga a Televisão*,
  *Dicas.ANACOM*);
- the section labels and blurbs in `templates/page_body.html`, which assert
  things like "mostly European Portuguese" that stay true only if the overrides
  are maintained.

## Environment notes

- Some corporate/agent proxies block `rtp.pt` outright (this project was
  developed through a browser on a personal machine for that reason). If
  `step02` returns nothing but errors, check that plain `curl https://www.rtp.pt/play/`
  works from the same host first.
- Nothing requires a login or defeats a technical protection measure, and
  `robots.txt` was checked: RTP disallows only `/play/pesquisa`, which the
  pipeline never touches. Keep it that way if you change the endpoints used.
- The page reproduces RTP's own synopsis text. That, rather than the fetching,
  is the part with copyright weight — keep attribution visible and keep every
  row linking back to RTP.
