#!/usr/bin/env python3
"""Step 1 - enumerate the RTP Play catalogue.

RTP Play's category pages load their listings by AJAX from an internal endpoint:

    GET /play/bg_l_pg/?listDate=&listQuery=&listProgram=&listcategory=<id>
        &listchannel=&listtype=recent&page=<n>&type=tv

It returns an HTML fragment of <article> blocks, 12 per page, until a page comes
back empty. Each block carries the programme's latest episode link, its title,
an icon (play triangle for TV, speaker for radio) and a meta line with the
episode number and date.

Output: data/catalogue.json  {pid: {pid,url,title,radio,meta,cats:[...]}}
"""
from __future__ import annotations

import argparse
import re
from concurrent.futures import ThreadPoolExecutor

from common import WORKERS, fetch, save_json, load_json, log

# Category ids are stable; they come from `currentHPListCategory` on each
# /play/programas/<slug>/canal page. Verify with --refresh-categories.
CATEGORIES = {
    "informacao": 1, "cultura": 2, "humor": 3, "musica": 4, "desporto": 5,
    "infantis-e-juvenis": 6, "institucionais": 7, "outros": 8, "ficcao": 9,
    "entretenimento": 10, "ciencia-e-natureza": 11, "entrevista-opiniao-e-debate": 12,
    "gastronomia": 13, "artes": 14, "religiosos-e-reflexao": 15, "saude": 16,
    "especiais": 17,
}

ITEM_RE = re.compile(r'<a href="(/play/p(\d+)/[^"]*)" title="Aceder a ([^"]*)"')
META_RE = re.compile(r'<meta content="([^"]*)"')
LIST_URL = ("/play/bg_l_pg/?listDate=&listQuery=&listProgram=&listcategory={cat}"
            "&listchannel=&listtype=recent&page={page}&type=tv")


def refresh_categories():
    out = {}
    for slug in CATEGORIES:
        html_text = fetch(f"/play/programas/{slug}/canal")
        m = re.search(r"currentHPListCategory\s*=\s*['\"]?(\d+)", html_text)
        out[slug] = int(m.group(1)) if m else None
    return out


def crawl_category(slug: str, cat_id: int, max_pages: int = 300):
    found = []
    for page in range(1, max_pages + 1):
        html_text = fetch(LIST_URL.format(cat=cat_id, page=page), use_cache=False)
        articles = html_text.split("<article")[1:]
        if not articles:
            break
        for a in articles:
            m = ITEM_RE.search(a)
            if not m:
                continue
            meta = META_RE.search(a)
            found.append({
                "pid": m.group(2),
                "url": m.group(1),                       # latest episode URL
                "title": m.group(3),                     # programme (or episode) title
                "radio": "fa-volume-down" in a,          # radio programmes carry a speaker icon
                "meta": meta.group(1) if meta else "",   # "Title Ep. 8 11 set. 2026"
                "cat": slug,
            })
    log(f"  {slug}: {len(found)} items")
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-categories", action="store_true",
                    help="re-read the category ids from RTP before crawling")
    ap.add_argument("--only", help="comma-separated category slugs (default: all)")
    args = ap.parse_args()

    cats = dict(CATEGORIES)
    if args.refresh_categories:
        fresh = refresh_categories()
        log("category ids:", fresh)
        cats.update({k: v for k, v in fresh.items() if v})
    if args.only:
        cats = {k: v for k, v in cats.items() if k in args.only.split(",")}

    catalogue: dict[str, dict] = load_json("catalogue.json", {}) or {}
    with ThreadPoolExecutor(max_workers=min(len(cats), WORKERS)) as ex:
        results = list(ex.map(lambda kv: crawl_category(*kv), cats.items()))

    for items in results:
        for it in items:
            rec = catalogue.setdefault(it["pid"], {
                "pid": it["pid"], "url": it["url"], "title": it["title"],
                "radio": it["radio"], "meta": it["meta"], "cats": [],
            })
            # keep the newest listing we saw for this programme
            rec.update({"url": it["url"], "title": it["title"],
                        "radio": it["radio"], "meta": it["meta"]})
            if it["cat"] not in rec["cats"]:
                rec["cats"].append(it["cat"])

    tv = [r for r in catalogue.values() if not r["radio"]]
    log(f"catalogue: {len(catalogue)} programmes, {len(tv)} TV")
    save_json("catalogue.json", catalogue)


if __name__ == "__main__":
    main()
