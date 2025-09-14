import re
from symspellpy import SymSpell, Verbosity # type: ignore
from wordfreq import top_n_list # type: ignore
from app.logging_setup import lg


_TOKEN = re.compile(r"[A-Za-z][A-Za-z\-']{2,}")  # слова ≥3 символов

def build_spell(extra_words: list[str] | None = None) -> SymSpell:
    sym = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    try:
        vocab = top_n_list("en", 60000, wordlist="best")
    except TypeError:
        vocab = top_n_list("en", 60000) 
    for w in vocab:
        sym.create_dictionary_entry(w, 1)
    for w in (extra_words or []):
        sym.create_dictionary_entry(w.lower(), 1)
    return sym

def correct_prompt(text: str, sym: SymSpell, whitelist: set[str] | None = None):
    wl = {w.lower() for w in (whitelist or [])}
    changes: list[tuple[str, str]] = []

    def _fix(m: re.Match):
        w = m.group(0)
        lw = w.lower()
        if lw in wl or any(ch.isdigit() for ch in lw):
            return w
        cand = sym.lookup(lw, Verbosity.CLOSEST, max_edit_distance=2, include_unknown=True)[0].term
        if cand != lw:
            changes.append((w, cand))
            return cand.capitalize() if w[0].isupper() else cand
        return w

    out = _TOKEN.sub(_fix, text)
    lg("prompt").bind(corrections=changes).debug("prompt.corrected")
    return out, changes
