#!/usr/bin/env python3
"""Step 5c - how many of a programme's recent episodes have captions.

Only each programme's latest episode decides whether it is listed (step 2). Readers
also want to know whether captions cover every episode or only some, so for
each row with more than one episode this step checks up to the RECENT newest
episodes for the same `vtt:` caption track and records `cov: [captioned, checked]`
on the row. Issue #49.

Where the episode list comes from: the latest-episode page only links the
programme's oldest dozen episodes, so the newest ones are read from RTP's
episode feed, /play/bg_l_ep/?listProgram=<pid>&page=N, which lists ~12 episodes
per page, oldest first. The last page is found by probing pages 1, 2, 4, 8, ...
until one is empty, then bisecting, so a 250-episode soap costs ~8 requests.

data/coverage.json (committed by the weekly workflow) remembers, per programme,
the latest episode seen, the newest RECENT episode ids and which of them had
captions. A programme whose latest episode hasn't changed costs nothing; when
it has, only episodes not already confirmed captioned are fetched again.

Runs after step 5 (and 5b) and before step 6. Reads and rewrites data/dataset.json.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

from common import WORKERS, fetch, load_json, log, save_json, subtitle_track

RECENT = 10
FEED = "/play/bg_l_ep/?listDate=&listQuery=&listProgram={pid}&listcategory=&listchannel=&listtype=&page={n}&type=tv"
EP_RE = r'href="(/play/p{pid}/e(\d+)/[^"]*)"'


def ids(url: str):
    m = re.search(r"/play/(?:zigzag/)?p(\d+)/e(\d+)/", url or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def feed_page(pid: str, n: int) -> dict[str, str]:
    """eid -> episode path on feed page n (empty dict past the end)."""
    try:
        h = fetch(FEED.format(pid=pid, n=n), use_cache=False)
    except Exception:                             # noqa: BLE001
        return {}
    return {e: u for u, e in re.findall(EP_RE.format(pid=pid), h)}


def newest_episodes(pid: str) -> dict[str, str]:
    """The RECENT newest episodes of a programme, eid -> path."""
    pages = {1: feed_page(pid, 1)}
    if not pages[1]:
        return {}
    lo, hi = 1, 2                                 # lo has items; find the first empty page hi
    while True:
        pages[hi] = feed_page(pid, hi)
        if not pages[hi]:
            break
        lo, hi = hi, hi * 2
        if hi > 512:
            break
    while hi - lo > 1:                            # bisect for the last non-empty page
        mid = (lo + hi) // 2
        pages[mid] = feed_page(pid, mid)
        lo, hi = (mid, hi) if pages[mid] else (lo, mid)
    found = dict(pages[lo])
    if len(found) < RECENT and lo > 1:            # the newest ten straddle two pages
        found.update(pages.get(lo - 1) or feed_page(pid, lo - 1))
    newest = sorted(found, key=int, reverse=True)[:RECENT]
    return {e: found[e] for e in newest}


def has_captions(path: str) -> bool | None:
    try:
        return bool(subtitle_track(fetch(path, use_cache=False)))
    except Exception:                             # noqa: BLE001 - unknown, try again next run
        return None


def check(job):
    pid, latest, row_u, cached = job
    if cached and cached.get("latest") == latest:
        return pid, cached                         # nothing new since last run
    eps = newest_episodes(pid)
    if not eps:
        return pid, None
    known = (cached or {}).get("cap", {})
    cap = {}
    for eid, path in eps.items():
        if eid == latest:
            cap[eid] = True                        # the row exists because this episode has captions
        elif known.get(eid) is True:
            cap[eid] = True                        # captions don't usually disappear
        else:
            res = has_captions(path)
            if res is not None:
                cap[eid] = res
    return pid, {"latest": latest, "eps": list(eps), "cap": cap}


def main():
    rows = load_json("dataset.json")
    if not rows:
        raise SystemExit("run step05_dataset.py first")
    memory = load_json("coverage.json") or {}
    jobs = []
    for r in rows:
        # Films are single episodes. The stored episode count (`e`) is unreliable (0 for some
        # series), so every other row asks the feed; one-offs simply come back with one episode.
        if r["s"] == "film":
            r.pop("cov", None)
            continue
        pid, eid = ids(r["u"])
        if pid:
            jobs.append((pid, eid, r["u"], memory.get(pid)))
    log(f"coverage: {len(jobs)} titles to check (films skipped), "
        f"{sum(1 for j in jobs if j[3] and j[3].get('latest') == j[1])} unchanged since last run")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = dict(ex.map(check, jobs))

    for r in rows:
        pid, _ = ids(r["u"])
        res = results.get(pid)
        if res and res.get("cap"):
            checked = [e for e in res["eps"] if e in res["cap"]]
            r["cov"] = [sum(1 for e in checked if res["cap"][e]), len(checked)]
        else:
            r.pop("cov", None)
    memory.update({pid: res for pid, res in results.items() if res})
    save_json("coverage.json", memory)
    save_json("dataset.json", rows)
    full = sum(1 for r in rows if r.get("cov") and r["cov"][0] == r["cov"][1])
    part = sum(1 for r in rows if r.get("cov") and r["cov"][0] < r["cov"][1])
    log(f"coverage: {full} titles captioned on every recent episode, {part} on only some")


if __name__ == "__main__":
    main()
