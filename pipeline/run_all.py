#!/usr/bin/env python3
"""Run the whole pipeline in order. `python run_all.py --help` for options.

    step 1  catalogue        enumerate every TV programme
    step 2  subtitles        check each one's latest episode for a vtt track
    step 3  rights           ask RTP's rights service about each subtitled title
    step 5a dataset --draft  decide sections (tells step 4 what to fetch)
    step 4  synopses         show-level descriptions for series/recurring strands
    step 5b dataset          merge seasons, fold in rights + synopses
    step 6  translate        English titles and descriptions (cached)
    step 7  render           index.html + csv

Every step is resumable and caches its HTTP calls, so re-running after a failure
is cheap. A full cold run takes about 30 minutes of mostly-waiting on GitHub
Actions at the default politeness settings (about 2 hours from a home
connection in September 2026).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ("catalogue", [sys.executable, "step01_catalogue.py"]),
    ("subtitles", [sys.executable, "step02_subtitles.py"]),
    ("rights", [sys.executable, "step03_rights.py"]),
    ("sections (draft)", [sys.executable, "step05_dataset.py", "--draft-only"]),
    ("synopses", [sys.executable, "step04_synopses.py"]),
    ("dataset", [sys.executable, "step05_dataset.py"]),
    ("translate", [sys.executable, "step06_translate.py"]),
    ("render", [sys.executable, "step07_render.py"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default="", help="start at this step name")
    ap.add_argument("--no-translate", action="store_true", help="skip the API translation step")
    args = ap.parse_args()

    started = not args.start
    for name, cmd in STEPS:
        if not started:
            started = name.startswith(args.start)
            if not started:
                continue
        if args.no_translate and name == "translate":
            cmd = cmd + ["--no-api"]
        print(f"\n=== {name} ===", flush=True)
        t0 = time.time()
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode:
            raise SystemExit(f"step '{name}' failed with exit code {r.returncode}")
        print(f"=== {name} done in {time.time() - t0:.0f}s ===", flush=True)


if __name__ == "__main__":
    main()
