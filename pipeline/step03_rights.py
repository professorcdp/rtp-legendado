#!/usr/bin/env python3
"""Step 3 - ask RTP whether each subtitled title plays from here.

The "SEM DIREITOS DE TRANSMISSÃO ONLINE" screen is produced client-side: the
player calls

    GET /services/rtpplay/?v=5&file=<fileKey>

and gets back JSON like

    {"country":"ES","rights":1,"video":{"streamer":"h2e.rtp.pt","file":"nas2.share/..."},
     "timeout":10800,"live":1,"cachefile":"STATIC"}

`rights: 0` means the poster image is shown instead of the player. The answer
depends on the IP the request comes from, so it describes the machine running
this script - note that in the page you publish.

Side observation: Portugal-only files sit under a `/pt/` path segment in the
fileKey, so `pt_only` is recorded as a second, location-independent signal.

Output: data/rights.json {pid: {rights, country, pt_only, file_key}}
"""
from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from common import WORKERS, fetch, load_json, log, save_json

RIGHTS_URL = "/services/rtpplay/?v=5&file={key}"


def check_one(rec: dict) -> dict:
    pid, key = rec["pid"], rec.get("file_key")
    if not key:
        return {"pid": pid, "rights": None, "error": "no fileKey on page"}
    try:
        raw = fetch(RIGHTS_URL.format(key=quote(key, safe="")), use_cache=False)
    except Exception as e:                        # noqa: BLE001
        return {"pid": pid, "rights": None, "error": str(e)[:120]}
    try:
        obj = json.loads(raw)
        rights, country = obj.get("rights"), obj.get("country")
    except Exception:                             # noqa: BLE001 - occasionally malformed JSON
        m = re.search(r'"rights"\s*:\s*(\d)', raw)
        c = re.search(r'"country"\s*:\s*"(\w+)"', raw)
        rights = int(m.group(1)) if m else None
        country = c.group(1) if c else None
    return {"pid": pid, "rights": rights, "country": country,
            "pt_only": "/pt/" in key, "file_key": key}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    subs = load_json("subtitles.json") or {}
    if not subs:
        raise SystemExit("run step02_subtitles.py first")
    done = {} if args.redo else (load_json("rights.json", {}) or {})

    todo = [v for v in subs.values() if v.get("has_subs") and v["pid"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    log(f"checking rights for {len(todo)} titles")

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for res in ex.map(check_one, todo):
            done[res["pid"]] = res

    save_json("rights.json", done)
    ok = sum(1 for v in done.values() if v.get("rights") == 1)
    log(f"done: {ok}/{len(done)} play from this location "
        f"(country seen: {next((v.get('country') for v in done.values() if v.get('country')), '?')})")


if __name__ == "__main__":
    main()
