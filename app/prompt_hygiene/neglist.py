from __future__ import annotations

import re
import threading
from collections.abc import Iterable

from .settings import DEFAULT_NEG_TOKENS


class NegList:
    """
    Thread safe set of undesirable tokens. Matching is case insensitive
    and token based, not substring inside words.
    """

    def __init__(self, initial: Iterable[str] | None = None) -> None:
        self._lock = threading.RLock()
        self._tokens: set[str] = set(DEFAULT_NEG_TOKENS)
        if initial:
            self._tokens.update(t.strip().lower() for t in initial if t.strip())

    def add(self, token: str) -> None:
        with self._lock:
            self._tokens.add(token.strip().lower())

    def remove(self, token: str) -> None:
        with self._lock:
            self._tokens.discard(token.strip().lower())

    def all(self) -> list[str]:
        with self._lock:
            return sorted(self._tokens)

    def hits(self, text: str) -> list[tuple[str, int]]:
        """
        Return list of (token, position) for tokens present in text.
        Position is character offset of the token start.
        """
        found: list[tuple[str, int]] = []
        if not text:
            return found

        # Word boundaries only
        pattern = re.compile(r"\b([A-Za-z0-9_]+)\b", re.UNICODE)
        lc_tokens = None  # lazy cache

        for m in pattern.finditer(text):
            word = m.group(1)
            if lc_tokens is None:
                with self._lock:
                    lc_tokens = set(self._tokens)
            if word.lower() in lc_tokens:
                found.append((word, m.start()))
        return found
