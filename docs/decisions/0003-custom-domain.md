# 3. Serve the site at legendado.professorcdp.com

**Date:** 2026-10-17
**Status:** accepted; switched over on 2026-10-18

## Context
The site lives at https://professorcdp.github.io/rtp-legendado/, with the original
https://jamminalley.github.io/rtp-legendado/ forwarding to it. Jim owns professorcdp.com (DNS
at Google) and wants the list at a short address of his own that matches his Substack:
**legendado.professorcdp.com**.

Once a custom domain is set in a GitHub Pages site's settings, GitHub immediately redirects the
github.io address to the custom domain. If the domain's DNS record doesn't exist yet, the site
is unreachable until it does. The same goes for anything that links to the new address
before it resolves (the forwarding repo, the page's canonical and social-card tags).

## Decision
- Use **legendado.professorcdp.com**, with a DNS record at Google:
  type **CNAME**, host **legendado**, value **professorcdp.github.io**.
- The site's address is one setting: `SITE_URL` at the top of `.github/workflows/site.yml`
  (read by `step07_render.py`). It stays at the github.io address until the domain works.
  When it's a custom domain, step 7 also writes a `CNAME` file next to the page.
- Switch-over, in this order, so the site is never offline:
  1. Jim adds the DNS record.
  2. Check it resolves: `dig +short legendado.professorcdp.com` shows `professorcdp.github.io.`
  3. Set the custom domain on the Pages site
     (`gh api -X PUT repos/professorcdp/rtp-legendado/pages -f cname=legendado.professorcdp.com`),
     and wait for GitHub's DNS check to pass.
  4. Change `SITE_URL` to `https://legendado.professorcdp.com`, update README.md and
     PROJECT.md, and run the workflow (mode "publish").
  5. Once GitHub has issued the certificate, turn on "Enforce HTTPS"
     (`gh api -X PUT repos/professorcdp/rtp-legendado/pages -F https_enforced=true`).
  6. Point the jamminalley/rtp-legendado forwarding site (index.html, 404.html, README)
     straight at https://legendado.professorcdp.com/, keeping path, query and #anchor.
  7. Check the old addresses: professorcdp.github.io/rtp-legendado and
     jamminalley.github.io/rtp-legendado should both land on the new one.

## Alternatives considered
- **Set the domain in GitHub first, then add DNS** (GitHub's general advice, to stop anyone
  else claiming the subdomain). It would take the site offline from the moment the domain is
  set until DNS works. With the record added first and the domain set straight after, the
  window in which someone could claim the subdomain is minutes. Verifying professorcdp.com
  for the organization (a TXT record) would close it completely; worth doing if more
  subdomains follow.
- **Keep the github.io address.** Works, but it's long and doesn't carry Jim's brand.

## Consequences
- Old links keep working: professorcdp.github.io/rtp-legendado redirects to the new domain
  (GitHub does this), and the jamminalley forwarding site goes straight there.
- The first deploy after the switch must have `SITE_URL` changed, or the page's canonical
  and social-card links keep pointing at the github.io address (harmless, but untidy).
- GitHub ignores a CNAME file when Pages deploys from Actions; the domain lives in the Pages
  settings. The CNAME file is written anyway, as a record of the intended domain.
