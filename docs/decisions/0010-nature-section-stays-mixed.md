# 10. Nature & science stays mixed; only fiction and Portuguese documentaries must be Portuguese-made

**Date:** 2026-11-02
**Status:** accepted

## Context
The first AI classification run (#58) flagged 19 titles as foreign productions. 18 were
acquired nature documentaries in "Nature & science" (A Floresta, Gronelândia sob Pressão,
Terra de Lendas…). The section's blurb already says it mixes Portuguese-made and acquired
documentaries: they carry Portuguese narration or captions and are useful to learners, just
not as examples of Portuguese production. The 19th, Ministério do Tempo (13094), looked like
the Spanish series El Ministerio del Tiempo but is RTP's 2017 Portuguese remake (Iniziomedia,
Portuguese cast, tagged "Séries Nacionais").

## Decision
- **Nature & science stays a mix** of Portuguese-made and acquired documentaries. It is not
  checked for foreign productions, by people or by the classifier.
- Only **Portuguese TV series, Portuguese films and Documentaries (Portugal)** must be
  Portuguese-made (Brazilian and other Lusophone titles stay, with a page note).
- `confirmed_portuguese` in `pipeline/config/overrides.json` lists titles confirmed Portuguese
  after a doubt, with the evidence. The classifier never asks about or flags them.
- The classifier (step05d_classify.py) also reads the credits on RTP's programme page
  (Produção, Realização, Intérpretes, Título Original, RTP labels) as evidence.
- Its suggestion appears next to each new title in the weekly review issue. It is never
  applied automatically; a person decides.

## Alternatives considered
- **Move acquired nature documentaries to International documentaries.** Cleaner labels, but
  it would empty much of Nature & science and split similar programs by who made them, which
  matters less to learners than the subject.
- **Apply confident "foreign" suggestions automatically.** Faster, but a wrong call (like
  Ministério do Tempo would have been) silently moves a Portuguese title.

## Consequences
- Fewer false alarms in the weekly review.
- The confirmed list needs a line each time a doubtful title is settled as Portuguese.
