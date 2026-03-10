from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.users.router import my_generations
from app.application.use_cases.get_generation_status import (
    GetGenerationStatusCommand,
    GetGenerationStatusUseCase,
)
from app.files.artifacts import ArtifactService


class _FakeUoW:
    def __init__(self, generation):
        self.generations = AsyncMock()
        self.generations.get = AsyncMock(return_value=generation)
        self.generations.count_by_user = AsyncMock(return_value=1)
        self.generations.list_by_user = AsyncMock(return_value=[generation])

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


def _generation():
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id="gen-1",
        user_id="user-1",
        status="completed",
        provider_name="comfyui",
        provider_job_id="prompt-1",
        provider_state={"wait_strategy": "polling"},
        result={"seed": 7},
        error=None,
        image_path="C:/outputs/gen-1.png",
        prompt={"prompt": "hello"},
        params={"width": 512, "height": 512},
        created_at=now,
        started_at=now,
        completed_at=now,
    )


@pytest.mark.asyncio
async def test_status_and_history_share_lifecycle_semantics():
    generation = _generation()
    artifacts = ArtifactService(outputs_dir=Path("C:/outputs"))
    status_use_case = GetGenerationStatusUseCase(uow=_FakeUoW(generation), artifacts=artifacts)

    status_result = await status_use_case(GetGenerationStatusCommand(task_id="gen-1"))
    assert status_result.success

    with patch("app.api.v1.users.router.get_uow", return_value=_FakeUoW(generation)):
        with patch("app.api.v1.users.router.get_artifact_service", return_value=artifacts):
            history_result = await my_generations(user=SimpleNamespace(id="user-1"), limit=20, offset=0)

    item = history_result.items[0]
    assert item.task_id == status_result.data.task_id
    assert item.status == status_result.data.status
    assert item.provider_name == status_result.data.provider_name
    assert item.provider_state == status_result.data.provider_state
    assert item.metadata == status_result.data.metadata
    assert item.image_url == status_result.data.image_url


def test_artifact_service_detects_canonical_path(tmp_path):
    artifacts = ArtifactService(outputs_dir=tmp_path)
    canonical_path = artifacts.canonical_path("gen-1", default_ext="png")
    canonical_path.write_bytes(b"png")

    assert artifacts.is_canonical_path("gen-1", canonical_path)
    assert artifacts.persist_local("gen-1", canonical_path) == str(canonical_path)
