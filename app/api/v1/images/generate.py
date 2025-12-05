"""
Image generation endpoints.
"""

from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.auth.deps import optional_user
from app.infra.uow import get_uow
from app.config import settings
from app.domain.schemas import GenReq, TaskResp
from app.services.rate_limiting import create_rate_limiter
from app.application.use_cases.generate_image import (
    GenerateImageCommand,
    GenerateImageUseCase,
)

router = APIRouter()

_generation_deps = [Depends(create_rate_limiter(settings.gen_per_user_per_min, 60))] if getattr(settings, "limits_enabled", False) else []


def get_generate_image_use_case() -> GenerateImageUseCase:
    """Dependency injection for GenerateImageUseCase."""
    uow = get_uow()
    return GenerateImageUseCase(uow=uow)


@router.post("/generate", response_model=TaskResp, dependencies=_generation_deps)
async def generate_image(
    request: GenReq,
    user: Optional[Any] = Depends(optional_user),
    use_case: GenerateImageUseCase = Depends(get_generate_image_use_case),
) -> TaskResp:
    user_id = str(getattr(user, "id", "anon")) if user is not None else "anon"
    
    command = GenerateImageCommand(
        user_id=user_id,
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        steps=request.steps,
        seed=request.seed,
        width=request.width,
        height=request.height,
        guidance_scale=request.guidance_scale,
        ref_image_b64=request.ref_image_b64,
        ip_scale=request.ip_scale,
        style=request.style,
    )
    
    result = await use_case(command)
    
    if not result.success or result.data is None:
        error_msg = result.error or "Unknown error"
        status_code = 400 if ("Blocked" in error_msg or "too large" in error_msg.lower()) else 500
        raise HTTPException(
            status_code=status_code,
            detail=error_msg,
        )
    
    return TaskResp(
        task_id=result.data.task_id,
        status=result.data.status,
    )

