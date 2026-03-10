"""
Use case for image generation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal
from uuid import UUID

from app.application.use_cases.base import Command, UseCaseResult, UseCase
from app.domain.providers import ProviderRegistry, get_provider_registry
from app.infra.queue import TaskQueue, get_task_queue
from app.infra.uow import SqlAlchemyUnitOfWork
from app.metrics.queue import record_queue_enqueue
from app.services.generation_service import GenerationService
from app.core.logging import lg
from app.domain.models import Generation
from app.domain.schemas import GenReq

Style = Literal['realistic', 'anime']


@dataclass
class GenerateImageCommand(Command):
    """
    Command for image generation use case.
    
    Contains all parameters needed to generate an image.
    """
    user_id: str
    prompt: str
    negative_prompt: Optional[str] = None
    steps: Optional[int] = None
    seed: Optional[int] = None
    width: int = 768
    height: int = 1152
    guidance_scale: float = 7.5
    ref_image_b64: Optional[str] = None
    ip_scale: float = 0.6
    style: Style = 'anime'


@dataclass
class GenerateImageResult:
    """Result data for image generation use case."""
    task_id: str
    status: str


class GenerateImageUseCase:
    """
    Use case for generating images asynchronously.
    
    Validates the request, enqueues the task, and persists metadata.
    """
    
    def __init__(
        self,
        uow: SqlAlchemyUnitOfWork,
        provider_registry: Optional[ProviderRegistry] = None,
        task_queue: Optional[TaskQueue] = None,
    ):
        self.uow = uow
        self.provider_registry = provider_registry or get_provider_registry()
        self.task_queue = task_queue or get_task_queue()
        self.generation_service = GenerationService()
    
    async def __call__(self, command: GenerateImageCommand) -> UseCaseResult[GenerateImageResult]:
        """
        Execute image generation use case.
        
        Args:
            command: Command containing generation parameters
            
        Returns:
            UseCaseResult with task_id on success, error message on failure
        """
        try:
            gen_req = GenReq(
                prompt=command.prompt,
                negative_prompt=command.negative_prompt,
                steps=command.steps,
                seed=command.seed,
                width=command.width,
                height=command.height,
                guidance_scale=command.guidance_scale,
                ref_image_b64=command.ref_image_b64,
                ip_scale=command.ip_scale,
                style=command.style,
            )
            
            user = None
            if command.user_id != "anon":
                async with self.uow:
                    user = await self.uow.users.get(command.user_id)
                    if user is not None:
                        user.settings = await self.uow.users.get_settings(user.id)
            
            self.generation_service._validate_request(gen_req)
            self.generation_service._check_safety_policies(gen_req, user)
            
            params: Dict[str, Any] = {
                "prompt": command.prompt,
                "seed": command.seed,
                "width": command.width,
                "height": command.height,
                "steps": command.steps,
                "guidance_scale": command.guidance_scale,
                "ref_image_b64": command.ref_image_b64,
                "ip_scale": command.ip_scale,
                "style": command.style,
            }
            prompt_blob: Dict[str, Any] = {
                "prompt": command.prompt,
                "negative_prompt": command.negative_prompt,
            }

            generation = Generation(
                user_id=None if command.user_id == "anon" else getattr(user, "id", None),
                prompt=prompt_blob,
                params=params,
                status="queued",
                provider_state={},
                result={},
            )

            async with self.uow:
                await self.uow.generations.add(generation)

            task_id = str(generation.id)

            try:
                await self.task_queue.enqueue(task_id)
            except Exception as exc:
                async with self.uow:
                    await self.uow.generations.update_fields(
                        generation.id,
                        status="failed",
                        error=f"Failed to enqueue task: {exc}",
                    )
                raise

            record_queue_enqueue()
            
            lg("api").info(
                "generate.task_enqueued",
                extra={
                    "task_id": task_id,
                    "user_id": command.user_id,
                },
            )
            
            return UseCaseResult(
                success=True,
                data=GenerateImageResult(task_id=task_id, status="queued"),
            )
            
        except ValueError as e:
            return UseCaseResult(
                success=False,
                error=str(e),
            )
        except Exception as e:
            lg("api").exception("generate.enqueue_failed", extra={"error": str(e)})
            return UseCaseResult(
                success=False,
                error=f"Failed to enqueue task: {str(e)}",
            )

