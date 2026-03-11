from __future__ import annotations

from .contracts import Correction, HygieneResult, Mode, Report
from .neglist import NegList
from .settings import (
    AUTOCORRECT_EXTRA_WORDS,
    AUTOCORRECT_WHITELIST,
    get_mode,
)
from .spell import SpellChecker, build_spell, correct_prompt
from .spell_negative import correct_negative
from .suggest import build_suggestions


class HygieneFacade:
    """
    Single entry point for prompt hygiene across modes.
    Stateless facade with explicit dependencies passed in at init.
    """

    def __init__(self, neglist: NegList | None = None, spell_checker: SpellChecker | None = None) -> None:
        self.neglist = neglist or NegList()
        self.spell_checker = spell_checker or build_spell(extra_words=list(AUTOCORRECT_EXTRA_WORDS))
        self._whitelist = set(AUTOCORRECT_WHITELIST)

    def run(
        self,
        user_id: str,
        prompt: str,
        negative: str,
        mode: Mode | None = None,
    ) -> HygieneResult:
        """
        Run hygiene according to user mode. If mode is provided, it overrides stored mode.
        Returns corrected texts and a report with corrections and suggestions.
        """
        active_mode = mode or get_mode(user_id)

        if active_mode == Mode.OFF:
            report = Report(suggestions=build_suggestions(prompt, self.neglist), corrections=[])
            return HygieneResult(applied=False, prompt=prompt, negative=negative, report=report)

        if active_mode == Mode.SUGGEST:
            sugg_p = build_suggestions(prompt, self.neglist)
            sugg_n = build_suggestions(negative, self.neglist) if negative else []
            # Merge lists while keeping prompt suggestions first
            suggestions = sugg_p + sugg_n
            return HygieneResult(
                applied=False, prompt=prompt, negative=negative, report=Report(suggestions=suggestions, corrections=[])
            )

        # AUTO
        fixed_p, corr_p = correct_prompt(prompt, self.spell_checker, whitelist=self._whitelist)
        fixed_n, corr_n = correct_negative(negative, self.spell_checker) if negative else (negative, [])
        corrections: list[Correction] = []
        pos_p = 0
        for before, after in corr_p:
            corrections.append(Correction(before=before, after=after, position=None))
            pos_p += 1
        for before, after in corr_n:
            corrections.append(Correction(before=before, after=after, position=None))
        suggestions = build_suggestions(fixed_p, self.neglist)
        if negative:
            suggestions += build_suggestions(fixed_n, self.neglist)
        return HygieneResult(
            applied=True,
            prompt=fixed_p,
            negative=fixed_n,
            report=Report(suggestions=suggestions, corrections=corrections),
        )


# Functional entry point for convenient import
_default_facade = HygieneFacade()


def run_hygiene(
    user_id: str,
    prompt: str,
    negative: str = "",
    mode: Mode | None = None,
) -> HygieneResult:
    return _default_facade.run(user_id=user_id, prompt=prompt, negative=negative, mode=mode)
