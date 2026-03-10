"""
Use case for retrieving generation task status.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.application.use_cases.base import Command, UseCaseResult, UseCase
from app.files.artifacts import ArtifactService, get_artifact_service
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
    provider_name: Optional[str] = None
    provider_state: Optional[Dict[str, Any]] = None
    image_path: Optional[str] = None
    image_filename: Optional[str] = None
    image_url: Optional[str] = None
    exp: Optional[int] = None
    sig: Optional[str] = None
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
        uow: Optional[SqlAlchemyUnitOfWork] = None,
        artifacts: Optional[ArtifactService] = None,
    ):
        self.uow = uow or SqlAlchemyUnitOfWork()
        self.artifacts = artifacts or get_artifact_service()
    
    async def __call__(self, command: GetGenerationStatusCommand) -> UseCaseResult[GenerationStatusResult]:
        """
        Execute get generation status use case.
        
        Args:
            command: Command containing task_id
            
        Returns:
            UseCaseResult with status data on success, error message if task not found
        """
        try:
            async with self.uow:
                generation = await self.uow.generations.get(command.task_id)

            if not generation:
                return UseCaseResult(
                    success=False,
                    error="Task not found",
                )
            signed = self.artifacts.build_signed_download(generation.image_path)
            return UseCaseResult(
                success=True,
                data=GenerationStatusResult(
                    task_id=command.task_id,
                    status=generation.status,
                    provider_name=generation.provider_name,
                    provider_state=generation.provider_state or {},
                    image_path=generation.image_path,
                    image_filename=signed["image_filename"],
                    image_url=signed["image_url"],
                    exp=signed["exp"],
                    sig=signed["sig"],
                    metadata=generation.result or {},
                    error=generation.error,
                    created_at=int(generation.created_at.timestamp()) if generation.created_at else None,
                    started_at=int(generation.started_at.timestamp()) if generation.started_at else None,
                    completed_at=int(generation.completed_at.timestamp()) if generation.completed_at else None,
                ),
            )
            
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=f"Failed to get task status: {str(e)}",
            )

