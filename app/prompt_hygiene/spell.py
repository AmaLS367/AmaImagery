from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Optional, Set, Tuple, List

from .settings import SPELL_SEED_VOCAB 
@dataclass
class SpellChecker:
    vocab: Set[str]
    max_distance: int = 2
    min_len: int = 3

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]*")

def build_spell(extra_words: Optional[List[str]] = None) -> SpellChecker:
    """
    Build a lightweight spell checker without external deps.
    Loads base vocabulary from config/spell_seed_vocab.txt and extends with extra_words.
    """
    seed = set(w.strip().lower() for w in SPELL_SEED_VOCAB if w and w.strip())
    if extra_words:
        seed.update(w.strip().lower() for w in extra_words if w and w.strip())
    return SpellChecker(vocab=seed)

def _best_candidate(token: str, vocab: Set[str]) -> Optional[str]:
    candidates = difflib.get_close_matches(token.lower(), vocab, n=1, cutoff=0.8)
    return candidates[0] if candidates else None

def correct_prompt(
    prompt: str,
    checker: SpellChecker,
    whitelist: Optional[Set[str]] = None,
) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Correct tokens in prompt that look like misspellings.
    Returns corrected prompt and list of (before, after).
    """
    if not prompt:
        return prompt, []

    wl = {t.lower() for t in whitelist or set()}
    parts: List[str] = []
    corrections: List[Tuple[str, str]] = []

    idx = 0
    for m in _WORD_RE.finditer(prompt):
        start, end = m.span()
        token = m.group(0)

        parts.append(prompt[idx:start])  # copy non-word chunk

        if len(token) >= checker.min_len and token.lower() not in wl and token.lower() not in checker.vocab:
            cand = _best_candidate(token, checker.vocab)
            if cand and cand != token.lower():
                parts.append(cand)
                corrections.append((token, cand))
            else:
                parts.append(token)
        else:
            parts.append(token)

        idx = end

    parts.append(prompt[idx:])
    return "".join(parts), corrections
