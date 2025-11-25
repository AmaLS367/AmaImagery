from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Iterable, List, Pattern

from app.config import settings

# Base paterns
_FALLBACK_PATTERNS: list[str] = [
    r"\bbestiality\b",
    r"\bzoophil(e|ia)\b",
    r"\bgore\b",
    r"\bnecrophil(e|ia)\b",
    r"\bcp\b",
    r"\blolicon\b",
    r"\bcub\b",
    r"\bunder\s*age\b",
    r"\byoung\s*(girl|boy|person)\b",
]

_cache_lock = threading.Lock()
_cache_compiled: list[Pattern] | None = None
_cache_mtime: float | None = None

_cache_forced_lock = threading.Lock()
_cache_forced_compiled: list[Pattern] | None = None
_cache_forced_mtime: float | None = None

def _load_rules_cache(force: bool = False) -> list[Pattern]:
    """
    Load and compile blocklist patterns with caching.
    force=True ignores nsfw_allow flag.
    """
    if not force and getattr(settings, "nsfw_allow", False):
        return []

    path = _rules_path()
    mtime = path.stat().st_mtime if path.exists() else -1.0

    global _cache_compiled, _cache_mtime, _cache_forced_compiled, _cache_forced_mtime
    lock = _cache_forced_lock if force else _cache_lock
    cache_compiled = _cache_forced_compiled if force else _cache_compiled
    cache_mtime = _cache_forced_mtime if force else _cache_mtime

    with lock:
        if cache_compiled is not None and cache_mtime == mtime:
            return cache_compiled

        entries = _read_blocklist_file(path)
        if not entries:
            entries = _FALLBACK_PATTERNS

        compiled = _compile_patterns(entries)

        if force:
            _cache_forced_compiled = compiled
            _cache_forced_mtime = mtime
        else:
            _cache_compiled = compiled
            _cache_mtime = mtime

        return compiled

def _normalize_entries(items: Iterable[str]) -> List[str]:
    out: list[str] = []
    for raw in items:
        s = (raw or "").strip()
        if not s:
            continue
        if s.lower().startswith("re:"):
            s = s[3:].strip()
            if s:
                out.append(s)
            continue
        escaped = re.escape(s)
        escaped = escaped.replace(r"\ ", r"\s+").replace(r"\-", r"[-\s]?")
        out.append(rf"\b{escaped}\b")
    return out


def _read_blocklist_file(p: Path) -> list[str]:
    try:
        if not p.exists() or not p.is_file():
            return []
        text = p.read_text(encoding="utf-8", errors="ignore")
        # JSON array of strings
        if p.suffix.lower() == ".json":
            arr = json.loads(text)
            if isinstance(arr, list):
                return [str(x) for x in arr]
            return []
        # TXT or other: separators are newline or comma
        parts: list[str] = []
        for line in text.splitlines():
            if "," in line:
                parts.extend([s.strip() for s in line.split(",")])
            else:
                parts.append(line.strip())
        return [s for s in parts if s]
    except Exception:
        return []


def _compile_patterns(entries: Iterable[str]) -> list[Pattern]:
    return [re.compile(e, re.IGNORECASE) for e in _normalize_entries(entries)]


def _rules_path() -> Path:
    return Path(settings.nsfw_blocklist_path).expanduser().resolve()


def get_rules() -> list[str]:
    entries = _read_blocklist_file(_rules_path())
    return entries if entries else list(_FALLBACK_PATTERNS)


def _get_compiled() -> list[Pattern]:
    return _load_rules_cache(force=False)



def is_blocked(text: str | None) -> bool:
    if not text:
        return False
    pats = _get_compiled()
    if not pats:
        return False
    return any(rx.search(text) for rx in pats)


def _get_compiled_forced() -> list[Pattern]:
    return _load_rules_cache(force=True)

def is_blocked_forced(text: str | None) -> bool:
    if not text:
        return False
    return any(rx.search(text) for rx in _get_compiled_forced())


def reload_rules() -> None:
    global _cache_compiled, _cache_mtime, _cache_forced_compiled, _cache_forced_mtime
    with _cache_lock:
        _cache_compiled = None
        _cache_mtime = None
    with _cache_forced_lock:
        _cache_forced_compiled = None
        _cache_forced_mtime = None
