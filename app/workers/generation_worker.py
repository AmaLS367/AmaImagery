"""
Generation worker that processes image generation tasks from the queue.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.core.events import GenerationFailedEvent, ImageGeneratedEvent, get_event_bus
from app.core.logging import lg, logger
from app.domain.models import Generation
from app.domain.providers import GenerationRequest, get_provider_registry
from app.infra.queue import get_task_queue
from app.infra.uow import get_uow
from app.metrics.queue import (
    record_queue_dequeue,
    record_task_start,
    record_task_success,
    record_task_error,
)


async def run_worker() -> None:
    """
    Main worker loop that continuously processes generation tasks.
    
    Blocks on queue dequeue with timeout, processes tasks, and updates status.
    Exits only on unrecoverable errors or explicit shutdown.
    """
    worker_log = lg("worker")
    
    try:
        task_queue = get_task_queue()
        worker_log.info("worker.task_queue_obtained")
    except Exception as e:
        worker_log.exception("worker.task_queue_error", extra={"error": str(e)})
        raise
    
    try:
        provider_registry = get_provider_registry()
        worker_log.info("worker.provider_registry_obtained")
    except Exception as e:
        worker_log.exception("worker.provider_registry_error", extra={"error": str(e)})
        raise
    
    worker_log.info("worker.started", extra={"dequeue_timeout": 5.0})
    empty_polls = 0
    
    while True:
        try:
            task_id = await task_queue.dequeue(timeout=5.0)
            
            if task_id is None:
                empty_polls += 1
                if empty_polls % 12 == 0:  # Log every minute (12 * 5s)
                    worker_log.debug("worker.polling_queue", extra={"empty_polls": empty_polls})
                continue
            
            empty_polls = 0
            worker_log.info("worker.task_dequeued", extra={"task_id": task_id})
            
            record_queue_dequeue()
            await task_queue.update_status(task_id, "running")
            
            task_start_time = time.time()
            task_type = "image_generation"
            
            try:
                status = await task_queue.get_status(task_id)
                if not status or "payload" not in status:
                    worker_log.warning("worker.task_missing_payload", extra={"task_id": task_id})
                    await task_queue.mark_failed(task_id, "Task payload not found")
                    record_task_error(task_type=task_type, error_type="missing_payload")
                    continue
                
                payload = status["payload"]
                
                gen_request = _payload_to_generation_request(payload)
                user_id = payload.get("user_id")
                
                provider = provider_registry.get_default()
                
                record_task_start(task_type=task_type)
                
                worker_log.info(
                    "worker.generation_started",
                    extra={
                        "task_id": task_id,
                        "user_id": user_id,
                        "prompt": gen_request.prompt[:50] if gen_request.prompt else None,
                    },
                )
                
                try:
                    result = await provider.generate(gen_request)
                    worker_log.info(
                        "worker.generation_provider_completed",
                        extra={
                            "task_id": task_id,
                            "image_path": result.image_path,
                        },
                    )
                except Exception as e:
                    worker_log.exception(
                        "worker.generation_provider_failed",
                        extra={
                            "task_id": task_id,
                            "error": str(e),
                        },
                    )
                    raise
                
                try:
                    await _save_generation_to_db(
                        payload=payload,
                        user_id=user_id,
                        output_path=result.image_path,
                        metadata=result.metadata,
                    )
                    worker_log.info("worker.generation_saved_to_db", extra={"task_id": task_id})
                except Exception as e:
                    worker_log.exception(
                        "worker.generation_db_save_failed",
                        extra={
                            "task_id": task_id,
                            "error": str(e),
                        },
                    )
                    # Don't fail the task if DB save fails, but log it
                
                await task_queue.mark_completed(
                    task_id,
                    {
                        "image_path": result.image_path,
                        "image_filename": Path(result.image_path).name,
                        "metadata": result.metadata,
                    },
                )
                worker_log.info("worker.generation_marked_completed", extra={"task_id": task_id})
                
                duration = time.time() - task_start_time
                record_task_success(task_type=task_type, duration_seconds=duration)
                
                event_bus = get_event_bus()
                await event_bus.publish(
                    ImageGeneratedEvent(
                        task_id=task_id,
                        user_id=user_id or "anon",
                        image_path=result.image_path,
                        metadata=result.metadata,
                    )
                )
                
                worker_log.info(
                    "worker.generation_completed",
                    extra={
                        "task_id": task_id,
                        "image_path": result.image_path,
                    },
                )
                
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                worker_log.exception(
                    "worker.generation_failed",
                    extra={
                        "task_id": task_id,
                        "error": error_msg,
                    },
                )
                await task_queue.mark_failed(task_id, error_msg)
                record_task_error(task_type=task_type, error_type=error_type)
                
                event_bus = get_event_bus()
                await event_bus.publish(
                    GenerationFailedEvent(
                        task_id=task_id,
                        user_id=user_id or "anon",
                        error=error_msg,
                        error_type=error_type,
                    )
                )
                
        except KeyboardInterrupt:
            worker_log.info("worker.shutdown_requested")
            break
        except Exception as e:
            worker_log.exception("worker.loop_error", extra={"error": str(e)})
            await asyncio.sleep(1.0)


def _payload_to_generation_request(payload: Dict[str, Any]) -> GenerationRequest:
    return GenerationRequest(
        prompt=payload["prompt"],
        negative_prompt=payload.get("negative_prompt"),
        seed=payload.get("seed"),
        width=payload.get("width", 768),
        height=payload.get("height", 1152),
        steps=payload.get("steps"),
        guidance_scale=payload.get("guidance_scale"),
        ref_image_b64=payload.get("ref_image_b64"),
        ip_scale=payload.get("ip_scale"),
        style=payload.get("style", "anime"),
    )


async def _save_generation_to_db(
    payload: Dict[str, Any],
    user_id: Optional[str],
    output_path: str,
    metadata: Dict[str, Any],
) -> None:
    prompt_blob = {
        "prompt": payload.get("prompt"),
        "negative_prompt": payload.get("negative_prompt"),
    }
    
    params_blob = {
        "width": payload.get("width"),
        "height": payload.get("height"),
        "steps": payload.get("steps"),
        "guidance_scale": payload.get("guidance_scale"),
        "ip_scale": payload.get("ip_scale"),
        "seed": payload.get("seed"),
        "model_id": metadata.get("model_id", settings.model_id),
    }
    
    generation = Generation(
        user_id=user_id,
        prompt=prompt_blob,
        params=params_blob,
        image_path=output_path,
    )
    
    uow = get_uow()
    try:
        async with uow:
            await uow.generations.add(generation)
    except Exception as e:
        logger.exception("worker.save_to_db_failed", extra={"error": str(e)})
        raise

