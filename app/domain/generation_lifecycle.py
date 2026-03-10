from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.files.artifacts import ArtifactService

QUEUED = "queued"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELED = "canceled"

TERMINAL_STATUSES = frozenset({COMPLETED, FAILED, CANCELED})
ACTIVE_STATUSES = frozenset({QUEUED, RUNNING})
PUBLIC_STATUSES = frozenset({QUEUED, RUNNING, COMPLETED, FAILED, CANCELED})


def normalize_generation_status(status: str | None) -> str:
    value = (status or QUEUED).strip().lower()
    if value in PUBLIC_STATUSES:
        return value
    return FAILED


def is_terminal_status(status: str | None) -> bool:
    return normalize_generation_status(status) in TERMINAL_STATUSES


def is_artifact_ready(status: str | None, image_path: str | None) -> bool:
    return normalize_generation_status(status) == COMPLETED and bool(image_path)


def build_artifact_fields(
    *,
    status: str | None,
    image_path: str | None,
    artifacts: ArtifactService,
) -> dict[str, int | str | None]:
    if not is_artifact_ready(status, image_path):
        return {"image_filename": None, "image_url": None, "exp": None, "sig": None}
    return artifacts.build_signed_download(image_path)


def timestamp_or_none(value: datetime | None) -> int | None:
    if value is None:
        return None
    return int(value.timestamp())


def isoformat_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


@dataclass(frozen=True)
class GenerationPublicPayload:
    task_id: str
    status: str
    provider_name: str | None
    provider_job_id: str | None
    provider_state: dict[str, Any]
    image_path: str | None
    image_filename: str | None
    image_url: str | None
    exp: int | None
    sig: str | None
    metadata: dict[str, Any]
    error: str | None
    created_at: int | None
    started_at: int | None
    completed_at: int | None


def build_generation_public_payload(
    generation: Any,
    *,
    artifacts: ArtifactService,
) -> GenerationPublicPayload:
    status = normalize_generation_status(getattr(generation, "status", None))
    download = build_artifact_fields(
        status=status,
        image_path=getattr(generation, "image_path", None),
        artifacts=artifacts,
    )
    image_path = getattr(generation, "image_path", None) if is_artifact_ready(status, getattr(generation, "image_path", None)) else None
    return GenerationPublicPayload(
        task_id=str(getattr(generation, "id")),
        status=status,
        provider_name=getattr(generation, "provider_name", None),
        provider_job_id=getattr(generation, "provider_job_id", None),
        provider_state=dict(getattr(generation, "provider_state", None) or {}),
        image_path=image_path,
        image_filename=download["image_filename"],  # type: ignore[arg-type]
        image_url=download["image_url"],  # type: ignore[arg-type]
        exp=download["exp"],  # type: ignore[arg-type]
        sig=download["sig"],  # type: ignore[arg-type]
        metadata=dict(getattr(generation, "result", None) or {}),
        error=getattr(generation, "error", None),
        created_at=timestamp_or_none(getattr(generation, "created_at", None)),
        started_at=timestamp_or_none(getattr(generation, "started_at", None)),
        completed_at=timestamp_or_none(getattr(generation, "completed_at", None)),
    )
