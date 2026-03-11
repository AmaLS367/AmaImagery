from __future__ import annotations

import re

from .contracts import Suggestion


def _add(s: list[Suggestion], code: str, msg: str, token: str | None = None, pos: int | None = None) -> None:
    s.append(Suggestion(code=code, message=msg, token=token, position=pos))


WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]*")
REPEAT_PUNCT_RE = re.compile(r"([,.;:!?])\1{1,}")
WHITESPACE_RE = re.compile(r"\s{2,}")


def validate_length(text: str, max_len: int = 2000) -> list[Suggestion]:
    out: list[Suggestion] = []
    if len(text) > max_len:
        _add(out, "LENGTH", f"Text length {len(text)} exceeds {max_len}.")
    return out


def validate_repeat_words(text: str, threshold: int = 5) -> list[Suggestion]:
    out: list[Suggestion] = []
    if not text:
        return out
    counts: dict[str, int] = {}
    for m in WORD_RE.finditer(text.lower()):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    for w, c in counts.items():
        if c >= threshold and len(w) > 2:
            _add(out, "REPEAT_WORDS", f"Word repeats {c} times: {w}", token=w)
    return out


def validate_punctuation(text: str) -> list[Suggestion]:
    out: list[Suggestion] = []
    for m in REPEAT_PUNCT_RE.finditer(text):
        _add(out, "PUNCT", "Repeated punctuation.", token=m.group(1), pos=m.start())
    if WHITESPACE_RE.search(text):
        _add(out, "WHITESPACE", "Excessive whitespace.")
    return out


def validate_basic(text: str) -> list[Suggestion]:
    out: list[Suggestion] = []
    out += validate_length(text)
    out += validate_repeat_words(text)
    out += validate_punctuation(text)
    return out
