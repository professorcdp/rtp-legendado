# Fonts

Both fonts are embedded in the page by `step07_render.py` (base64 in the CSS), so the site
makes no requests to Google or anyone else. They are Google Fonts' Latin subsets, as served by
fonts.gstatic.com in October 2026.

- `space-grotesk-latin.woff2`: [Space Grotesk](https://github.com/floriankarsten/space-grotesk)
  by The Space Grotesk Project Authors, variable (weights 300–700); the page uses 400, 500 and
  600 for all UI and body text. Licence: `OFL-SpaceGrotesk.txt`.
- `instrument-serif-latin.woff2`: [Instrument Serif](https://github.com/Instrument/instrument-serif)
  by The Instrument Serif Project Authors, regular (400); used for the page title and the
  section headings only. Licence: `OFL-InstrumentSerif.txt`.

Both are licensed under the SIL Open Font License 1.1. Chosen to match Jim's NúmerosPT project
(docs/decisions/0007-azulejo-palette.md); Inter, used before, was removed.
