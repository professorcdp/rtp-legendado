#!/usr/bin/env python3
"""Step 6 - English translations of every title and description.

The translations in the published page were produced by Claude, in batches, with
the prompt below. This script does the same thing through the Anthropic API so a
scheduled rebuild can translate only what is new.

Translations are cached in data/translations.json, keyed by a hash of the source
text, so a rebuild costs nothing for rows that haven't changed and only pays for
new or re-worded entries.

    export ANTHROPIC_API_KEY=sk-ant-...
    python step06_translate.py                # translate what's missing
    python step06_translate.py --dry-run      # report what would be translated
    python step06_translate.py --no-api       # fill gaps with "" and carry on

The cache is seeded from snapshot/dataset-2026-09-11.json the first time, so
rows whose text hasn't changed since September keep their English even without
an API key. When a row's description has changed but its title hasn't, the
English title is reused and only the description is left for the API.

Output: data/translations.json {hash: {"n":..., "n_en":..., "x_en":...}} and the
translated fields merged into data/dataset.json (fields `ne` and `xe`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

from common import ROOT, load_json, log, save_json

SNAPSHOT = ROOT / "snapshot" / "dataset-2026-09-11.json"

MODEL = os.environ.get("RTP_TRANSLATE_MODEL", "claude-sonnet-5-5")
BATCH = int(os.environ.get("RTP_TRANSLATE_BATCH", "40"))

SYSTEM = """You translate European Portuguese TV programme metadata into natural English for language learners.

For each item you receive {i, n, x}: n is the programme title, x is its description (sometimes cut off mid-sentence, sometimes empty).

Return JSON only: a list of {"i": <same id>, "n_en": "...", "x_en": "..."} with one entry for every input item.

- n_en: a meaningful English title. "Bem-vindos a Beirais" -> "Welcome to Beirais"; "Pôr do Sol" -> "Sunset"; "Conta-me Como Foi" -> "Tell Me How It Was". Keep proper names as they are. If the title is already English or is only a name (e.g. "Taskmaster", "Elvis", "Sara"), repeat it unchanged. For a foreign film with a well-known English title, you may use that title.
- x_en: a faithful, natural English translation of x. If x is cut off, translate what is there and end with "…". If x is empty, return "".
- No commentary, no markdown fences."""


def key_of(n: str, x: str) -> str:
    return hashlib.sha256(f"{n}␟{x}".encode()).hexdigest()[:24]


def seed_from_snapshot(cache: dict) -> int:
    """Add the September translations to the cache (never overwrites)."""
    if not SNAPSHOT.exists():
        return 0
    added = 0
    for r in json.loads(SNAPSHOT.read_text(encoding="utf-8")):
        k = key_of(r["n"], r["x"])
        if k not in cache and r.get("ne"):
            cache[k] = {"n": r["n"], "n_en": r["ne"], "x_en": r.get("xe", "")}
            added += 1
    return added


def translate_batch(client, items):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(items, ensure_ascii=False)}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-api", action="store_true", help="leave untranslated rows empty")
    args = ap.parse_args()

    rows = load_json("dataset.json")
    if not rows:
        raise SystemExit("run step05_dataset.py first")
    cache = load_json("translations.json", {}) or {}
    seeded = seed_from_snapshot(cache)
    if seeded:
        log(f"seeded {seeded} translations from the September snapshot")

    todo = []
    for r in rows:
        k = key_of(r["n"], r["x"])
        if k not in cache:
            todo.append({"i": k, "n": r["n"], "x": r["x"]})
    log(f"{len(rows)} rows, {len(todo)} need translation, {len(cache)} cached")

    if args.dry_run:
        for t in todo[:20]:
            log("  ", t["n"])
        return

    if todo and not args.no_api:
        try:
            import anthropic
        except ImportError:
            raise SystemExit("pip install anthropic, or run with --no-api")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit("set ANTHROPIC_API_KEY, or run with --no-api")
        client = anthropic.Anthropic()
        for start in range(0, len(todo), BATCH):
            chunk = todo[start:start + BATCH]
            try:
                for out in translate_batch(client, chunk):
                    src = next((t["n"] for t in chunk if t["i"] == out["i"]), "")
                    cache[out["i"]] = {"n": src, "n_en": out.get("n_en", ""), "x_en": out.get("x_en", "")}
            except Exception as e:                # noqa: BLE001 - keep going, retry next run
                log(f"  batch {start // BATCH} failed: {e}")
            save_json("translations.json", cache)
            log(f"  translated {min(start + BATCH, len(todo))}/{len(todo)}")

    # English titles by Portuguese title, for rows whose description changed
    title_en = {v["n"]: v["n_en"] for v in cache.values() if v.get("n") and v.get("n_en")}
    for r in rows:
        got = cache.get(key_of(r["n"], r["x"]), {})
        r["ne"] = got.get("n_en", "") or title_en.get(r["n"], "")
        r["xe"] = (got.get("x_en", "") or "").replace("�", "")

    save_json("dataset.json", rows)
    save_json("translations.json", cache)
    missing = sum(1 for r in rows if not r["ne"])
    no_desc = sum(1 for r in rows if r["x"] and not r["xe"])
    log(f"done: {len(rows) - missing} rows with an English title, {missing} without; "
        f"{no_desc} descriptions without English")


if __name__ == "__main__":
    main()
