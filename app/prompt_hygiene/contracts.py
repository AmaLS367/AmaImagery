from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Mode(str, Enum):
    OFF = "OFF"
    SUGGEST = "SUGGEST"
    AUTO = "AUTO"


@dataclass(frozen=True)
class Suggestion:
    code: str
    message: str
    token: str | None = None
    position: int | None = None  # character offset in source string


@dataclass(frozen=True)
class Correction:
    before: str
    after: str
    position: int | None = None  # character offset of token start


@dataclass(frozen=True)
class Report:
    suggestions: list[Suggestion] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)


@dataclass(frozen=True)
class HygieneResult:
    applied: bool
    prompt: str
    negative: str
    report: Report
