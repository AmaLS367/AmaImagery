"""
Use case for image generation.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, cast

from app.application.use_cases.base import Command, UseCaseResult
from app.core.logging import lg
from app.domain.generation_lifecycle import FAILED, QUEUED
from app.domain.models import Generation
from app.domain.providers import ProviderRegistry, get_provider_registry
from app.domain.schemas import GenReq
from app.infra.queue import TaskQueue, get_task_queue
from app.infra.uow import SqlAlchemyUnitOfWork, get_uow
from app.metrics.queue import record_queue_enqueue
from app.services.generation_service import GenerationService

Style = Literal["realistic", "anime"]


@dataclass
class GenerateImageCommand(Command):
    """
    Command for image generation use case.

    Contains all parameters needed to generate an image.
    """

    user_id: str
    prompt: str
    negative_prompt: str | None = None
    steps: int | None = None
    seed: int | None = None
    width: int = 768
    height: int = 1152
    guidance_scale: float = 7.5
    ref_image_b64: str | None = None
    ip_scale: float = 0.6
    style: Style = "anime"


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
        uow: SqlAlchemyUnitOfWork | None = None,
        uow_factory: Callable[[], SqlAlchemyUnitOfWork] | None = None,
        provider_registry: ProviderRegistry | None = None,
        task_queue: TaskQueue | None = None,
    ):
        if uow_factory is not None:
            self._uow_factory = uow_factory
        elif uow is not None:
            self._uow_factory = _build_uow_factory(uow)
        else:
            self._uow_factory = get_uow
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
                steps=command.steps or 28,
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
                async with self._uow_factory() as uow:
                    user = await uow.users.get(command.user_id)
                    if user is not None:
                        user_settings = await uow.users.get_settings(user.id)
                        cast(Any, user).settings = user_settings

            self.generation_service._validate_request(gen_req)
            self.generation_service._check_safety_policies(gen_req, user)

            params: dict[str, Any] = {
                "prompt": command.prompt,
                "seed": command.seed,
                "width": command.width,
                "height": command.height,
                "steps": command.steps or 28,
                "guidance_scale": command.guidance_scale,
                "ref_image_b64": command.ref_image_b64,
                "ip_scale": command.ip_scale,
                "style": command.style,
            }
            prompt_blob: dict[str, Any] = {
                "prompt": command.prompt,
                "negative_prompt": command.negative_prompt,
            }
            default_provider = self.provider_registry.get_default()
            provider_name = _provider_name(default_provider)

            generation = Generation(
                user_id=None if command.user_id == "anon" else getattr(user, "id", None),
                prompt=prompt_blob,
                params=params,
                status=QUEUED,
                provider_name=provider_name,
                provider_state={},
                result={},
            )

            async with self._uow_factory() as uow:
                await uow.generations.add(generation)

            task_id = str(generation.id)

            try:
                await self.task_queue.enqueue(task_id)
            except Exception as exc:
                async with self._uow_factory() as uow:
                    await uow.generations.update_fields(
                        generation.id,
                        status=FAILED,
                        error=f"Failed to enqueue task: {exc}",
                        completed_at=datetime.now(UTC),
                    )
                raise

            record_queue_enqueue()

            lg("api").info(
                "generate.task_enqueued",
                extra={
                    "task_id": task_id,
                    "user_id": command.user_id,
                    "provider_name": provider_name,
                },
            )

            return UseCaseResult(
                success=True,
                data=GenerateImageResult(task_id=task_id, status=QUEUED),
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


def _provider_name(provider: Any) -> str:
    explicit_name = getattr(provider, "provider_name", None)
    if isinstance(explicit_name, str) and explicit_name.strip():
        return explicit_name
    return type(provider).__name__.removesuffix("Provider").lower()


def _build_uow_factory(uow: SqlAlchemyUnitOfWork) -> Callable[[], SqlAlchemyUnitOfWork]:
    if (
        isinstance(uow, SqlAlchemyUnitOfWork)
        and getattr(uow, "_owns_session", False)
        and getattr(uow, "_session", None) is None
    ):
        return SqlAlchemyUnitOfWork
    return lambda: uow
