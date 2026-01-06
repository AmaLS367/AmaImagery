"""
Task status endpoint.
"""

import time
from pathlib import Path as PathLib
from fastapi import APIRouter, Depends, HTTPException, Path

from app.config import settings
from app.core.logging import lg
from app.domain.schemas import TaskStatusResp
from app.files.signing import make_signature
from app.application.use_cases.get_generation_status import (
    GetGenerationStatusCommand,
    GetGenerationStatusUseCase,
)


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
    
    # Generate signed URL if image is available
    image_url = None
    exp = None
    sig = None
    if data.status == "completed" and data.image_filename:
        now = int(time.time())
        ttl = int(settings.file_download_ttl_sec)
        exp = now + ttl
        sig = make_signature(data.image_filename, exp)
        image_url = f"/api/v1/file?path={data.image_filename}&exp={exp}&sig={sig}"
    
    # Log response for debugging
    lg("app").bind(
        scope="images",
        action="get_status",
        task_id=task_id,
        status=data.status,
        has_image_path=bool(data.image_path),
        has_image_filename=bool(data.image_filename),
        has_image_url=bool(image_url),
        created_at=data.created_at,
        started_at=data.started_at,
        completed_at=data.completed_at,
    ).info("Task status retrieved")
    
    response = TaskStatusResp(
        task_id=data.task_id,
        status=data.status,
        image_path=data.image_path,
        image_filename=data.image_filename,
        image_url=image_url,
        exp=exp,
        sig=sig,
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
            }
        )
    
    return response

