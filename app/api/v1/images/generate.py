"""
Image generation endpoints.
"""

from typing import Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.auth.deps import optional_user
from app.infra.db import get_db
from app.infra.uow import get_uow
from app.core.logging import lg
from app.config import settings
from app.domain.schemas import GenReq, TaskResp
from app.services.generation_service import GenerationService
from app.services.rate_limiting import create_rate_limiter
from app.infra.queue import get_task_queue

router = APIRouter()

_generation_deps = [Depends(create_rate_limiter(settings.gen_per_user_per_min, 60))] if getattr(settings, "limits_enabled", False) else []

@router.post("/generate", response_model=TaskResp, dependencies=_generation_deps)
async def generate_image(
    request: GenReq,
    db: Session = Depends(get_db),
    user: Optional[Any] = Depends(optional_user),
) -> TaskResp:
    uow = get_uow(session=db)
    generation_service = GenerationService(uow)
    
    try:
        generation_service._validate_request(request)
        generation_service._check_safety_policies(request, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    user_id = str(getattr(user, "id", "anon")) if user is not None else "anon"
    
    payload: Dict[str, Any] = {
        "prompt": request.prompt,
        "negative_prompt": request.negative_prompt,
        "seed": request.seed,
        "width": request.width,
        "height": request.height,
        "steps": request.steps,
        "guidance_scale": request.guidance_scale,
        "ref_image_b64": request.ref_image_b64,
        "ip_scale": request.ip_scale,
        "style": request.style,
        "user_id": user_id,
    }
    
    try:
        task_queue = get_task_queue()
        task_id = await task_queue.enqueue(payload)
        
        lg("api").info(
            "generate.task_enqueued",
            extra={
                "task_id": task_id,
                "user_id": user_id,
            },
        )
        
        return TaskResp(task_id=task_id, status="queued")
        
    except Exception as e:
        lg("api").exception("generate.enqueue_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to enqueue task: {str(e)}")

