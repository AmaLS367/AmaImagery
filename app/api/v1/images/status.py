"""
Task status endpoint.
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Path

from app.application.use_cases.get_generation_status import (
    GetGenerationStatusCommand,
    GetGenerationStatusUseCase,
)
from app.core.logging import lg
from app.domain.schemas import TaskStatusResp

router = APIRouter()


def get_generation_status_use_case() -> GetGenerationStatusUseCase:
    """Dependency injection for GetGenerationStatusUseCase."""
    return GetGenerationStatusUseCase()


@router.get("/status/{task_id}", response_model=TaskStatusResp)
async def get_task_status(
    task_id: str = Path(..., description="Task identifier"),
    use_case: GetGenerationStatusUseCase = Depends(get_generation_status_use_case),
) -> TaskStatusResp:
    command = GetGenerationStatusCommand(task_id=task_id)
    result = await use_case(command)

    if not result.success or result.data is None:
        error_msg = result.error or "Unknown error"
        status_code = 404 if "not found" in error_msg.lower() else 500

        lg("app").bind(
            scope="images",
            action="get_status",
            task_id=task_id,
            status_code=status_code,
            error=error_msg,
        ).error("Failed to get task status")

        raise HTTPException(
            status_code=status_code,
            detail=error_msg,
        )

    data = result.data

    # Log response for debugging
    lg("app").bind(
        scope="images",
        action="get_status",
        task_id=task_id,
        status=data.status,
        provider_name=data.provider_name,
        has_image_path=bool(data.image_path),
        has_image_filename=bool(data.image_filename),
        has_image_url=bool(data.image_url),
        created_at=data.created_at,
        started_at=data.started_at,
        completed_at=data.completed_at,
    ).info("Task status retrieved")

    response = TaskStatusResp(
        task_id=data.task_id,
        status=data.status,
        provider_name=data.provider_name,
        provider_state=data.provider_state,
        image_path=data.image_path,
        image_filename=data.image_filename,
        image_url=data.image_url,
        exp=data.exp,
        sig=data.sig,
        metadata=data.metadata,
        error=data.error,
        created_at=data.created_at,
        started_at=data.started_at,
        completed_at=data.completed_at,
    )

    # Additional debug logging
    if data.status == "queued":
        lg("app").warning(
            "Task still queued",
            extra={
                "task_id": task_id,
                "created_at": data.created_at,
                "age_seconds": int(time.time()) - (data.created_at or 0) if data.created_at else None,
            },
        )

    return response
