from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.domain.providers.errors import ProviderOperationError
from app.domain.providers.interfaces import ProviderResult, ProviderSubmission
from app.workers.generation_worker import run_worker


def _generation(status: str = "queued") -> SimpleNamespace:
    return SimpleNamespace(
        id="gen-1",
        user_id=None,
        prompt={"prompt": "test prompt", "negative_prompt": ""},
        params={"width": 512, "height": 512, "steps": 10, "guidance_scale": 7.5},
        status=status,
    )


class DiffusersProviderFake:
    provider_name = "diffusers"

    def __init__(self) -> None:
        self.submit = AsyncMock(
            return_value=ProviderSubmission(
                provider_name="diffusers",
                provider_job_id="gen-1",
                provider_state={"request": {"prompt": "test prompt"}},
            )
        )
        self.wait_for_result = AsyncMock(
            return_value=ProviderResult(
                provider_name="diffusers",
                image_path="C:/tmp/gen-1.png",
                provider_job_id="gen-1",
                provider_state={"local": True},
                metadata={"width": 512},
                artifact_persisted=True,
            )
        )


class ComfyuiProviderFake:
    provider_name = "comfyui"

    def __init__(self) -> None:
        self.submit = AsyncMock(
            return_value=ProviderSubmission(
                provider_name="comfyui",
                provider_job_id="prompt-1",
                provider_state={"prompt_id": "prompt-1"},
            )
        )
        self.wait_for_result = AsyncMock(side_effect=RuntimeError("history malformed"))


@pytest.mark.asyncio
async def test_worker_transitions_generation_to_completed():
    queue = AsyncMock()
    queue.dequeue = AsyncMock(side_effect=["gen-1", KeyboardInterrupt()])

    provider = DiffusersProviderFake()
    provider_registry = Mock()
    provider_registry.get_default = Mock(return_value=provider)

    update_generation = AsyncMock()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()

    with (
        patch("app.workers.generation_worker.get_task_queue", return_value=queue),
        patch("app.workers.generation_worker.get_provider_registry", return_value=provider_registry),
        patch("app.workers.generation_worker._load_generation", AsyncMock(side_effect=[_generation(), _generation()])),
        patch("app.workers.generation_worker._update_generation", update_generation),
        patch("app.workers.generation_worker._persist_artifact", AsyncMock(return_value="C:/tmp/gen-1.png")),
        patch("app.workers.generation_worker.get_event_bus", Mock(return_value=event_bus)),
    ):
        await run_worker()

    running_call = update_generation.await_args_list[0]
    assert running_call.args[0] == "gen-1"
    assert running_call.kwargs["status"] == "running"
    assert running_call.kwargs["provider_name"] == "diffusers"
    assert running_call.kwargs["started_at"] is not None

    completed_call = update_generation.await_args_list[-1]
    assert completed_call.args[0] == "gen-1"
    assert completed_call.kwargs["status"] == "completed"
    assert completed_call.kwargs["provider_job_id"] == "gen-1"
    assert completed_call.kwargs["completed_at"] is not None
    assert completed_call.kwargs["image_path"] == "C:/tmp/gen-1.png"
    assert completed_call.kwargs["result"] == {"width": 512}


@pytest.mark.asyncio
async def test_worker_transitions_generation_to_failed():
    queue = AsyncMock()
    queue.dequeue = AsyncMock(side_effect=["gen-1", KeyboardInterrupt()])

    provider = ComfyuiProviderFake()
    provider_registry = Mock()
    provider_registry.get_default = Mock(return_value=provider)

    update_generation = AsyncMock()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()

    with (
        patch("app.workers.generation_worker.get_task_queue", return_value=queue),
        patch("app.workers.generation_worker.get_provider_registry", return_value=provider_registry),
        patch("app.workers.generation_worker._load_generation", AsyncMock(side_effect=[_generation(), _generation()])),
        patch("app.workers.generation_worker._update_generation", update_generation),
        patch("app.workers.generation_worker.get_event_bus", Mock(return_value=event_bus)),
    ):
        await run_worker()

    failed_call = update_generation.await_args_list[-1]
    assert failed_call.args[0] == "gen-1"
    assert failed_call.kwargs["status"] == "failed"
    assert failed_call.kwargs["provider_name"] == "comfyui"
    assert failed_call.kwargs["completed_at"] is not None
    assert "history malformed" in failed_call.kwargs["error"]


@pytest.mark.asyncio
async def test_worker_skips_terminal_generation():
    queue = AsyncMock()
    queue.dequeue = AsyncMock(side_effect=["gen-1", KeyboardInterrupt()])
    provider_registry = Mock()
    provider_registry.get_default = Mock()

    with (
        patch("app.workers.generation_worker.get_task_queue", return_value=queue),
        patch("app.workers.generation_worker.get_provider_registry", return_value=provider_registry),
        patch("app.workers.generation_worker._load_generation", AsyncMock(return_value=_generation(status="completed"))),
        patch("app.workers.generation_worker._update_generation", AsyncMock()) as update_generation,
    ):
        await run_worker()

    update_generation.assert_not_awaited()
    provider_registry.get_default.assert_not_called()


@pytest.mark.asyncio
async def test_worker_persists_provider_failure_metadata():
    queue = AsyncMock()
    queue.dequeue = AsyncMock(side_effect=["gen-1", KeyboardInterrupt()])

    provider = ComfyuiProviderFake()
    provider.wait_for_result = AsyncMock(
        side_effect=ProviderOperationError(
            provider_name="comfyui",
            stage="wait",
            message="ComfyUI prompt prompt-1 did not finish in time",
            error_code="execution_timeout",
            provider_job_id="prompt-1",
            provider_state={"prompt_id": "prompt-1", "wait_strategy": "polling"},
        )
    )
    provider_registry = Mock()
    provider_registry.get_default = Mock(return_value=provider)

    update_generation = AsyncMock()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()

    with (
        patch("app.workers.generation_worker.get_task_queue", return_value=queue),
        patch("app.workers.generation_worker.get_provider_registry", return_value=provider_registry),
        patch("app.workers.generation_worker._load_generation", AsyncMock(side_effect=[_generation(), _generation()])),
        patch("app.workers.generation_worker._update_generation", update_generation),
        patch("app.workers.generation_worker.get_event_bus", Mock(return_value=event_bus)),
    ):
        await run_worker()

    failed_call = update_generation.await_args_list[-1]
    assert failed_call.kwargs["status"] == "failed"
    assert failed_call.kwargs["provider_name"] == "comfyui"
    assert failed_call.kwargs["provider_job_id"] == "prompt-1"
    assert failed_call.kwargs["provider_state"]["failure_code"] == "execution_timeout"
    assert failed_call.kwargs["provider_state"]["prompt_id"] == "prompt-1"


@pytest.mark.asyncio
async def test_worker_fails_cleanly_when_prompt_is_missing():
    queue = AsyncMock()
    queue.dequeue = AsyncMock(side_effect=["gen-1", KeyboardInterrupt()])

    provider = DiffusersProviderFake()
    provider_registry = Mock()
    provider_registry.get_default = Mock(return_value=provider)

    update_generation = AsyncMock()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()
    broken_generation = _generation()
    broken_generation.prompt = {}

    with (
        patch("app.workers.generation_worker.get_task_queue", return_value=queue),
        patch("app.workers.generation_worker.get_provider_registry", return_value=provider_registry),
        patch("app.workers.generation_worker._load_generation", AsyncMock(side_effect=[broken_generation, broken_generation])),
        patch("app.workers.generation_worker._update_generation", update_generation),
        patch("app.workers.generation_worker.get_event_bus", Mock(return_value=event_bus)),
    ):
        await run_worker()

    failed_call = update_generation.await_args_list[-1]
    assert failed_call.kwargs["status"] == "failed"
    assert "Prompt cannot be empty" in failed_call.kwargs["error"]
