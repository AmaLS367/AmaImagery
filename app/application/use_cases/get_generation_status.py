"""
Use case for retrieving generation task status.
"""

from dataclasses import dataclass
from typing import Any

from app.application.use_cases.base import Command, UseCaseResult
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
    provider_name: str | None = None
    provider_state: dict[str, Any] | None = None
    image_path: str | None = None
    image_filename: str | None = None
    image_url: str | None = None
    exp: int | None = None
    sig: str | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None
    created_at: int | None = None
    started_at: int | None = None
    completed_at: int | None = None


class GetGenerationStatusUseCase:
    """
    Use case for retrieving generation task status.

    Retrieves task status from the queue and maps it to the API response format.
    """

    def __init__(
        self,
        uow: SqlAlchemyUnitOfWork | None = None,
        artifacts: ArtifactService | None = None,
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
