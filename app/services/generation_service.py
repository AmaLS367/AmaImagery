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
from typing import Optional, Tuple, List, Dict, Any

import torch, os
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import lg, logger
from app.domain.models import Generation
from app.domain.schemas import GenReq, GenResp
from app.services.image_service import ImageProcessingService
from app.utils import out_path, prompt_hash
from app.utils_01.spell import build_spell, correct_prompt
from app.core.safety import is_blocked, is_blocked_forced

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

    def _choose_hq_scheduler(self, pipeline, steps: int) -> None:
        """
        DPM++ 2M Karras — даёт заметный прирост качества и чувствительность к количеству шагов.
        """
        try:
            from diffusers import DPMSolverMultistepScheduler # type: ignore[reportMissingImports]
            pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                pipeline.scheduler.config,
                algorithm_type="sde-dpmsolver++",
                use_karras_sigmas=True,
                solver_order=2,
            )
        except Exception:
            pass


    
    def _setup_autocorrect(self) -> None:
        """Setup autocorrect functionality."""
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
        """
        try:
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

        except Exception:
            # Печатаем полноценный traceback в dev и логируем всегда
            traceback.print_exc()
            logger.exception(
                "generation.failed",
                extra={
                    "event_type": "app",
                    "scope": "generation",
                },
            )
            # Ничего не скрываем тут — пусть поднимется выше до dev middleware
            raise

    
    def _validate_request(self, request: GenReq) -> None:
        """Validate generation request parameters."""
        if request.width > settings.max_gen_width or request.height > settings.max_gen_height:
            raise ValueError("Image size too large")
        
        max_safe = 256
        if int(request.steps) > max_safe:
            raise ValueError(f"Steps too large (>{max_safe})")
        
        guidance = getattr(request, "guidance_scale", getattr(request, "guidance", 7.5))
        if float(guidance) > settings.max_guidance:
            raise ValueError("Guidance too large")
        
        batch_size = getattr(request, "batch", 1)
        if batch_size > settings.max_batch:
            raise ValueError("Batch too large")
    
    def _check_safety_policies(self, request: GenReq, user: Optional[Any]) -> None:
        """Check safety policies for the request."""
        
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
            return min(cfg_cap, 704)
        if vram <= 7168:
            return min(cfg_cap, 896)
        return min(cfg_cap, 1024)


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

        # желаемое базовое соотношение 2:3 по умолчанию
        req_w = int(request.width or 768)
        req_h = int(request.height or 1152)

        cap = self._effective_max_size()
        # масштабирование по длинной стороне с сохранением пропорций
        long_side = max(req_w, req_h)
        if long_side > cap:
            scale = cap / float(long_side)
            req_w = int(round(req_w * scale))
            req_h = int(round(req_h * scale))

        w = self._snap64(req_w)
        h = self._snap64(req_h)

        # шаги и гайд
        use_steps = max(24, int(request.steps or 28))
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

        # Получаем пайплайн
        try:
            from app.inference.pipeline import get_pipeline, get_pipeline_with_ip  # импорт локальной фабрики
            pipeline = get_pipeline_with_ip() if use_ip else get_pipeline()
            
            self._set_quality_mode(pipeline)
            steps = int(params.get("steps", 28) or 28)
            style = params.get("style") or ""
            self._choose_hq_scheduler(pipeline, steps)

        except Exception as e:
            # если IP-адаптер не поднялся — даём фолбэк на обычный пайплайн
            lg("app").bind(event="ip_adapter.unavailable", reason=str(e)).warning("ip_adapter.unavailable")
            from app.inference.pipeline import get_pipeline
            pipeline = get_pipeline()
            use_ip = False

        # Девайс/генератор
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

        # Жёсткая синхронизация типов/девайсов перед вызовом
        try:
            unet_dtype = next(pipeline.unet.parameters()).dtype
        except Exception:
            unet_dtype = torch.float16 if device.type == "cuda" else torch.float32

        if getattr(pipeline, "unet", None) is not None:
            pipeline.unet.to(device=device, dtype=unet_dtype)
        if getattr(pipeline, "vae", None) is not None:
            pipeline.vae.to(device=device, dtype=unet_dtype)
        if getattr(pipeline, "text_encoder", None) is not None:
            if torch.cuda.is_available():
                pipeline.text_encoder.to(device="cpu", dtype=torch.float32)
            else:
                pipeline.text_encoder.to(device=device, dtype=torch.float32)


        # Если есть заранее подготовленные эмбеддинги IP-Adapter — привести к dtype UNet
        if use_ip and "image_embeds" in locals():
            try:
                image_embeds = image_embeds.to(device=device, dtype=unet_dtype)
            except Exception:
                pass

        ctx = (torch.autocast(device_type=device.type, dtype=unet_dtype)
            if device.type == "cuda" else nullcontext())

        # Подготовка IP-эмбедов, если надо
        extra: Dict[str, Any] = {}
        if use_ip and params.get("ref_image_b64"):
            try:
                ref_image = self.image_service.prepare_reference_image(params["ref_image_b64"], target_size=512)

                # масштаб влияния
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

                    # text_encoder на том же девайсе, что и UNet
                    if hasattr(pipeline, "text_encoder") and pipeline.text_encoder is not None:
                        pipeline.text_encoder.to(dev)

                    # vision encoder держим на CPU/fp32 (минимум VRAM, без микса типов)
                    if hasattr(pipeline, "image_encoder") and pipeline.image_encoder is not None:
                        pipeline.image_encoder.to(device="cpu", dtype=torch.float32)
                except Exception:
                    logger.exception("ip_adapter_device_guard_failed")
                # --- end: guard devices before IP encoding ---

                image_embeds = None

                # Приоритет: нативный encode_image, чтобы у diffusers/ip-adapter не ломалась сигнатура
                if hasattr(pipeline, "encode_image"):
                    image_embeds = pipeline.encode_image(
                        ref_image, device=device, num_images_per_prompt=1
                    )
                    # Приведение к dtype UNet гарантирует согласованность с attention-проекциями
                    try:
                        image_embeds = image_embeds.to(device=device, dtype=unet_dtype)
                    except Exception:
                        pass

                # Фолбэк: прямой энкодер (CLIP)
                elif hasattr(pipeline, "image_encoder"):
                    enc = pipeline.image_encoder  # type: ignore[attr-defined]
                    proc = getattr(pipeline, "image_processor", None) or getattr(pipeline, "feature_extractor", None)
                    if proc is None:
                        raise RuntimeError("IP-Adapter: image processor not found")
                    with torch.inference_mode():
                        proc_out = proc(images=ref_image, return_tensors="pt")
                        # держим препроцесс и энкодер строго на CPU/FP32
                        pixel = proc_out["pixel_values"].to(device="cpu", dtype=torch.float32)

                        enc = enc.to(device="cpu", dtype=torch.float32).eval()
                        with torch.inference_mode():
                            image_embeds = enc(pixel)

                        # а уже готовые эмбеды переносим к UNet (его девайс/тип)
                        image_embeds = image_embeds.to(
                            device=device,
                            dtype=getattr(pipeline, "dtype", torch.float16)
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

                # Используем современные ключи (image_embeds). Старые (ip_adapter_image/ip_adapter_scale) не суём.
                extra["image_embeds"] = image_embeds

            except Exception:
                traceback.print_exc()
                logger.exception("ip_adapter.prepare_failed", extra={"event_type": "app"})
                # Если эмбеды не удалось — мягко откатываемся на генерацию без IP (чтобы получить стек дальше)
                use_ip = False
                extra.clear()

        # Ограничения для CPU, если вдруг
        use_width = int(params.get("width", 512))
        use_height = int(params.get("height", 512))
        use_steps = int(params.get("steps", 20))
        
        # фиксируем timesteps только если Karras-сигмы выключены
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

        # Таймаут мягкий через callback
        soft_deadline = time.time() + getattr(settings, "generation_timeout_sec", 60) - 1.0

        def timeout_callback(step, timestep=None, latents=None):
            if time.time() > soft_deadline:
                raise RuntimeError("generation_timeout")

        # Вызов пайплайна
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

                    # deadline проверяем здесь, т.к. старый callback удаляем
                    def _on_step_end(pipe, step, timestep, callback_kwargs):
                        _effective["n"] += 1
                        if time.time() > soft_deadline:
                            raise RuntimeError("generation_timeout")
                        return {}

                    # убираем старые ключи
                    call_kwargs.pop("callback", None)          # старый timeout_callback больше не нужен
                    call_kwargs.pop("callback_steps", None)

                    call_kwargs["callback_on_step_end"] = _on_step_end
                    call_kwargs["callback_on_step_end_tensor_inputs"] = []

                    res = pipeline(
                        **call_kwargs,
                        **({} if not use_ip else extra),
                    )

                    # lg("generation").bind(phase="steps", asked=use_steps, effective=_effective["n"]).info("steps.effective")
                    return res  # ← ВАЖНО: вернуть результат

                except TypeError:
                    # откат для старых версий diffusers без нового API
                    call_kwargs.pop("noise_offset", None)
                    call_kwargs.pop("timesteps", None)
                    call_kwargs.pop("callback_on_step_end", None)
                    call_kwargs.pop("callback_on_step_end_tensor_inputs", None)
                    return pipeline(
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
                timeout=getattr(settings, "generation_timeout_sec", 60) + 2,
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
                raise ValueError("CUDA out of memory: снизь width/height до 512 или уменьшай steps")
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

        # Извлекаем изображение
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
