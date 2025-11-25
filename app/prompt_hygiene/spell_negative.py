from __future__ import annotations

from typing import List, Set, Tuple

from .settings import AUTOCORRECT_WHITELIST, NEGATIVE_WHITELIST_EXTRA
from .spell import SpellChecker, correct_prompt


def correct_negative(
    negative: str,
    checker: SpellChecker,
) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Apply softer corrections for negative prompt.
    Uses base whitelist extended with negative specific tokens.
    """
    wl: Set[str] = set(AUTOCORRECT_WHITELIST) | set(NEGATIVE_WHITELIST_EXTRA)
    return correct_prompt(negative, checker, whitelist=wl)
