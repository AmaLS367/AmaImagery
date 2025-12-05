"""
Task status endpoint.
"""

from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Path

from app.core.logging import lg
from app.domain.schemas import TaskStatusResp
from app.infra.queue import get_task_queue

router = APIRouter()


@router.get("/status/{task_id}", response_model=TaskStatusResp)
async def get_task_status(
    task_id: str = Path(..., description="Task identifier"),
) -> TaskStatusResp:
    task_queue = get_task_queue()
    
    status_data = await task_queue.get_status(task_id)
    
    if not status_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = status_data.get("status", "unknown")
    
    if status == "completed":
        result = status_data.get("result", {})
        return TaskStatusResp(
            task_id=task_id,
            status=status,
            image_path=result.get("image_path"),
            image_filename=result.get("image_filename"),
            metadata=result.get("metadata"),
            created_at=status_data.get("created_at"),
            started_at=status_data.get("started_at"),
            completed_at=status_data.get("completed_at"),
        )
    
    if status == "failed":
        return TaskStatusResp(
            task_id=task_id,
            status=status,
            error=status_data.get("error"),
            created_at=status_data.get("created_at"),
            started_at=status_data.get("started_at"),
            completed_at=status_data.get("completed_at"),
        )
    
    return TaskStatusResp(
        task_id=task_id,
        status=status,
        created_at=status_data.get("created_at"),
        started_at=status_data.get("started_at"),
    )

