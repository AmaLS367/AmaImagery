"""
Image generation service.

Handles the core business logic for AI image generation.
"""

import asyncio
import gc
import traceback
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, cast

import torch
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import lg, logger
from app.domain.models import Generation
from app.domain.schemas import GenReq, GenResp
from app.services.image_service import ImageProcessingService
from app.utils import prompt_hash
from app.prompt_hygiene.facade import run_hygiene

from app.core.safety import is_blocked, is_blocked_forced
from app.core.limits import get_gen_semaphore
from app.inference.pipeline import get_unet_dtype, align_to_unet_dtype

cfg = cast(Any, settings)

class GenerationService:
    """Service for handling image generation requests."""
    
    def __init__(self, db: Session):
        self.db = db
        self.image_service = ImageProcessingService()
        self._setup_autocorrect()    

    def _set_quality_mode(self, pipeline) -> None:
        if hasattr(pipeline, "enable_vae_tiling"):
            pipeline.enable_vae_tiling()
        if hasattr(pipeline, "enable_vae_slicing"):
            pipeline.enable_vae_slicing()

        try:
            if hasattr(pipeline, "enable_model_cpu_offload"):
                pipeline.enable_model_cpu_offload()
        except Exception:
            pass
    
    def _setup_autocorrect(self) -> None:
        pass

    async def generate_image(
        self,
        request: GenReq,
        user: Optional[Any] = None
    ) -> GenResp:
        """
        Generate an image based on the request.
        """
        semaphore = get_gen_semaphore()
        acquired = False
        try:
            gen_limit = float(cfg.generation_timeout_seconds)
            queue_timeout = max(20.0, min(gen_limit - 5.0, gen_limit / 2.0))
            await asyncio.wait_for(semaphore.acquire(), timeout=queue_timeout)
            acquired = True

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
                model_id=cfg.model_id,
                size=[request.width, request.height],
                steps=request.steps,
                guidance_scale=request.guidance_scale,
                ip_scale=request.ip_scale,
                seed=request.seed,
            ).info("generation.requested")

            # Check safety policies
            self._check_safety_policies(request, user)

            # Process prompt
            processed_prompt, corrections = self._process_prompt(
                prompt=request.prompt,
                negative=request.negative_prompt or "",
                user=user,
            )

            # Prepare generation parameters
            generation_params = self._prepare_generation_params(request, processed_prompt)

            # Generate the image
            image = await self._generate_image_async(generation_params)

            # Save the image
            output_path = self.image_service.save_image(image, prompt_hash_value)

            # Save generation metadata to database
            self._save_generation_metadata(request, user, output_path, prompt_hash_value)

            # Log completion
            gen_logger.bind(
                phase="completed",
                prompt_hash=prompt_hash_value,
                output_path=output_path,
            ).success("generation.completed")

            # Create signed URL if enabled
            signed_url = self._create_signed_url(output_path) if cfg.file_signing_enabled else None

            return GenResp(
                ok=True,
                path=Path(output_path).name,
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
        """Validate generation request parameters."""
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
        """Check safety policies for the request."""
        
        # Determine if NSFW is allowed
        allow_global = cfg.nsfw_allow
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
        """
        Run prompt hygiene via facade.
        Returns: (possibly updated prompt, list of (before, after) corrections)
        """
        user_id = str(getattr(user, "id", "anon"))
        res = run_hygiene(user_id=user_id, prompt=prompt, negative=negative, mode=None)
        fixed = res.prompt
        corr = [(c.before, c.after) for c in res.report.corrections]
        return fixed, corr
    
    def _prepare_generation_params(self, request: GenReq, processed_prompt: str) -> Dict[str, Any]:
        """Prepare parameters for image generation."""
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

    
    async def _generate_image_async(self, params: Dict[str, Any]) -> Image.Image:
        """ Asynchronously generate an image """
        gen_log = lg("generation")
        use_ip = bool(params.get("ref_image_b64"))
        gen_log.debug(
            "generate_async.start",
            extra={
                "use_ip": use_ip,
                "w": int(params.get("width", 0)),
                "h": int(params.get("height", 0)),
                "steps": int(params.get("steps", 0)),
                "gs": float(params.get("guidance_scale", 0.0)),
                "ip_scale": params.get("ip_scale"),
            },
        )

        try:
            from app.inference.pipeline import get_pipeline, get_pipeline_with_ip
            pipeline = get_pipeline_with_ip() if use_ip else get_pipeline()
            
            self._set_quality_mode(pipeline)
            steps = int(params.get("steps", 28) or 28)
            style = params.get("style") or ""

        except Exception as e:
            # if IP-adapter failed to load fallback to regular pipeline
            lg("app").bind(event="ip_adapter.unavailable", reason=str(e)).warning("ip_adapter.unavailable")
            from app.inference.pipeline import get_pipeline
            pipeline = get_pipeline()
            use_ip = False

        try:
            device = next(pipeline.unet.parameters()).device  # type: ignore[attr-defined]
        except Exception:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        gen_log.debug(
            "pipeline.ready",
            extra={"device": str(device), "dtype": str(getattr(pipeline, "dtype", None))},
        )

        generator = None
        if params.get("seed") is not None:
            try:
                generator = torch.Generator(device=str(device)).manual_seed(int(params["seed"]))
            except Exception:
                generator = None

        unet_dtype = get_unet_dtype(pipeline)

        if getattr(pipeline, "unet", None) is not None:
            pipeline.unet.to(device=device, dtype=unet_dtype)
        if getattr(pipeline, "vae", None) is not None:
            pipeline.vae.to(device=device, dtype=unet_dtype)
        if getattr(pipeline, "text_encoder", None) is not None:
            if torch.cuda.is_available():
                pipeline.text_encoder.to(device="cpu", dtype=torch.float32)
            else:
                pipeline.text_encoder.to(device=device, dtype=torch.float32)

        ctx = (torch.autocast(device_type=device.type, dtype=unet_dtype)
            if device.type == "cuda" else nullcontext())

        extra: Dict[str, Any] = {}
        if use_ip and params.get("ref_image_b64"):
            try:
                ref_image = self.image_service.prepare_reference_image(params["ref_image_b64"], target_size=512)

                ip_scale = 0.55 if params.get("ip_scale") is None else float(params["ip_scale"])
                ip_scale = max(0.0, min(1.5, ip_scale))

                if hasattr(pipeline, "set_ip_adapter_scale"):
                    try:
                        pipeline.set_ip_adapter_scale(ip_scale)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                    
                # --- begin: guard devices before IP encoding ---
                try:
                    dev = next(pipeline.unet.parameters()).device

                    # text_encoder on same device as UNet
                    if hasattr(pipeline, "text_encoder") and pipeline.text_encoder is not None:
                        pipeline.text_encoder.to(dev)

                    # keep vision encoder on CPU/fp32 (minimum VRAM, no mixed types)
                    if hasattr(pipeline, "image_encoder") and pipeline.image_encoder is not None:
                        pipeline.image_encoder.to(device="cpu", dtype=torch.float32)
                except Exception:
                    logger.exception("ip_adapter_device_guard_failed")
                # --- end: guard devices before IP encoding ---

                image_embeds = None

                # Priority: native encode_image to avoid breaking diffusers/ip-adapter signature
                if hasattr(pipeline, "encode_image"):
                    image_embeds = pipeline.encode_image(
                        ref_image, device=device, num_images_per_prompt=1
                    )
                    # Make embeds consistent with UNet precision
                    try:
                        image_embeds = align_to_unet_dtype(image_embeds.to(device=device), pipeline)
                    except Exception:
                        pass

                # Fallback: direct encoder (CLIP)
                elif hasattr(pipeline, "image_encoder"):
                    enc = pipeline.image_encoder  # type: ignore[attr-defined]
                    proc = getattr(pipeline, "image_processor", None) or getattr(pipeline, "feature_extractor", None)
                    if proc is None:
                        raise RuntimeError("IP-Adapter: image processor not found")
                    with torch.inference_mode():
                        proc_out = proc(images=ref_image, return_tensors="pt")
                        # keep preprocessor and encoder strictly on CPU/FP32
                        pixel = proc_out["pixel_values"].to(device="cpu", dtype=torch.float32)

                        enc = enc.to(device="cpu", dtype=torch.float32).eval()
                        with torch.inference_mode():
                            image_embeds = enc(pixel)

                        # align embeds with UNet device and dtype to avoid mixed precision issues
                        image_embeds = image_embeds.to(
                            device=device,
                            dtype=unet_dtype
                        )


                if image_embeds is None:
                    raise RuntimeError("IP-Adapter: failed to prepare image embeddings")

                gen_log.debug(
                    "ip_adapter.embeds_ready",
                    extra={
                        "embeds_type": type(image_embeds).__name__,
                        "has_cuda": torch.cuda.is_available(),
                        "embeds_device": str(getattr(image_embeds, "device", "n/a")),
                        "embeds_shape": tuple(getattr(image_embeds, "shape", ())),
                        "ip_scale": ip_scale,
                    },
                )

                # Use modern keys (image_embeds). Don't use old ones (ip_adapter_image/ip_adapter_scale).
                extra["image_embeds"] = image_embeds

            except Exception:
                traceback.print_exc()
                logger.exception("ip_adapter.prepare_failed", extra={"event_type": "app"})
                # If embeddings failed softly fallback to generation without IP (to get stack further)
                use_ip = False
                extra.clear()

        use_width = int(params.get("width", 512))
        use_height = int(params.get("height", 512))
        use_steps = int(params.get("steps", 20))
        
        _fixed_timesteps = None
        try:
            if not bool(getattr(pipeline.scheduler.config, "use_karras_sigmas", False)):
                pipeline.scheduler.set_timesteps(use_steps, device=device)
                _fixed_timesteps = pipeline.scheduler.timesteps
        except Exception:
            _fixed_timesteps = None

    
        if device.type == "cpu":
            max_side = 640
            if max(use_width, use_height) > max_side:
                ratio = max_side / float(max(use_width, use_height))
                use_width = int(round(use_width * ratio / 8) * 8)
                use_height = int(round(use_height * ratio / 8) * 8)

        soft_deadline = time.time() + float(cfg.generation_timeout_seconds) - 1.0

        def timeout_callback(step, timestep=None, latents=None):
            if time.time() > soft_deadline:
                raise RuntimeError("generation_timeout")

        def sync_generation():
            with torch.inference_mode(), ctx:
                call_kwargs = dict(
                    prompt=params.get("prompt"),
                    negative_prompt=params.get("negative_prompt"),
                    num_inference_steps=use_steps,
                    width=use_width,
                    height=use_height,
                    guidance_scale=float(params.get("guidance_scale", 7.0)),
                    generator=generator,
                    noise_offset=0.02,
                )

                if _fixed_timesteps is not None:
                    call_kwargs["timesteps"] = _fixed_timesteps

                try:
                    _effective = {"n": 0}

                    def _on_step_end(pipe, step, timestep, callback_kwargs):
                        _effective["n"] += 1
                        if time.time() > soft_deadline:
                            raise RuntimeError("generation_timeout")
                        return {}

                    call_kwargs.pop("callback", None)
                    call_kwargs.pop("callback_steps", None)

                    call_kwargs["callback_on_step_end"] = _on_step_end
                    call_kwargs["callback_on_step_end_tensor_inputs"] = []

                    res = cast(Any, pipeline)(
                        **call_kwargs,
                        **({} if not use_ip else extra),
                    )

                    return res

                except TypeError:
                    # fallback for old diffusers versions without new API
                    call_kwargs.pop("noise_offset", None)
                    call_kwargs.pop("timesteps", None)
                    call_kwargs.pop("callback_on_step_end", None)
                    call_kwargs.pop("callback_on_step_end_tensor_inputs", None)
                    return cast(Any, pipeline)(
                        **call_kwargs,
                        **({} if not use_ip else extra),
                    )

        gen_log.debug(
            "pipeline.call",
            extra={
                "w": use_width,
                "h": use_height,
                "steps": use_steps,
                "gs": float(params.get("guidance_scale", 7.0)),
                "with_ip": use_ip,
            },
        )

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(sync_generation),
                timeout=float(cfg.generation_timeout_seconds) + 2.0,
            )
        except asyncio.TimeoutError:
            traceback.print_exc()
            logger.exception("generation.timeout", extra={"event_type": "app"})
            raise
        except RuntimeError as e:
            traceback.print_exc()
            logger.exception("generation.runtime_error", extra={"event_type": "app", "msg": str(e)})
            msg = str(e).lower()
            if "generation_timeout" in msg:
                raise RuntimeError("Generation timed out")
            if "out of memory" in msg or ("cuda" in msg and "memory" in msg):
                raise ValueError("CUDA out of memory: reduce width/height to 512 or decrease steps")
            raise
        except Exception as e:
            traceback.print_exc()
            logger.exception("generation.exception", extra={"event_type": "app", "where": "pipeline.call", "msg": str(e)})
            raise
        finally:
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            gc.collect()

        try:
            image = self.image_service.extract_image_from_result(result)
            gen_log.info(
                "pipeline.ok",
                extra={"mode": getattr(image, "mode", None), "size": getattr(image, "size", None)},
            )
            return image
        except Exception as e:
            traceback.print_exc()
            logger.exception("generation.extract_failed", extra={"event_type": "app", "msg": str(e)})
            raise

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
