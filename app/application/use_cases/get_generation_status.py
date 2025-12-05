"""
Use case for retrieving generation task status.

Retrieves task status from the queue and maps it to API response format.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.application.use_cases.base import Command, UseCaseResult, UseCase
from app.infra.queue import TaskQueue, get_task_queue
from app.infra.uow import SqlAlchemyUnitOfWork


@dataclass
class GetGenerationStatusCommand(Command):
    """
    Command for getting generation task status.
    
    Attributes:
        task_id: Unique task identifier
    """
    task_id: str


@dataclass
class GenerationStatusResult:
    """
    Result data for generation status use case.
    
    Contains all fields needed for TaskStatusResp API response.
    """
    task_id: str
    status: str
    image_path: Optional[str] = None
    image_filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[int] = None
    started_at: Optional[int] = None
    completed_at: Optional[int] = None


class GetGenerationStatusUseCase:
    """
    Use case for retrieving generation task status.
    
    Retrieves task status from the queue and maps it to the API response format.
    """
    
    def __init__(
        self,
        task_queue: Optional[TaskQueue] = None,
        uow: Optional[SqlAlchemyUnitOfWork] = None,
    ):
        self.task_queue = task_queue or get_task_queue()
        self.uow = uow
    
    async def __call__(self, command: GetGenerationStatusCommand) -> UseCaseResult[GenerationStatusResult]:
        """
        Execute get generation status use case.
        
        Args:
            command: Command containing task_id
            
        Returns:
            UseCaseResult with status data on success, error message if task not found
        """
        try:
            status_data = await self.task_queue.get_status(command.task_id)
            
            if not status_data:
                return UseCaseResult(
                    success=False,
                    error="Task not found",
                )
            
            status = status_data.get("status", "unknown")
            
            if status == "completed":
                result = status_data.get("result", {})
                return UseCaseResult(
                    success=True,
                    data=GenerationStatusResult(
                        task_id=command.task_id,
                        status=status,
                        image_path=result.get("image_path"),
                        image_filename=result.get("image_filename"),
                        metadata=result.get("metadata"),
                        created_at=status_data.get("created_at"),
                        started_at=status_data.get("started_at"),
                        completed_at=status_data.get("completed_at"),
                    ),
                )
            
            if status == "failed":
                return UseCaseResult(
                    success=True,
                    data=GenerationStatusResult(
                        task_id=command.task_id,
                        status=status,
                        error=status_data.get("error"),
                        created_at=status_data.get("created_at"),
                        started_at=status_data.get("started_at"),
                        completed_at=status_data.get("completed_at"),
                    ),
                )
            
            return UseCaseResult(
                success=True,
                data=GenerationStatusResult(
                    task_id=command.task_id,
                    status=status,
                    created_at=status_data.get("created_at"),
                    started_at=status_data.get("started_at"),
                ),
            )
            
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=f"Failed to get task status: {str(e)}",
            )

