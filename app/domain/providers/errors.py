from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderOperationError(RuntimeError):
    provider_name: str
    stage: str
    message: str
    error_code: str
    provider_job_id: str | None = None
    provider_state: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False
    terminal: bool = True

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.message)

    def as_persistable_state(self) -> dict[str, Any]:
        state = dict(self.provider_state)
        state.setdefault("failure_stage", self.stage)
        state.setdefault("failure_code", self.error_code)
        state.setdefault("retryable", self.retryable)
        return state
