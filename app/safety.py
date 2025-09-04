import re

_BLOCK = []
_compiled = [re.compile(p, re.I) for p in _BLOCK]

def is_blocked(text: str | None) -> bool:
    if not text:
        return False
    return any(rx.search(text) for rx in _compiled)
