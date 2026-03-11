from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from app.domain.providers.errors import ProviderOperationError
from app.domain.providers.interfaces import GenerationRequest, IImageProvider, ProviderResult, ProviderSubmission
from app.files.artifacts import get_artifact_service
from app.infra.providers.comfyui_client import (
    ComfyUIArtifactError,
    ComfyUIClient,
    ComfyUICompletion,
    ComfyUIExecutionTimeout,
    ComfyUIHistoryError,
    ComfyUISubmitError,
    ComfyUIWebsocketError,
)
from app.infra.providers.comfyui_workflows import inject_request, load_workflow_bundle, output_node_id


class ComfyUIProvider(IImageProvider):
    provider_name = "comfyui"

    def __init__(self, client: ComfyUIClient | None = None) -> None:
        from app.config import settings

        self.client = client or ComfyUIClient()
        self.timeout_sec = float(settings.comfyui_timeout_sec)

    async def submit(self, request: GenerationRequest) -> ProviderSubmission:
        try:
            workflow, workflow_map = load_workflow_bundle()
            rendered = inject_request(
                workflow,
                workflow_map,
                {
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt or "",
                    "seed": request.seed or 0,
                    "width": request.width,
                    "height": request.height,
                    "steps": request.steps or 28,
                    "cfg": float(request.guidance_scale or 7.5),
                },
            )
            payload = await self.client.submit_prompt(rendered)
            prompt_id = payload.get("prompt_id")
            if not prompt_id:
                raise ComfyUISubmitError("ComfyUI did not return prompt_id")
            return ProviderSubmission(
                provider_name=self.provider_name,
                provider_job_id=str(prompt_id),
                provider_state={
                    "prompt_id": str(prompt_id),
                    "workflow_map": workflow_map,
                    "generation_id": request.generation_id,
                },
            )
        except ProviderOperationError:
            raise
        except Exception as exc:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="submit",
                message=str(exc),
                error_code="submit_failed",
            ) from exc

    async def wait_for_result(self, submission: ProviderSubmission, timeout_sec: float) -> ProviderResult:
        prompt_id = submission.provider_job_id or submission.provider_state.get("prompt_id")
        if not prompt_id:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="wait",
                message="Missing ComfyUI prompt_id",
                error_code="missing_provider_job_id",
                provider_state=dict(submission.provider_state or {}),
            )

        try:
            completion = await self.client.wait_for_completion(str(prompt_id), timeout_sec)
        except ComfyUIExecutionTimeout as exc:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="wait",
                message=str(exc),
                error_code="execution_timeout",
                provider_job_id=str(prompt_id),
                provider_state=dict(submission.provider_state or {}),
                retryable=False,
            ) from exc
        except (ComfyUIHistoryError, ComfyUIWebsocketError) as exc:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="wait",
                message=str(exc),
                error_code="execution_tracking_failed",
                provider_job_id=str(prompt_id),
                provider_state=dict(submission.provider_state or {}),
                retryable=True,
            ) from exc

        history = completion.history
        provider_state = _provider_state(history, None, completion)
        remote_error = _extract_terminal_error(history)
        if remote_error:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="wait",
                message=remote_error,
                error_code="remote_execution_failed",
                provider_job_id=str(prompt_id),
                provider_state=provider_state,
            )

        try:
            image_info = _extract_image_info(history, submission.provider_state.get("workflow_map") or {})
        except ComfyUIHistoryError as exc:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="result",
                message=str(exc),
                error_code="result_missing",
                provider_job_id=str(prompt_id),
                provider_state=provider_state,
            ) from exc

        try:
            payload = await self.client.fetch_image_bytes(
                image_info["filename"],
                subfolder=image_info.get("subfolder", ""),
                folder_type=image_info.get("type", "output"),
            )
        except ComfyUIArtifactError as exc:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="artifact",
                message=str(exc),
                error_code="artifact_retrieval_failed",
                provider_job_id=str(prompt_id),
                provider_state=_provider_state(history, image_info, completion),
            ) from exc

        generation_id = submission.provider_state.get("generation_id")
        if not generation_id:
            raise ProviderOperationError(
                provider_name=self.provider_name,
                stage="artifact",
                message="Missing generation_id for ComfyUI artifact persistence",
                error_code="artifact_persistence_failed",
                provider_job_id=str(prompt_id),
                provider_state=_provider_state(history, image_info, completion),
            )

        ext = Path(image_info["filename"]).suffix.lstrip(".") or "png"
        image_path = await get_artifact_service().persist_bytes(str(generation_id), payload, ext=ext)
        return ProviderResult(
            provider_name=self.provider_name,
            image_path=image_path,
            provider_job_id=str(prompt_id),
            provider_state=_provider_state(history, image_info, completion),
            metadata={
                "history": history,
                "wait_strategy": completion.wait_strategy,
                "websocket_error": completion.websocket_error,
            },
            artifact_persisted=True,
        )

    async def cancel(self, submission: ProviderSubmission) -> None:
        raise ProviderOperationError(
            provider_name=self.provider_name,
            stage="cancel",
            message="ComfyUI cancellation is not supported by this provider implementation",
            error_code="cancel_unsupported",
            provider_job_id=submission.provider_job_id,
            provider_state=dict(submission.provider_state or {}),
            retryable=False,
            terminal=False,
        )

    async def health_check(self) -> bool:
        return await self.client.ping()

    def supports_features(self, features: set[str]) -> bool:
        return features.issubset({"text2image"})


def _extract_image_info(history: dict[str, Any], workflow_map: dict[str, Any]) -> dict[str, Any]:
    outputs = history.get("outputs", {})
    preferred = output_node_id(workflow_map)
    if preferred and preferred in outputs:
        node_output = outputs[preferred]
    elif outputs:
        node_output = next(iter(outputs.values()))
    else:
        raise ComfyUIHistoryError("ComfyUI history did not contain outputs")
    images = node_output.get("images") or []
    if not images:
        raise ComfyUIHistoryError("ComfyUI output did not contain images")
    return cast(dict[str, Any], images[0])


def _provider_state(
    history: dict[str, Any],
    image_info: dict[str, Any] | None,
    completion: ComfyUICompletion,
) -> dict[str, Any]:
    state = {
        "history": history,
        "wait_strategy": completion.wait_strategy,
        "websocket_error": completion.websocket_error,
    }
    if image_info is not None:
        state["image"] = image_info
    return state


def _extract_terminal_error(history: dict[str, Any]) -> str | None:
    status = history.get("status")
    if not isinstance(status, dict):
        return None

    completed = status.get("completed")
    status_str = str(status.get("status_str") or "").strip().lower()
    if completed is False or status_str in {"error", "failed", "failure"}:
        messages = status.get("messages")
        if isinstance(messages, list) and messages:
            last_message = messages[-1]
            if isinstance(last_message, (list, tuple)) and len(last_message) >= 2:
                return str(last_message[1])
            return str(last_message)
        return f"ComfyUI execution failed ({status_str or 'unknown'})"
    return None
