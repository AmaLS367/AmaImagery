"""
Task status endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, Path

from app.domain.schemas import TaskStatusResp
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
        raise HTTPException(
            status_code=404 if "not found" in error_msg.lower() else 500,
            detail=error_msg,
        )
    
    data = result.data
    return TaskStatusResp(
        task_id=data.task_id,
        status=data.status,
        image_path=data.image_path,
        image_filename=data.image_filename,
        metadata=data.metadata,
        error=data.error,
        created_at=data.created_at,
        started_at=data.started_at,
        completed_at=data.completed_at,
    )

