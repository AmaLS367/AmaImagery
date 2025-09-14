# app/safety.py
from __future__ import annotations

import json, re, threading
from pathlib import Path
from typing import Iterable, List, Pattern

from app.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth.deps import current_user


router = APIRouter(prefix="/nsfw", tags=["nsfw"])
# Базовые паттерны на случай отсутствия файла (минимум, без излишеств)
# Включится только когда NSFW_ALLOW=false и файл не найден/пуст.
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
        # поддержка 're:' для явных регэкспов
        if s.lower().startswith("re:"):
            s = s[3:].strip()
            if s:
                out.append(s)
            continue
        # по умолчанию — слово/фраза, экранируем и ставим word boundary
        escaped = re.escape(s)
        # допускаем дефисы/пробелы как разделители
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
        # TXT/любое: разделители — новая строка или запятая
        parts = []
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

def _get_compiled() -> list[Pattern]:
    if settings.nsfw_allow:
        return []

    path = Path(settings.nsfw_blocklist_path).expanduser().resolve()
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
    if not pats:  # NSFW_ALLOW=True
        return False
    return any(rx.search(text) for rx in pats)

def _get_compiled_forced() -> list[Pattern]:
    path = Path(settings.nsfw_blocklist_path).expanduser().resolve()
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

class NSFWToggle(BaseModel):
    allow: bool

@router.patch("/users/me/nsfw")
def set_nsfw(toggle: NSFWToggle, db: Session = Depends(get_db), user=Depends(current_user)):
    user.nsfw_allow = bool(toggle.allow)
    db.add(user); db.commit()
    return {"ok": True, "nsfw_allow": user.nsfw_allow}