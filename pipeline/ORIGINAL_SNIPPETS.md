# The original, ad-hoc code — for the record

The September 2026 build was not run from a tidy repo. It was done
interactively: JavaScript executed inside a browser tab on `www.rtp.pt` (so the
fetches were same-origin, with the site's own cookies and no CORS problems),
with Python in a sandbox for the bookkeeping. The scripts in this repo are a
faithful re-implementation of that logic in one place — same endpoints, same
patterns, same rules — not a transcript.

This file preserves the originals, in the order they ran, so you can see exactly
what produced the published data.

## 1. Catalogue sweep (browser console, on www.rtp.pt)

```js
const cats = {"artes":14,"ciencia-e-natureza":11,"cultura":2,"desporto":5,"entretenimento":10,
  "entrevista-opiniao-e-debate":12,"especiais":17,"ficcao":9,"gastronomia":13,"humor":3,
  "infantis-e-juvenis":6,"informacao":1,"institucionais":7,"musica":4,"outros":8,
  "religiosos-e-reflexao":15,"saude":16};
window.CAT = {}; window.CRAWLDONE = 0;
const queue = Object.entries(cats);
async function worker() {
  while (queue.length) {
    const [c, id] = queue.shift();
    for (let p = 1; p < 300; p++) {
      let h;
      try {
        h = await fetch('https://www.rtp.pt/play/bg_l_pg/?' + new URLSearchParams({
          listDate: '', listQuery: '', listProgram: '', listcategory: id,
          listchannel: '', listtype: 'recent', page: p, type: 'tv'
        })).then(r => r.text());
      } catch (e) { break; }
      const arts = h.split('<article').slice(1);
      if (!arts.length) break;
      for (const a of arts) {
        const m = a.match(/<a href="(\/play\/p(\d+)\/[^"]*)" title="Aceder a ([^"]*)"/);
        if (!m) continue;
        const radio = /fa-volume-down/.test(a);
        const meta = (a.match(/<meta content="([^"]*)"/) || [])[1] || '';
        const pid = m[2];
        if (!CAT[pid]) CAT[pid] = { pid, url: m[1], title: m[3], radio, meta, cats: [] };
        if (!CAT[pid].cats.includes(c)) CAT[pid].cats.push(c);
      }
    }
    CRAWLDONE++;
  }
  if (CRAWLDONE == 17) localStorage.setItem('jim_cat', JSON.stringify(CAT));
}
for (let i = 0; i < 6; i++) worker();   // 6 workers; more got throttled
```

## 2. Subtitle check (browser console)

```js
window.RES = JSON.parse(localStorage.getItem('jim_res') || '{}');
window.CHK = { done: 0 };
const q = Object.values(CAT).filter(x => !x.radio && !(x.pid in RES));
async function w() {
  while (q.length) {
    const x = q.shift();
    try {
      const r = await fetch('https://www.rtp.pt' + x.url);
      const h = await r.text();
      const m = h.match(/\n\s*vtt:\s*\[\['[^']*','[^']*','([^']*)'/);
      RES[x.pid] = m ? m[1] : (r.status == 200 ? 0 : r.status);
    } catch (e) { RES[x.pid] = 'ERR'; }
    CHK.done++;
    if (CHK.done % 50 == 0) localStorage.setItem('jim_res', JSON.stringify(RES));
  }
  localStorage.setItem('jim_res', JSON.stringify(RES));
}
for (let i = 0; i < 12; i++) w();
```

(Run in priority order — fiction, humour, entertainment, science, food, arts,
health, culture, kids, then the rest — so the useful sections finished first.)

## 3. Page metadata for the hits (browser console)

```js
window.INFO = {}; const q = [...IQ];   // IQ = pids with a subtitle track
async function w() {
  while (q.length) {
    const k = q.shift();
    const h = await fetch('https://www.rtp.pt' + CAT[k].url).then(r => r.text());
    const d = new DOMParser().parseFromString(h, 'text/html');
    const kw = d.querySelector('meta[name="keywords"]')?.content || '';
    const desc = d.querySelector('meta[name="description"]')?.content || '';
    const col = [...d.querySelectorAll('h2')].map(e => e.textContent.trim())
      .filter(t => t.startsWith('Este conteúdo')).map(t => t.replace('Este conteúdo faz parte de ', ''));
    const eps = new Set([...h.matchAll(new RegExp('/play/p' + k + '/e(\\d+)', 'g'))].map(m => m[1])).size;
    INFO[k] = { t: d.querySelector('meta[property="og:title"]')?.content || '', kw, desc: desc.slice(0, 220), col, eps };
  }
}
for (let i = 0; i < 6; i++) w();
```

## 4. Subtitle-file sound-cue counts (browser console)

```js
const re = /^(?:[-– ]*)(M[ÚU]SICA|RISOS?|RI|RIEM|SUSPIRA|GEME|GEMIDOS?|TOSSE|APLAUSOS|CHORA|GRITA|ARFA|BATE|CAMPAINHA|TELEFONE|PASSOS|RESPIRA|NARRADORA?|VOZ OFF|OFF|CANTA|SILÊNCIO|RUÍDO|BARULHO|ESTRONDO|CÃO|LADRA|PORTA)\b/;
window.CUE = {};
async function w() {
  while (q.length) {
    const k = q.shift();
    const t = await fetch(RES[k]).then(r => r.text());          // RES[k] is the .vtt URL
    const lines = t.split('\n').map(s => s.trim())
      .filter(l => l && !/-->|^\d+$|WEBVTT/.test(l));
    let cues = 0, caps = 0;
    for (const l of lines) {
      if (re.test(l)) cues++;
      if (/^[A-ZÁÉÍÓÚÂÊÔÃÕÇÀ ,:.!?'-]{3,}$/.test(l)) caps++;
    }
    CUE[k] = [lines.length, cues, caps];
  }
}
```

## 5. Rights check (browser console)

```js
window.fk = h => {
  const m = h.match(/fileKey:\s*atob\(\s*decodeURIComponent\((\[[^\]]*\])\.join\(""\)\)\)/);
  if (m) return atob(decodeURIComponent(JSON.parse(m[1]).join('')));
  const n = h.match(/fileKey\s*:\s*["']([^"']+)["']/);
  return n ? n[1] : null;
};
window.RIGHTS = {};
async function w() {
  while (q.length) {
    const k = q.shift();
    const u = CAT[k].url;
    const h = await fetch('https://www.rtp.pt' + u).then(r => r.text());
    const key = fk(h);
    let r = null, c = null;
    if (key) {
      const t = await fetch('/services/rtpplay/?v=5&file=' + encodeURIComponent(key)).then(x => x.text());
      r = (t.match(/"rights"\s*:\s*(\d)/) || [])[1];
      c = (t.match(/"country"\s*:\s*"(\w+)"/) || [])[1];
    }
    RIGHTS[u] = [r === undefined ? null : +r, key ? (/\/pt\//.test(key) ? 'pt' : 'ww') : 'nokey', c];
  }
}
for (let i = 0; i < 6; i++) w();
```

## 6. Show-level synopses (browser console)

```js
window.SYN = {};
async function w() {
  while (q.length) {
    const [idx, pid] = q.shift();
    const h = await fetch('https://www.rtp.pt/play/p' + pid + '/').then(r => r.text());
    const d = new DOMParser().parseFromString(h, 'text/html');
    d.querySelectorAll('script,style').forEach(e => e.remove());
    const meta = (d.querySelector('meta[name="description"]')?.content || '').replace(/\s+/g, ' ').trim();
    const ps = [...d.querySelectorAll('p')].map(e => e.textContent.replace(/\s+/g, ' ').trim())
      .filter(t => t.length > 60
        && !/^(Intérpretes|Autoria|Realiza|Argumento|Elenco|Produção|Ficha)/i.test(t)
        && !/cookies|RTP Play está/i.test(t));
    (SYN[idx] = SYN[idx] || []).push([meta, ps.sort((a, b) => b.length - a.length)[0] || '']);
  }
}
for (let i = 0; i < 5; i++) w();
```

## 7. Dataset build (Python — this is the file the repo's `step05_dataset.py` is derived from)

```python
import json, re, html
h = json.load(open('hits.json')); cue = json.load(open('cue.json'))
MONTHS = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}
def dkey(s):
    m = re.match(r'(\d{2}) (\w{3})\.? (\d{4})', s or '')
    return (int(m.group(3)), MONTHS.get(m.group(2), 0), int(m.group(1))) if m else (0, 0, 0)

FOREIGN_FIC = {15979,15980,15981,16269,16270,16476,16477,16479,16480,16482,16570,16573,16624,
               16625,16711,16712,16905,16906,16907,16926,17001,17008,15870,15416,15502,17049,
               17050,17060,17061,14754,15480,16035,15993}
INTL_DOC = {10193,10836,12990,13562,13927,14135,15066,15137,15174,15177,15193,15462,15638,
            15809,15815,15872,16010,16015,16146,16348,16372,16399,16420,16447,16449,16496,
            16554,16557,16560,16617,16639,16643,16694,16726,16838,16918,16937,16964,16966,
            14482,8670,7391}
NOTES = {16884:'Brazilian novela (Brazilian Portuguese)', 5725:'Brazilian film (Brazilian Portuguese)',
         7017:'Cape Verde setting, much Crioulo', 9769:'Partly in English (set in London)',
         1305:'Daily soap, 300+ episodes', 3019:'Daily sitcom, 300 episodes'}
LANG = {3144,3991,1747,2798,3081,4370,1688,14843,6157,12890}
FIXNAME = {13427: 'Uma Primavera Portuguesa'}
EXCL_T = re.compile(r'Mensagem de Natal|Trailer|^Remo$', re.I)

groups = {}
for k, p in h.items():
    pid = int(k); lines = cue.get(k, [0])[0]
    if lines < 30: continue
    name = html.unescape(html.unescape(p[1])).strip()
    if EXCL_T.search(name): continue
    name = FIXNAME.get(pid, name)
    cats = p[2]; kw = p[5]; cols = p[6]; eps = int(p[7] or 0)
    if pid in FOREIGN_FIC: sec = 'foreign'
    elif pid in LANG: sec = 'lang'
    elif 'infantis' in cats: sec = 'kids'
    elif 'ficcao' in cats and ('Teatro' in cols or 'Teatr' in kw): sec = 'stage'
    elif 'ficcao' in cats:
        film = ('Cinema Português' in cols or 'Filmes Portugueses' in cols or 'Cinema Internacional' in cols) \
               or (eps <= 2 and 'Séries' not in cols and 'Minissérie' not in name)
        sec = 'film' if film else 'series'
    elif pid in INTL_DOC: sec = 'intl'
    elif 'musica' in cats or 'Musicais' in kw or 'Música' in kw or 'Concertos' in cols \
         or 'artes' in cats and 'Musicais' in kw: sec = 'music'
    elif 'Teatro' in cols: sec = 'stage'
    elif 'humor' in cats or 'entretenimento' in cats: sec = 'fun'
    elif 'gastronomia' in cats: sec = 'food'
    elif 'ciencia' in cats or re.search(r'Ciência e Natureza|Ecologia|Ciência, Tecnologia', cols) \
         or re.search(r'Biosfera', name): sec = 'nature'
    elif any(c in cats for c in ['informacao','entrevista','institucionais','saude']) \
         or ('outros' in cats and eps >= 8): sec = 'mag'
    else: sec = 'docs'
    nk = re.sub(r'\s+', ' ', name.lower()).strip()
    key = ('film' if sec == 'film' else 'x', nk)
    PRI = ['foreign','series','lang','fun','food','music','stage','kids','nature','intl','docs','mag']
    g = groups.setdefault(key, {'sec': sec, 'name': name, 'items': []})
    if key[0] == 'x' and PRI.index(sec) < PRI.index(g['sec']): g['sec'] = sec
    g['items'].append({'url': 'https://www.rtp.pt' + p[3], 'date': p[4], 'eps': eps,
                       'channel': kw.split('|')[0] if kw else '',
                       'desc': html.unescape(p[8]).replace('\n', ' ')[:160]})
    if pid in NOTES and NOTES[pid]: g['note'] = NOTES[pid]

out = []
for g in groups.values():
    g['items'].sort(key=lambda i: dkey(i['date']), reverse=True)
    it = g['items'][0]
    out.append({'s': g['sec'], 'n': g['name'], 'u': it['url'], 'd': it['date'],
                'dk': '%04d%02d%02d' % dkey(it['date']),
                'e': max(i['eps'] for i in g['items']), 'c': it['channel'],
                'x': it['desc'], 'note': g.get('note', ''),
                'more': [{'u': i['url'], 'd': i['date']} for i in g['items'][1:]]})

R = json.load(open('rights.json'))
for o in out:
    o['r'] = R.get(o['u'].replace('https://www.rtp.pt', ''), [None])[0]
    for m in o['more']: m['r'] = R.get(m['u'].replace('https://www.rtp.pt', ''), [None])[0]
    if o['r'] != 1:
        for i, m in enumerate(o['more']):
            if m['r'] == 1:
                o['more'][i] = {'u': o['u'], 'd': o['d'], 'r': o['r']}
                o['u'], o['d'], o['r'] = m['u'], m['d'], 1
                break
    o['ok'] = 1 if (o['r'] == 1 or any(m['r'] == 1 for m in o['more'])) else 0
out.sort(key=lambda o: (o['s'], -int(o['dk'])))
json.dump(out, open('data.json', 'w'), ensure_ascii=False)
```

## 8. Translation

Five parallel Claude agents, each given a slice of `[{i, n, x}]` and this
instruction (reproduced from the run):

> Translate European Portuguese TV programme metadata into natural English for
> language learners. … n_en: meaningful English title ("Bem-vindos a Beirais" ->
> "Welcome to Beirais", "Pôr do Sol" -> "Sunset", "Conta-me Como Foi" -> "Tell Me
> How It Was"). Keep proper names. If the title is already English or just a
> name, repeat it unchanged. Well-known English titles of foreign films may be
> used. x_en: faithful natural English translation of x; if x is cut off,
> translate what's there and end with "…"; empty x -> "".

A sixth run did the same for the 72 series synopses, and two more for the other
168 show-level descriptions. `step06_translate.py` carries the same prompt.

## 9. Page assembly

```python
d = open('data.json').read().replace('�', '')
head = open('page_head.html').read()
body = open('page_body.html').read()
open('rtp-legendado.html', 'w').write(head + body.replace('__DATA__', d.replace('</', '<\\/')))
```

Plus a hand-written `<!doctype html>` wrapper with the canonical and social-card
meta tags for the standalone/GitHub Pages copy. `step07_render.py` does all of
this.
