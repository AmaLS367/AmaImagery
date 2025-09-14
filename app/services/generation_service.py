"""
Image generation service.

Handles the core business logic for AI image generation.
"""

import asyncio
import gc
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import torch
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.logging_setup import lg, logger, save_prompt_raw
from app.models import Generation
from app.schemas import GenReq, GenResp
from app.services.image_service import ImageProcessingService
from app.services.safety_service import SafetyService
from app.utils import out_path, prompt_hash
from app.utils_01.spell import build_spell, correct_prompt


class GenerationService:
    """Service for handling image generation requests."""
    
    def __init__(self, db: Session):
        self.db = db
        self.image_service = ImageProcessingService()
        self.safety_service = SafetyService()
        self._setup_autocorrect()
    
    def _setup_autocorrect(self) -> None:
        """Setup autocorrect functionality."""
        import os
        self.autocorrect_mode = os.getenv("AUTOCORRECT", "on")
        self.spell_checker = build_spell(extra_words=[
            "bokeh", "karras", "euler", "dpmsolver", "lora", "vae",
            "anime", "photorealistic", "cinematic", "volumetric",
        ])
        self.whitelist = {"sd15", "sdxl", "lcm", "lora", "vae"}
    
    async def generate_image(
        self, 
        request: GenReq, 
        user: Optional[Any] = None
    ) -> GenResp:
        """
        Generate an image based on the request.
        
        Args:
            request: Generation request parameters
            user: Optional authenticated user
            
        Returns:
            GenerationResponse with generated image details
        """
        # Validate request parameters
        self._validate_request(request)
        
        # Setup logging
        gen_logger = lg("generation")
        prompt_logger = lg("prompt")
        
        # Generate prompt hash
        prompt_hash_value = prompt_hash(request.prompt, request.negative_prompt)
        
        # Log generation request
        gen_logger.bind(
            phase="requested",
            model_id=settings.model_id,
            size=[request.width, request.height],
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            ip_scale=request.ip_scale,
            seed=request.seed,
        ).info("generation.requested")
        
        # Check safety policies
        self._check_safety_policies(request, user)
        
        # Process prompt
        processed_prompt, corrections = self._process_prompt(request.prompt)
        
        # Prepare generation parameters
        generation_params = self._prepare_generation_params(request, processed_prompt)
        
        # Generate the image
        image = await self._generate_image_async(generation_params)
        
        # Save the image
        output_path = self._save_image(image, prompt_hash_value)
        
        # Save generation metadata to database
        self._save_generation_metadata(request, user, output_path, prompt_hash_value)
        
        # Log completion
        gen_logger.bind(
            phase="completed",
            prompt_hash=prompt_hash_value,
            output_path=output_path,
            device=settings.device,
        ).success("generation.completed")
        
        # Create signed URL if enabled
        signed_url = self._create_signed_url(output_path) if settings.file_signing_enabled else None
        
        return GenResp(
            ok=True,
            path=Path(output_path).name,
            prompt_hash=prompt_hash_value,
            corrections=corrections,
            exp=signed_url["exp"] if signed_url else None,
            sig=signed_url["sig"] if signed_url else None,
        )
    
    def _validate_request(self, request: GenReq) -> None:
        """Validate generation request parameters."""
        if request.width > settings.max_gen_width or request.height > settings.max_gen_height:
            raise ValueError("Image size too large")
        
        if request.steps > settings.max_gen_steps:
            raise ValueError("Steps too large")
        
        guidance = getattr(request, "guidance_scale", getattr(request, "guidance", 7.5))
        if float(guidance) > settings.max_guidance:
            raise ValueError("Guidance too large")
        
        batch_size = getattr(request, "batch", 1)
        if batch_size > settings.max_batch:
            raise ValueError("Batch too large")
    
    def _check_safety_policies(self, request: GenReq, user: Optional[Any]) -> None:
        """Check safety policies for the request."""
        from app.safety import is_blocked, is_blocked_forced
        
        # Determine if NSFW is allowed
        allow_global = settings.nsfw_allow
        allow_user = True
        
        if user is not None and hasattr(user, "nsfw_allow"):
            allow_user = bool(user.nsfw_allow)
        
        # Apply safety checks
        if not allow_global:
            # Global ban: forced blocklist applies to everyone
            if is_blocked_forced(request.prompt):
                raise ValueError("Blocked by safety policy.")
        else:
            # Global allow: apply blocklist only to users with NSFW disabled
            if not allow_user and is_blocked_forced(request.prompt):
                raise ValueError("Blocked by safety policy.")
        
        # Check regular blocklist
        if is_blocked(request.prompt) or is_blocked(request.negative_prompt):
            lg("error").bind(
                scope="safety",
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
        cfg_cap = int(getattr(settings, "max_size", 768))
        if vram == 0:
            return min(cfg_cap, 768)
        if vram <= 4608:
            return min(cfg_cap, 512)
        if vram <= 7168:
            return min(cfg_cap, 640)
        return min(cfg_cap, 768)

    def _snap64(self, x: int) -> int:
        return max(256, (int(x) // 64) * 64)


    
    def _process_prompt(self, prompt: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Process and correct the prompt."""
        corrections = []
        
        if self.autocorrect_mode != "off":
            fixed, corrections = correct_prompt(
                prompt, 
                self.spell_checker, 
                whitelist=self.whitelist
            )
            if self.autocorrect_mode == "on":
                prompt = fixed
        
        return prompt, corrections
    
    def _prepare_generation_params(self, request: GenReq, processed_prompt: str) -> Dict[str, Any]:
        """Prepare parameters for image generation."""
        # Apply style
        style = getattr(request, 'style', 'anime')
        if style == 'anime':
            final_prompt = f"anime, illustration, clean lineart, cel shading, vibrant colors, key visual, {processed_prompt}"
        else:
            final_prompt = f"photorealistic, natural lighting, detailed film look, {processed_prompt}"
        
        # Prepare negative prompt
        negative_prompt = request.negative_prompt or (
            "close-up, cropped, zoomed in, out of frame, bad composition, "
            "lowres, blurry, jpeg artifacts, extra fingers, extra limbs, bad hands, worst quality, low quality"
        )

        cap = self._effective_max_size()
        w = self._snap64(min(request.width, cap))
        h = self._snap64(min(request.height, cap))

        return {
            "prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "width": w,
            "height": h,
            "steps": min(request.steps, settings.max_gen_steps),
            "guidance_scale": request.guidance_scale,
            "seed": request.seed,
            "ref_image_b64": request.ref_image_b64,
            "ip_scale": request.ip_scale,
        }
    
    async def _generate_image_async(self, params: Dict[str, Any]) -> Image.Image:
        """Generate the image asynchronously."""
        from app.inference.pipeline import get_pipeline, get_pipeline_with_ip
        
        # Get the appropriate pipeline
        use_ip = bool(params["ref_image_b64"])
        pipeline = get_pipeline_with_ip() if use_ip else get_pipeline()
        
        # Setup device and generator
        device = next(pipeline.unet.parameters()).device
        generator = None
        if params["seed"] is not None:
            generator = torch.Generator(device=str(device)).manual_seed(int(params["seed"]))
        
        # Setup autocast context
        ctx = (
            torch.autocast("cuda", dtype=torch.float16) 
            if device.type == "cuda" 
            else nullcontext()
        )
        
        # Prepare extra parameters
        extra = {}
        if use_ip and params["ref_image_b64"]:
            ref_image = self.image_service.prepare_reference_image(
                params["ref_image_b64"], 
                target_size=512
            )
            extra["ip_adapter_image"] = ref_image
            
            # Clamp ip_scale to valid range
            ip_scale = 0.6 if params["ip_scale"] is None else float(params["ip_scale"])
            ip_scale = max(0.0, min(1.5, ip_scale))
            extra["ip_adapter_scale"] = ip_scale
        
        # CPU-автосейф: если устройство CPU — снижаем требования, чтобы уложиться в лимит
        use_width = int(params["width"])
        use_height = int(params["height"])
        use_steps = int(params["steps"])
        if device.type == "cpu":
            # ограничиваем геометрию и шаги для CPU
            max_side = 640
            if max(use_width, use_height) > max_side:
                ratio = max_side / float(max(use_width, use_height))
                use_width = int(round(use_width * ratio / 8) * 8)
                use_height = int(round(use_height * ratio / 8) * 8)
            if use_steps > 24:
                use_steps = 22

        # Setup timeout callback с мягким запасом
        soft_deadline = time.time() + settings.generation_timeout_sec - 1.0

        def timeout_callback(step, timestep=None, latents=None):
            if time.time() > soft_deadline:
                raise RuntimeError("generation_timeout")

        # Generate the image
        def sync_generation():
            with torch.inference_mode(), ctx:
                return pipeline(
                    prompt=params["prompt"],
                    negative_prompt=params["negative_prompt"],
                    num_inference_steps=use_steps,
                    width=use_width,
                    height=use_height,
                    guidance_scale=params["guidance_scale"],
                    generator=generator,
                    callback=timeout_callback,
                    callback_steps=1,
                    **extra,
                )
        
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(sync_generation),
                timeout=settings.generation_timeout_sec + 2,
            )
            
            # Extract image from result
            image = self.image_service.extract_image_from_result(result)
            return image
            
        except asyncio.TimeoutError:
            raise RuntimeError("Generation timed out")
        except RuntimeError as e:
            msg = str(e).lower()
            if "generation_timeout" in msg:
                raise RuntimeError("Generation timed out")
            if "out of memory" in msg or "cuda" in msg and "memory" in msg:
                raise ValueError("CUDA out of memory: снизь width/height до 512 или уменьшай steps")
            raise
        finally:
            # Cleanup GPU memory
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            gc.collect()
    
    def _save_image(self, image: Image.Image, prompt_hash_value: str) -> str:
        """Save the generated image to disk."""
        output_path = out_path(prompt_hash_value)
        image.save(output_path)
        return output_path
    
    def _save_generation_metadata(
        self, 
        request: GenReq, 
        user: Optional[Any], 
        output_path: str, 
        prompt_hash_value: str
    ) -> None:
        """Save generation metadata to database."""
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
            "model_id": getattr(request, "model_id", None),
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
        """Create a signed URL for the generated image."""
        from app.files.signing import make_signature
        import time
        
        exp = int(time.time()) + int(settings.file_download_ttl_sec)
        sig = make_signature(Path(output_path).name, exp)
        
        return {
            "path": Path(output_path).name,
            "exp": exp,
            "sig": sig
        }
