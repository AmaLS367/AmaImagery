"""
Domain helpers for image generation.

Provides pure domain logic for validation, safety checks, and prompt processing.
"""

from typing import Any, cast

from app.config import settings
from app.core.logging import lg
from app.core.safety import is_blocked, is_blocked_forced
from app.domain.schemas import GenReq
from app.prompt_hygiene.facade import run_hygiene
from app.utils import prompt_hash

cfg = cast(Any, settings)


class GenerationService:
    """
    Domain helpers for image generation business rules.

    Provides validation, safety checks, and prompt processing without orchestration.
    """

    def __init__(self) -> None:
        pass

    def _validate_request(self, request: GenReq) -> None:
        if request.width > cfg.max_gen_width or request.height > cfg.max_gen_height:
            raise ValueError("Image size too large")

        max_safe = int(cfg.max_steps)
        if int(request.steps) > max_safe:
            raise ValueError(f"Steps too large (>{max_safe})")

        guidance = getattr(request, "guidance_scale", getattr(request, "guidance", 7.5))
        if float(guidance) > cfg.max_guidance:
            raise ValueError("Guidance too large")

        batch_size = getattr(request, "batch", 1)
        if batch_size > cfg.max_batch:
            raise ValueError("Batch too large")

    def _check_safety_policies(self, request: GenReq, user: Any | None) -> None:
        allow_global = cfg.nsfw_allow
        # Global allow is an explicit operator override: generation requests should
        # bypass NSFW blocking entirely, while preserving user-level settings/API.
        if allow_global:
            return

        allow_user = False

        if user is not None:
            settings_blob = getattr(getattr(user, "settings", None), "data", None)
            if isinstance(settings_blob, dict):
                allow_user = bool(settings_blob.get("nsfw_allow", False))

        if not allow_user and is_blocked_forced(request.prompt):
            raise ValueError("Blocked by safety policy.")

        if is_blocked(request.prompt) or is_blocked(request.negative_prompt):
            lg("safety").bind(
                prompt_hash=prompt_hash(request.prompt, request.negative_prompt),
                reason="blocked_by_rules",
            ).error("safety.blocked")
            raise ValueError("Blocked by safety policy.")

    def _device_vram_mb(self) -> int:
        try:
            import torch

            if torch.cuda.is_available():
                try:
                    return int(torch.cuda.get_device_properties(0).total_memory // (1024 * 1024))
                except Exception:
                    return 0
        except Exception:
            return 0
        return 0

    def _effective_max_size(self) -> int:
        vram = self._device_vram_mb()
        cfg_cap = int(getattr(cfg, "max_size", 768))
        if vram == 0:
            return min(cfg_cap, 768)
        if vram <= 4608:
            return min(cfg_cap, 704)
        if vram <= 7168:
            return min(cfg_cap, 896)
        return min(cfg_cap, 1024)

    def _snap64(self, x: int) -> int:
        return max(256, (int(x) // 64) * 64)

    def _process_prompt(self, prompt: str, negative: str, user: Any | None) -> tuple[str, list[tuple[str, str]]]:
        user_id = str(getattr(user, "id", "anon"))
        res = run_hygiene(user_id=user_id, prompt=prompt, negative=negative, mode=None)
        fixed = res.prompt
        corr = [(c.before, c.after) for c in res.report.corrections]
        return fixed, corr

    def _prepare_generation_params(self, request: GenReq, processed_prompt: str) -> dict[str, Any]:
        style = getattr(request, "style", "realistic")

        quality_prefix = "masterpiece, best quality, ultra-detailed"
        if style == "anime":
            style_prefix = "anime style, clean lineart, detailed shading, vibrant colors"
        else:
            style_prefix = "photorealistic, cinematic lighting, detailed skin, depth of field"

        final_prompt = f"{quality_prefix}, {style_prefix}, {processed_prompt}"

        negative_prompt = request.negative_prompt or (
            "bad anatomy, bad hands, missing fingers, extra fingers, extra limbs, poorly drawn face, "
            "deformed, body out of frame, cropped, lowres, blurry, jpeg artifacts, watermark, signature, text, "
            "worst quality, low quality"
        )

        req_w = int(request.width or 768)
        req_h = int(request.height or 1152)

        cap = self._effective_max_size()
        long_side = max(req_w, req_h)
        if long_side > cap:
            scale = cap / float(long_side)
            req_w = int(round(req_w * scale))
            req_h = int(round(req_h * scale))

        w = self._snap64(req_w)
        h = self._snap64(req_h)

        max_safe = int(cfg.max_steps)
        use_steps = min(max_safe, max(24, int(request.steps or 28)))
        use_gs = float(request.guidance_scale if request.guidance_scale is not None else 7.5)

        return {
            "prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "width": w,
            "height": h,
            "steps": use_steps,
            "guidance_scale": use_gs,
            "seed": request.seed,
            "ref_image_b64": request.ref_image_b64,
            "ip_scale": request.ip_scale,
            "style": style,
        }
