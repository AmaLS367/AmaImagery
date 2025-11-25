from __future__ import annotations

from typing import List, Tuple

from .contracts import Suggestion
from .neglist import NegList
from .validators import validate_basic


def build_suggestions(text: str, neglist: NegList) -> List[Suggestion]:
    """
    Aggregate suggestions from validators and neglist hits.
    No mutations are applied here.
    """
    suggestions: List[Suggestion] = []
    suggestions += validate_basic(text)

    for token, pos in neglist.hits(text):
        suggestions.append(
            Suggestion(
                code="NEG_TOKEN",
                message=f"Undesirable token: {token}",
                token=token,
                position=pos,
            )
        )
    return suggestions
