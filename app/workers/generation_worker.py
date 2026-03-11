"""
Generation worker that processes image generation tasks from the queue.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.core.events import GenerationFailedEvent, ImageGeneratedEvent, get_event_bus
from app.core.logging import lg
from app.domain.generation_lifecycle import COMPLETED, FAILED, RUNNING, is_terminal_status
from app.domain.models import Generation
from app.domain.providers import (
    GenerationRequest,
    ProviderOperationError,
    ProviderResult,
    ProviderSubmission,
    get_provider_registry,
)
from app.files.artifacts import get_artifact_service
from app.infra.queue import get_task_queue
from app.infra.uow import get_uow
from app.metrics.queue import (
    record_queue_dequeue,
    record_task_error,
    record_task_start,
    record_task_success,
)


async def run_worker() -> None:
    worker_log = lg("worker")
    task_queue = get_task_queue()
    provider_registry = get_provider_registry()

    worker_log.info("worker.started", extra={"dequeue_timeout": 5.0})
    empty_polls = 0

    while True:
        try:
            generation_id = await task_queue.dequeue(timeout=5.0)
            if generation_id is None:
                empty_polls += 1
                if empty_polls % 12 == 0:
                    worker_log.debug("worker.polling_queue", extra={"empty_polls": empty_polls})
                continue

            empty_polls = 0
            record_queue_dequeue()
            task_start_time = time.time()
            task_type = "image_generation"

            generation = await _load_generation(generation_id)
            if generation is None:
                worker_log.warning("worker.task_missing_generation", extra={"task_id": generation_id})
                record_task_error(task_type=task_type, error_type="missing_generation")
                continue

            if is_terminal_status(generation.status):
                worker_log.info(
                    "worker.task_already_terminal",
                    extra={"task_id": generation_id, "status": generation.status},
                )
                continue

            user_id = str(generation.user_id) if generation.user_id else None
            submission: ProviderSubmission | None = None
            provider_name: str | None = None

            try:
                provider = provider_registry.get_default()
                provider_name = _provider_name(provider)
                await _update_generation(
                    generation_id,
                    status=RUNNING,
                    provider_name=provider_name,
                    started_at=datetime.now(timezone.utc),
                    error=None,
                    completed_at=None,
                )
                generation = await _load_generation(generation_id)
                if generation is None:
                    raise RuntimeError("Generation disappeared during processing")

                request = _generation_to_request(generation)
                record_task_start(task_type=task_type)

                submission = await provider.submit(request)
                await _persist_submission(generation_id, submission)

                result = await provider.wait_for_result(
                    submission,
                    timeout_sec=float(getattr(provider, "timeout_sec", settings.comfyui_timeout_sec)),
                )
                persisted_path = await _persist_artifact(generation_id, result)

                await _update_generation(
                    generation_id,
                    status=COMPLETED,
                    provider_name=result.provider_name,
                    provider_job_id=result.provider_job_id,
                    provider_state=result.provider_state,
                    result=result.metadata,
                    image_path=persisted_path,
                    error=None,
                    completed_at=datetime.now(timezone.utc),
                )

                duration = time.time() - task_start_time
                record_task_success(task_type=task_type, duration_seconds=duration)
                await get_event_bus().publish(
                    ImageGeneratedEvent(
                        task_id=generation_id,
                        user_id=user_id or "anon",
                        image_path=persisted_path,
                        metadata=result.metadata,
                    )
                )
            except ProviderOperationError as exc:
                failure_state = exc.as_persistable_state()
                if submission is not None:
                    failure_state = {
                        **dict(submission.provider_state or {}),
                        **failure_state,
                    }
                await _update_generation(
                    generation_id,
                    status=FAILED,
                    provider_name=exc.provider_name or locals().get("provider_name"),
                    provider_job_id=exc.provider_job_id or (submission.provider_job_id if submission else None),
                    provider_state=failure_state,
                    image_path=None,
                    error=exc.message,
                    completed_at=datetime.now(timezone.utc),
                )
                record_task_error(task_type=task_type, error_type=exc.error_code)
                await get_event_bus().publish(
                    GenerationFailedEvent(
                        task_id=generation_id,
                        user_id=user_id or "anon",
                        error=exc.message,
                        error_type=exc.error_code,
                    )
                )
                worker_log.warning(
                    "worker.generation_failed",
                    extra={
                        "task_id": generation_id,
                        "provider_name": exc.provider_name,
                        "provider_job_id": exc.provider_job_id,
                        "error": exc.message,
                        "error_code": exc.error_code,
                        "stage": exc.stage,
                    },
                )
            except Exception as exc:
                error_msg = str(exc)
                error_type = type(exc).__name__
                provider_state = dict(submission.provider_state or {}) if submission else {}
                await _update_generation(
                    generation_id,
                    status=FAILED,
                    provider_name=provider_name,
                    provider_job_id=submission.provider_job_id if submission else None,
                    provider_state=provider_state,
                    image_path=None,
                    error=error_msg,
                    completed_at=datetime.now(timezone.utc),
                )
                record_task_error(task_type=task_type, error_type=error_type)
                await get_event_bus().publish(
                    GenerationFailedEvent(
                        task_id=generation_id,
                        user_id=user_id or "anon",
                        error=error_msg,
                        error_type=error_type,
                    )
                )
                worker_log.exception(
                    "worker.generation_failed",
                    extra={"task_id": generation_id, "error": error_msg},
                )
        except KeyboardInterrupt:
            worker_log.info("worker.shutdown_requested")
            break
        except Exception as exc:
            worker_log.exception("worker.loop_error", extra={"error": str(exc)})
            await asyncio.sleep(1.0)


def _generation_to_request(generation: Generation) -> GenerationRequest:
    prompt_blob = generation.prompt or {}
    params = generation.params or {}
    return GenerationRequest(
        generation_id=str(generation.id),
        prompt=prompt_blob.get("prompt") or "",
        negative_prompt=prompt_blob.get("negative_prompt"),
        seed=params.get("seed"),
        width=params.get("width", 768),
        height=params.get("height", 1152),
        steps=params.get("steps"),
        guidance_scale=params.get("guidance_scale"),
        ref_image_b64=params.get("ref_image_b64"),
        ip_scale=params.get("ip_scale"),
        style=params.get("style", "anime"),
    )


async def _load_generation(generation_id: str) -> Generation | None:
    async with get_uow() as uow:
        return await uow.generations.get(generation_id)


async def _update_generation(generation_id: str, **fields: Any) -> Generation | None:
    async with get_uow() as uow:
        return await uow.generations.update_fields(generation_id, **fields)


async def _persist_submission(generation_id: str, submission: ProviderSubmission) -> None:
    await _update_generation(
        generation_id,
        provider_name=submission.provider_name,
        provider_job_id=submission.provider_job_id,
        provider_state=submission.provider_state,
    )


async def _persist_artifact(generation_id: str, result: ProviderResult) -> str:
    artifact_service = get_artifact_service()
    if result.artifact_persisted:
        return str(result.image_path)
    return artifact_service.persist_local(generation_id, result.image_path)


def _provider_name(provider: Any) -> str:
    explicit_name = getattr(provider, "provider_name", None)
    if isinstance(explicit_name, str) and explicit_name.strip():
        return explicit_name
    return type(provider).__name__.removesuffix("Provider").lower()
