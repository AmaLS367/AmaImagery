"""
Generation worker that processes image generation tasks from the queue.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import lg, logger
from app.domain.models import Generation
from app.domain.providers import GenerationRequest, get_provider_registry
from app.infra.queue import get_task_queue
from app.infra.uow import get_uow


async def run_worker() -> None:
    """
    Main worker loop that continuously processes generation tasks.
    
    Blocks on queue dequeue with timeout, processes tasks, and updates status.
    Exits only on unrecoverable errors or explicit shutdown.
    """
    task_queue = get_task_queue()
    provider_registry = get_provider_registry()
    
    worker_log = lg("worker")
    worker_log.info("worker.started")
    
    while True:
        try:
            task_id = await task_queue.dequeue(timeout=5.0)
            
            if task_id is None:
                continue
            
            await task_queue.update_status(task_id, "running")
            
            try:
                status = await task_queue.get_status(task_id)
                if not status or "payload" not in status:
                    worker_log.warning("worker.task_missing_payload", extra={"task_id": task_id})
                    await task_queue.mark_failed(task_id, "Task payload not found")
                    continue
                
                payload = status["payload"]
                
                gen_request = _payload_to_generation_request(payload)
                user_id = payload.get("user_id")
                
                provider = provider_registry.get_default()
                
                worker_log.info(
                    "worker.generation_started",
                    extra={
                        "task_id": task_id,
                        "user_id": user_id,
                        "prompt": gen_request.prompt[:50] if gen_request.prompt else None,
                    },
                )
                
                result = await provider.generate(gen_request)
                
                await _save_generation_to_db(
                    payload=payload,
                    user_id=user_id,
                    output_path=result.image_path,
                    metadata=result.metadata,
                )
                
                await task_queue.mark_completed(
                    task_id,
                    {
                        "image_path": result.image_path,
                        "image_filename": Path(result.image_path).name,
                        "metadata": result.metadata,
                    },
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
                worker_log.exception(
                    "worker.generation_failed",
                    extra={
                        "task_id": task_id,
                        "error": error_msg,
                    },
                )
                await task_queue.mark_failed(task_id, error_msg)
                
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

