#!/usr/bin/env python3
"""Compare today's Portugal-only flag with the September 2026 rights check.

For every episode link in snapshot/rights-2026-09-11.json (the check made from
a connection RTP placed in Spain), fetch the page again, look for the subtitle
track and the fileKey, derive pt_only from the `/pt/` path segment, and ask the
rights service what it says from here. Prints how well pt_only predicts the
September "blocked from Spain" answer.

    python check_pt_only.py              # all links
    python check_pt_only.py --limit 50   # quick look

Output: data/pt_only_check.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from common import ROOT, WORKERS, fetch, file_key, log, save_json, subtitle_track
from step03_rights import check_one as rights_check

SNAPSHOT = ROOT / "snapshot" / "rights-2026-09-11.json"


def check(item):
    url, (sept_rights, sept_path) = item[0], item[1][:2]
    out = {"url": url, "sept_rights": sept_rights, "sept_pt": sept_path == "pt"}
    try:
        page = fetch(url, use_cache=False)
    except Exception as e:                        # noqa: BLE001
        return {**out, "error": str(e)[:120]}
    key = file_key(page)
    out["has_subs"] = bool(subtitle_track(page))
    out["pt_only"] = bool(key and "/pt/" in key)
    if key:
        r = rights_check({"pid": url, "file_key": key})
        out["rights_here"], out["country_here"] = r.get("rights"), r.get("country")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    items = list(snap.items())[: args.limit] if args.limit else list(snap.items())
    log(f"re-checking {len(items)} September links, {WORKERS} workers")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        res = list(ex.map(check, items))
    save_json("pt_only_check.json", res)

    ok = [r for r in res if "error" not in r]
    print(f"links re-checked: {len(ok)} of {len(res)} ({len(res) - len(ok)} errors)")
    print(f"subtitle track still present: {sum(r['has_subs'] for r in ok)}")
    print(f"country RTP sees for this machine: {Counter(r.get('country_here') for r in ok).most_common(3)}")
    print(f"plays from here: {sum(1 for r in ok if r.get('rights_here') == 1)}")

    keyed = [r for r in ok if "rights_here" in r]
    same = sum(1 for r in keyed if r["pt_only"] == r["sept_pt"])
    print(f"pt_only unchanged since September: {same} of {len(keyed)}")
    c = Counter((r["pt_only"], r["sept_rights"]) for r in keyed)
    agree = c[(True, 0)] + c[(False, 1)]
    print(f"today's pt_only vs September Spain check: agree {agree} of {len(keyed)} "
          f"({agree / max(len(keyed), 1):.1%})")
    print(f"  pt_only and blocked in Spain:     {c[(True, 0)]}")
    print(f"  not pt_only and played in Spain:  {c[(False, 1)]}")
    print(f"  not pt_only but blocked in Spain: {c[(False, 0)]}")
    print(f"  pt_only but played in Spain:      {c[(True, 1)]}")


if __name__ == "__main__":
    main()
