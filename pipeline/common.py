"""Shared helpers: polite HTTP session, on-disk cache, resumable JSON state.

Everything in the pipeline goes through fetch() so that throttling, retries and
caching are handled in one place. RTP's servers slow down sharply under
concurrency (see GOTCHAS.md), so keep WORKERS low.
"""
from __future__ import annotations

import base64
import json
import hashlib
import os
import random
import re
import sys
import threading
import time
import urllib.parse
from pathlib import Path

import requests

BASE = "https://www.rtp.pt"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CACHE = DATA / "cache"
DATA.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

# Tunables (environment variables override)
WORKERS = int(os.environ.get("RTP_WORKERS", "5"))
DELAY = float(os.environ.get("RTP_DELAY", "0.15"))        # polite pause per request, seconds
TIMEOUT = float(os.environ.get("RTP_TIMEOUT", "45"))
RETRIES = int(os.environ.get("RTP_RETRIES", "3"))
CACHE_TTL = float(os.environ.get("RTP_CACHE_TTL", "86400"))  # seconds; 0 disables reads
USER_AGENT = os.environ.get(
    "RTP_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 rtp-legendado/1.0 (+https://github.com/professorcdp/rtp-legendado)",
)

_session_local = threading.local()
_throttle_lock = threading.Lock()
_last_request = [0.0]


def session() -> requests.Session:
    s = getattr(_session_local, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.6",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Referer": BASE + "/play/",
        })
        _session_local.s = s
    return s


def _cache_path(url: str) -> Path:
    return CACHE / (hashlib.sha256(url.encode()).hexdigest()[:40] + ".bin")


def fetch(url: str, *, binary: bool = False, use_cache: bool = True):
    """GET a URL with retries, polite throttling and an on-disk cache.

    Returns text (str) or bytes. Raises requests.HTTPError after RETRIES failures.
    """
    if not url.startswith("http"):
        url = BASE + url
    cp = _cache_path(url)
    if use_cache and CACHE_TTL and cp.exists() and (time.time() - cp.stat().st_mtime) < CACHE_TTL:
        raw = cp.read_bytes()
        return raw if binary else raw.decode("utf-8", "replace")

    last_err = None
    for attempt in range(RETRIES):
        with _throttle_lock:                     # global spacing between requests
            gap = time.time() - _last_request[0]
            if gap < DELAY:
                time.sleep(DELAY - gap)
            _last_request[0] = time.time()
        try:
            r = session().get(url, timeout=TIMEOUT)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code} for {url}", response=r)
            r.raise_for_status()
            raw = r.content
            if use_cache:
                cp.write_bytes(raw)
            return raw if binary else raw.decode("utf-8", "replace")
        except Exception as e:                   # noqa: BLE001 - retry everything transient
            last_err = e
            time.sleep((2 ** attempt) + random.random())
    raise last_err


def load_json(name, default=None):
    p = DATA / name
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default


def save_json(name, obj):
    p = DATA / name
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=0), encoding="utf-8")
    tmp.replace(p)
    return p


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- RTP specifics

# The player config on an episode page carries the subtitle track like this:
#   vtt: [['PT','Português adaptado','https://cdn-ondemand.rtp.pt/.../x.vtt']],
# A commented-out example block elsewhere in the page also contains the string
# "vtt", which is why the pattern insists on the full `vtt: [[ '..','..','..' ]]`
# shape rather than just looking for "vtt".
VTT_RE = re.compile(r"\n\s*vtt:\s*\[\['[^']*','([^']*)','([^']*)'")

# fileKey is obfuscated as atob(decodeURIComponent(["chunk","chunk"].join("")))
FILEKEY_OBF_RE = re.compile(r'fileKey:\s*atob\(\s*decodeURIComponent\(\s*(\[[^\]]*\])\.join\(""\)\s*\)\s*\)')
FILEKEY_PLAIN_RE = re.compile(r'fileKey\s*:\s*["\']([^"\']+)["\']')


def subtitle_track(html_text: str):
    """Return (label, url) of the Portuguese subtitle track, or None."""
    m = VTT_RE.search(html_text)
    return (m.group(1), m.group(2)) if m else None


def file_key(html_text: str):
    """Return the player's fileKey (the path RTP's rights service asks about)."""
    m = FILEKEY_OBF_RE.search(html_text)
    if m:
        try:
            parts = json.loads(m.group(1))
            return base64.b64decode(urllib.parse.unquote("".join(parts))).decode("utf-8", "replace")
        except Exception:                        # noqa: BLE001
            return None
    m = FILEKEY_PLAIN_RE.search(html_text)
    return m.group(1) if m else None


MONTHS = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
          "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}


def date_key(s: str):
    """'10 set. 2026' -> (2026, 9, 10); unparseable -> (0, 0, 0)."""
    m = re.match(r"(\d{2}) (\w{3})\.? (\d{4})", s or "")
    return (int(m.group(3)), MONTHS.get(m.group(2), 0), int(m.group(1))) if m else (0, 0, 0)
