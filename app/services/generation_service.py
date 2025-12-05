"""
Image generation service.

Handles the core business logic for AI image generation.
"""

import asyncio
import traceback
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, cast

import torch
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import lg, logger
from app.domain.models import Generation
from app.domain.providers import GenerationRequest, ProviderRegistry
from app.domain.schemas import GenReq, GenResp
from app.services.image_service import ImageProcessingService
from app.utils import prompt_hash
from app.prompt_hygiene.facade import run_hygiene

from app.core.safety import is_blocked, is_blocked_forced
from app.core.limits import get_gen_semaphore

cfg = cast(Any, settings)

class GenerationService:
    """
    Orchestrates image generation by coordinating provider selection, prompt processing, and result persistence.
    """
    
    def __init__(self, db: Session, provider_registry: Optional[ProviderRegistry] = None):
        self.db = db
        self.image_service = ImageProcessingService()
        self.provider_registry = provider_registry
        self._setup_autocorrect()    

    def _setup_autocorrect(self) -> None:
        pass

    async def generate_image(
        self,
        request: GenReq,
        user: Optional[Any] = None
    ) -> GenResp:
        semaphore = get_gen_semaphore()
        acquired = False
        try:
            gen_limit = float(cfg.generation_timeout_seconds)
            queue_timeout = max(20.0, min(gen_limit - 5.0, gen_limit / 2.0))
            await asyncio.wait_for(semaphore.acquire(), timeout=queue_timeout)
            acquired = True

            self._validate_request(request)

            gen_logger = lg("generation")
            prompt_logger = lg("prompt")

            prompt_hash_value = prompt_hash(request.prompt, request.negative_prompt)

            gen_logger.bind(
                phase="requested",
                model_id=cfg.model_id,
                size=[request.width, request.height],
                steps=request.steps,
                guidance_scale=request.guidance_scale,
                ip_scale=request.ip_scale,
                seed=request.seed,
            ).info("generation.requested")

            self._check_safety_policies(request, user)

            processed_prompt, corrections = self._process_prompt(
                prompt=request.prompt,
                negative=request.negative_prompt or "",
                user=user,
            )

            generation_params = self._prepare_generation_params(request, processed_prompt)

            if self.provider_registry is None:
                from app.domain.providers import get_provider_registry
                provider_registry = get_provider_registry()
            else:
                provider_registry = self.provider_registry
            
            provider = provider_registry.get_default()

            gen_request = GenerationRequest(
                prompt=generation_params["prompt"],
                negative_prompt=generation_params.get("negative_prompt"),
                seed=generation_params.get("seed"),
                width=generation_params["width"],
                height=generation_params["height"],
                steps=generation_params.get("steps"),
                guidance_scale=generation_params.get("guidance_scale"),
                ref_image_b64=generation_params.get("ref_image_b64"),
                ip_scale=generation_params.get("ip_scale"),
                style=generation_params.get("style", "anime"),
            )

            result = await provider.generate(gen_request)

            output_path = result.image_path

            self._save_generation_metadata(request, user, output_path, prompt_hash_value)

            gen_logger.bind(
                phase="completed",
                prompt_hash=prompt_hash_value,
                output_path=output_path,
            ).success("generation.completed")

            signed_url = self._create_signed_url(output_path) if cfg.file_signing_enabled else None

            return GenResp(
                ok=True,
                path=Path(result.image_path).name,
                prompt_hash=prompt_hash_value,
                corrections=corrections,
                exp=signed_url["exp"] if signed_url else None,
                sig=signed_url["sig"] if signed_url else None,
            )

        except Exception:
            traceback.print_exc()
            logger.exception(
                "generation.failed",
                extra={
                    "event_type": "app",
                    "scope": "generation",
                },
            )
            raise
        finally:
            if acquired:
                try:
                    semaphore.release()
                except Exception:
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
    
    def _check_safety_policies(self, request: GenReq, user: Optional[Any]) -> None:
        allow_global = cfg.nsfw_allow
        allow_user = True
        
        if user is not None and hasattr(user, "nsfw_allow"):
            allow_user = bool(user.nsfw_allow)
        
        if not allow_global:
            if is_blocked_forced(request.prompt):
                raise ValueError("Blocked by safety policy.")
        else:
            if not allow_user and is_blocked_forced(request.prompt):
                raise ValueError("Blocked by safety policy.")
        
        if is_blocked(request.prompt) or is_blocked(request.negative_prompt):
            lg("safety").bind(
                prompt_hash=prompt_hash(request.prompt, request.negative_prompt),
                reason="blocked_by_rules",
            ).error("safety.blocked")
            raise ValueError("Blocked by safety policy.")

    
    def _device_vram_mb(self) -> int:
        if torch.cuda.is_available():
            try:
                return int(torch.cuda.get_device_properties(0).total_memory // (1024 * 1024))
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
    
    def _process_prompt(self, prompt: str, negative: str, user: Optional[Any]) -> Tuple[str, List[Tuple[str, str]]]:
        user_id = str(getattr(user, "id", "anon"))
        res = run_hygiene(user_id=user_id, prompt=prompt, negative=negative, mode=None)
        fixed = res.prompt
        corr = [(c.before, c.after) for c in res.report.corrections]
        return fixed, corr
    
    def _prepare_generation_params(self, request: GenReq, processed_prompt: str) -> Dict[str, Any]:
        style = getattr(request, 'style', 'anime')

        quality_prefix = "masterpiece, best quality, ultra-detailed"
        if style == 'anime':
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

    def _save_generation_metadata(
        self, 
        request: GenReq, 
        user: Optional[Any], 
        output_path: str, 
        prompt_hash_value: str
    ) -> None:
        prompt_blob = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt
        }
        
        params_blob = {
            "width": request.width,
            "height": request.height,
            "steps": request.steps,
            "guidance_scale": request.guidance_scale,
            "ip_scale": request.ip_scale,
            "seed": request.seed,
            "model_id": cfg.model_id,
        }
        
        generation = Generation(
            user_id=getattr(user, "id", None),
            prompt=prompt_blob,
            params=params_blob,
            image_path=output_path,
        )
        
        self.db.add(generation)
        self.db.commit()
    
    def _create_signed_url(self, output_path: str) -> Dict[str, Any]:
        from app.files.signing import make_signature
        import time
        
        exp = int(time.time()) + int(cfg.file_download_ttl_sec)
        sig = make_signature(Path(output_path).name, exp)
        
        return {
            "path": Path(output_path).name,
            "exp": exp,
            "sig": sig
        }
