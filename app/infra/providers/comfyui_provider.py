from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import settings
from app.domain.providers.interfaces import GenerationRequest, IImageProvider, ProviderResult, ProviderSubmission
from app.files.artifacts import get_artifact_service
from app.infra.providers.comfyui_client import ComfyUIClient
from app.infra.providers.comfyui_workflows import inject_request, load_workflow_bundle, output_node_id


class ComfyUIProvider(IImageProvider):
    def __init__(self, client: ComfyUIClient | None = None) -> None:
        self.client = client or ComfyUIClient()
        self.timeout_sec = float(settings.comfyui_timeout_sec)

    async def submit(self, request: GenerationRequest) -> ProviderSubmission:
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
            raise RuntimeError("ComfyUI did not return prompt_id")
        return ProviderSubmission(
            provider_name="comfyui",
            provider_job_id=str(prompt_id),
            provider_state={
                "prompt_id": str(prompt_id),
                "workflow_map": workflow_map,
                "generation_id": request.generation_id,
            },
        )

    async def wait_for_result(self, submission: ProviderSubmission, timeout_sec: float) -> ProviderResult:
        prompt_id = submission.provider_job_id or submission.provider_state.get("prompt_id")
        if not prompt_id:
            raise RuntimeError("Missing ComfyUI prompt_id")
        history = await self.client.wait_for_completion(str(prompt_id), timeout_sec)
        image_info = _extract_image_info(history, submission.provider_state.get("workflow_map") or {})
        payload = await self.client.fetch_image_bytes(
            image_info["filename"],
            subfolder=image_info.get("subfolder", ""),
            folder_type=image_info.get("type", "output"),
        )
        generation_id = submission.provider_state.get("generation_id")
        if not generation_id:
            raise RuntimeError("Missing generation_id for ComfyUI artifact persistence")
        ext = Path(image_info["filename"]).suffix.lstrip(".") or "png"
        image_path = await get_artifact_service().persist_bytes(str(generation_id), payload, ext=ext)
        return ProviderResult(
            provider_name="comfyui",
            image_path=image_path,
            provider_job_id=str(prompt_id),
            provider_state={"history": history, "image": image_info},
            metadata={"history": history},
        )

    async def cancel(self, submission: ProviderSubmission) -> None:
        return None

    async def health_check(self) -> bool:
        return bool(settings.comfyui_base_url)

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
        raise RuntimeError("ComfyUI history did not contain outputs")
    images = node_output.get("images") or []
    if not images:
        raise RuntimeError("ComfyUI output did not contain images")
    return images[0]
