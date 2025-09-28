from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Iterable, List, Pattern

from app.config import settings

# Базовые паттерны на случай отсутствия файла (минимум, без излишеств)
# Включается только когда список пуст и/или файл не найден.
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
        # JSON-массив строк
        if p.suffix.lower() == ".json":
            arr = json.loads(text)
            if isinstance(arr, list):
                return [str(x) for x in arr]
            return []
        # TXT/прочее: разделители — новая строка или запятая
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
    """
    Сырые записи из файла правил (или fallback, если файла нет/пуст).
    Без нормализации и компиляции.
    """
    entries = _read_blocklist_file(_rules_path())
    return entries if entries else list(_FALLBACK_PATTERNS)


def _get_compiled() -> list[Pattern]:
    """
    Обычная проверка (учитывает флаг settings.nsfw_allow).
    Если nsfw_allow=True — список пуст, ничего не блокируем.
    """
    if getattr(settings, "nsfw_allow", False):
        return []

    path = _rules_path()
    mtime = path.stat().st_mtime if path.exists() else -1.0

    global _cache_compiled, _cache_mtime
    with _cache_lock:
        if _cache_compiled is not None and _cache_mtime == mtime:
            return _cache_compiled

        entries = _read_blocklist_file(path)
        if not entries:
            entries = _FALLBACK_PATTERNS

        _cache_compiled = _compile_patterns(entries)
        _cache_mtime = mtime
        return _cache_compiled


def is_blocked(text: str | None) -> bool:
    if not text:
        return False
    pats = _get_compiled()
    if not pats:  # nsfw_allow=True → ничего не блокируем
        return False
    return any(rx.search(text) for rx in pats)


def _get_compiled_forced() -> list[Pattern]:
    """
    Принудительная проверка — игнорирует nsfw_allow.
    Используется для административных/системных проверок.
    """
    path = _rules_path()
    mtime = path.stat().st_mtime if path.exists() else -1.0

    global _cache_forced_compiled, _cache_forced_mtime
    with _cache_forced_lock:
        if _cache_forced_compiled is not None and _cache_forced_mtime == mtime:
            return _cache_forced_compiled

        entries = _read_blocklist_file(path)
        if not entries:
            entries = _FALLBACK_PATTERNS

        _cache_forced_compiled = _compile_patterns(entries)
        _cache_forced_mtime = mtime
        return _cache_forced_compiled


def is_blocked_forced(text: str | None) -> bool:
    if not text:
        return False
    return any(rx.search(text) for rx in _get_compiled_forced())


def reload_rules() -> None:
    """
    Сбросить кэш правил. Подхватит изменения файла без рестарта.
    """
    global _cache_compiled, _cache_mtime, _cache_forced_compiled, _cache_forced_mtime
    with _cache_lock:
        _cache_compiled = None
        _cache_mtime = None
    with _cache_forced_lock:
        _cache_forced_compiled = None
        _cache_forced_mtime = None
