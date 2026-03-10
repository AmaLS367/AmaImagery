"""
Use case for retrieving generation task status.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.application.use_cases.base import Command, UseCaseResult, UseCase
from app.domain.generation_lifecycle import build_generation_public_payload
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
            payload = build_generation_public_payload(generation, artifacts=self.artifacts)
            return UseCaseResult(
                success=True,
                data=GenerationStatusResult(
                    task_id=payload.task_id,
                    status=payload.status,
                    provider_name=payload.provider_name,
                    provider_state=payload.provider_state,
                    image_path=payload.image_path,
                    image_filename=payload.image_filename,
                    image_url=payload.image_url,
                    exp=payload.exp,
                    sig=payload.sig,
                    metadata=payload.metadata,
                    error=payload.error,
                    created_at=payload.created_at,
                    started_at=payload.started_at,
                    completed_at=payload.completed_at,
                ),
            )
            
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=f"Failed to get task status: {str(e)}",
            )

