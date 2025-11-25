from __future__ import annotations

import threading
from pathlib import Path
from typing import Dict, Iterable, List, Set

from .contracts import Mode

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def _read_txt(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip() and not line.startswith("#")}

def load_autocorrect_extra() -> Set[str]:
    return _read_txt(_CONFIG_DIR / "autocorrect_extra_words.txt")

def load_autocorrect_whitelist() -> Set[str]:
    return _read_txt(_CONFIG_DIR / "autocorrect_whitelist.txt")

def load_negative_whitelist_extra() -> Set[str]:
    return _read_txt(_CONFIG_DIR / "negative_whitelist_extra.txt")

def load_default_neg_tokens() -> Set[str]:
    return _read_txt(_CONFIG_DIR / "neg_tokens.txt")

def load_spell_seed_vocab() -> Set[str]:
    return _read_txt(_CONFIG_DIR / "spell_seed_vocab.txt")

# Caches
AUTOCORRECT_EXTRA_WORDS: Set[str] = load_autocorrect_extra()
AUTOCORRECT_WHITELIST: Set[str] = load_autocorrect_whitelist()
NEGATIVE_WHITELIST_EXTRA: Set[str] = load_negative_whitelist_extra()
DEFAULT_NEG_TOKENS: Set[str] = load_default_neg_tokens()
SPELL_SEED_VOCAB: Set[str] = load_spell_seed_vocab()

class _ModeStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._modes: Dict[str, Mode] = {}

    def get(self, user_id: str, default: Mode = Mode.SUGGEST) -> Mode:
        with self._lock:
            return self._modes.get(user_id, default)

    def set(self, user_id: str, mode: Mode) -> None:
        with self._lock:
            self._modes[user_id] = mode

    def bulk_set(self, items: Iterable[tuple[str, Mode]]) -> None:
        with self._lock:
            for k, v in items:
                self._modes[k] = v

_MODE_STORE = _ModeStore()

def get_mode(user_id: str) -> Mode:
    return _MODE_STORE.get(user_id)

def set_mode(user_id: str, mode: Mode) -> None:
    _MODE_STORE.set(user_id, mode)
