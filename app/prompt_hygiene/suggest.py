from __future__ import annotations

from .contracts import Suggestion
from .neglist import NegList
from .validators import validate_basic


def build_suggestions(text: str, neglist: NegList) -> list[Suggestion]:
    """
    Aggregate suggestions from validators and neglist hits.
    No mutations are applied here.
    """
    suggestions: list[Suggestion] = []
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
