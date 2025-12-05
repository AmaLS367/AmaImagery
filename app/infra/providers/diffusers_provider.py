"""
Diffusers-based image generation provider implementation.

Wraps diffusers pipeline to implement IImageProvider interface.
"""

import asyncio
import gc
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, Optional, cast

import torch
from PIL import Image

from app.config import settings
from app.core.logging import lg, logger
from app.domain.providers.base import GenerationRequest, GenerationResult, IImageProvider
from app.inference.pipeline import get_unet_dtype, align_to_unet_dtype
from app.services.image_service import ImageProcessingService


class DiffusersProvider:
    """
    Diffusers-based provider that isolates application code from diffusers-specific implementation details.
    
    Handles device management, dtype alignment, IP-Adapter setup, and timeout enforcement.
    """
    
    def __init__(
        self,
        get_pipeline_fn: Optional[Callable[[], Any]] = None,
        get_pipeline_with_ip_fn: Optional[Callable[[], Any]] = None,
        image_service: Optional[ImageProcessingService] = None,
    ):
        if get_pipeline_fn is None:
            from app.inference.pipeline import get_pipeline
            self._get_pipeline: Callable[[], Any] = get_pipeline
        else:
            self._get_pipeline = get_pipeline_fn
        
        if get_pipeline_with_ip_fn is None:
            from app.inference.pipeline import get_pipeline_with_ip
            self._get_pipeline_with_ip: Callable[[], Any] = get_pipeline_with_ip
        else:
            self._get_pipeline_with_ip = get_pipeline_with_ip_fn
        
        self._image_service = image_service or ImageProcessingService()
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        May raise RuntimeError on generation timeout or device errors.
        Raises ValueError if request parameters are invalid at provider level.
        """
        gen_log = lg("generation")
        use_ip = bool(request.ref_image_b64)
        
        try:
            pipeline = self._get_pipeline_with_ip() if use_ip else self._get_pipeline()
            self._set_quality_mode(pipeline)
        except Exception as e:
            lg("app").bind(event="ip_adapter.unavailable", reason=str(e)).warning("ip_adapter.unavailable")
            pipeline = self._get_pipeline()
            use_ip = False
        
        try:
            device = next(pipeline.unet.parameters()).device
        except Exception:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        generator = None
        if request.seed is not None:
            try:
                generator = torch.Generator(device=str(device)).manual_seed(int(request.seed))
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
        
        from contextlib import nullcontext
        ctx = (torch.autocast(device_type=device.type, dtype=unet_dtype)
            if device.type == "cuda" else nullcontext())
        
        extra: Dict[str, Any] = {}
        if use_ip and request.ref_image_b64:
            try:
                ref_image = self._image_service.prepare_reference_image(request.ref_image_b64, target_size=512)
                
                ip_scale = 0.55 if request.ip_scale is None else float(request.ip_scale)
                ip_scale = max(0.0, min(1.5, ip_scale))
                
                if hasattr(pipeline, "set_ip_adapter_scale"):
                    try:
                        pipeline.set_ip_adapter_scale(ip_scale)
                    except Exception:
                        pass
                
                try:
                    dev = next(pipeline.unet.parameters()).device
                    
                    if hasattr(pipeline, "text_encoder") and pipeline.text_encoder is not None:
                        pipeline.text_encoder.to(dev)
                    
                    if hasattr(pipeline, "image_encoder") and pipeline.image_encoder is not None:
                        pipeline.image_encoder.to(device="cpu", dtype=torch.float32)
                except Exception:
                    logger.exception("ip_adapter_device_guard_failed")
                
                image_embeds = None
                
                if hasattr(pipeline, "encode_image"):
                    embeds = pipeline.encode_image(
                        ref_image, device=device, num_images_per_prompt=1
                    )
                    try:
                        if isinstance(embeds, torch.Tensor):
                            image_embeds = align_to_unet_dtype(embeds.to(device=device), pipeline)
                        else:
                            image_embeds = embeds
                    except Exception:
                        image_embeds = embeds
                
                elif hasattr(pipeline, "image_encoder"):
                    enc = pipeline.image_encoder
                    proc = getattr(pipeline, "image_processor", None) or getattr(pipeline, "feature_extractor", None)
                    if proc is None:
                        raise RuntimeError("IP-Adapter: image processor not found")
                    with torch.inference_mode():
                        proc_out = proc(images=ref_image, return_tensors="pt")
                        pixel = proc_out["pixel_values"].to(device="cpu", dtype=torch.float32)
                        
                        enc = enc.to(device="cpu", dtype=torch.float32).eval()
                        with torch.inference_mode():
                            image_embeds = enc(pixel)
                        
                        image_embeds = image_embeds.to(
                            device=device,
                            dtype=unet_dtype
                        )
                
                if image_embeds is None:
                    raise RuntimeError("IP-Adapter: failed to prepare image embeddings")
                
                extra["image_embeds"] = image_embeds
                
            except Exception:
                traceback.print_exc()
                logger.exception("ip_adapter.prepare_failed", extra={"event_type": "app"})
                use_ip = False
                extra.clear()
        
        use_width = int(request.width or 512)
        use_height = int(request.height or 512)
        use_steps = int(request.steps or 28)
        
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
        
        cfg = cast(Any, settings)
        soft_deadline = time.time() + float(cfg.generation_timeout_seconds) - 1.0
        
        def timeout_callback(step, timestep=None, latents=None):
            if time.time() > soft_deadline:
                raise RuntimeError("generation_timeout")
        
        def sync_generation():
            with torch.inference_mode(), ctx:
                call_kwargs = dict(
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt or "",
                    num_inference_steps=use_steps,
                    width=use_width,
                    height=use_height,
                    guidance_scale=float(request.guidance_scale or 7.5),
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
                    
                    call_kwargs["callback_on_step_end"] = _on_step_end  # type: ignore
                    call_kwargs["callback_on_step_end_tensor_inputs"] = []  # type: ignore
                    
                    res = cast(Any, pipeline)(
                        **call_kwargs,
                        **({} if not use_ip else extra),
                    )
                    
                    return res
                    
                except TypeError:
                    call_kwargs.pop("noise_offset", None)
                    call_kwargs.pop("timesteps", None)
                    call_kwargs.pop("callback_on_step_end", None)
                    call_kwargs.pop("callback_on_step_end_tensor_inputs", None)
                    return cast(Any, pipeline)(
                        **call_kwargs,
                        **({} if not use_ip else extra),
                    )
        
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(sync_generation),
                timeout=float(cfg.generation_timeout_seconds) + 2.0,
            )
        except asyncio.TimeoutError:
            traceback.print_exc()
            logger.exception("generation.timeout", extra={"event_type": "app"})
            raise RuntimeError("Generation timed out")
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
            raise RuntimeError(f"Generation failed: {str(e)}")
        finally:
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            gc.collect()
        
        try:
            image = self._image_service.extract_image_from_result(result)
            
            from app.utils import prompt_hash
            prompt_hash_value = prompt_hash(request.prompt, request.negative_prompt or "")
            
            output_path = self._image_service.save_image(image, prompt_hash_value)
            
            return GenerationResult(
                image_path=output_path,
                metadata={
                    "width": use_width,
                    "height": use_height,
                    "steps": use_steps,
                    "guidance_scale": float(request.guidance_scale or 7.5),
                    "seed": request.seed,
                    "device": str(device),
                    "dtype": str(unet_dtype),
                    "ip_adapter_used": use_ip,
                }
            )
        except Exception as e:
            traceback.print_exc()
            logger.exception("generation.extract_failed", extra={"event_type": "app"})
            raise RuntimeError(f"Failed to extract image: {str(e)}")
    
    async def health_check(self) -> bool:
        try:
            pipeline = self._get_pipeline()
            return pipeline is not None
        except Exception:
            return False
    
    def supports_features(self, features: set[str]) -> bool:
        supported = {"text2image"}
        try:
            pipeline = self._get_pipeline()
            if hasattr(pipeline, "ip_adapter") or hasattr(pipeline, "image_encoder"):
                supported.add("ip_adapter")
        except Exception:
            pass
        return features.issubset(supported)
    
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

