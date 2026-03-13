"""
Diffusers-based image generation provider implementation.
"""

import asyncio
import gc
import logging
import time
from collections.abc import Callable
from contextlib import nullcontext
from typing import Any

import torch

from app.config import settings
from app.domain.providers.interfaces import (
    GenerationRequest,
    GenerationResult,
    IImageProvider,
    ProviderResult,
    ProviderSubmission,
)
from app.files.artifacts import get_artifact_service
from app.inference.dtype_helpers import align_to_unet_dtype, get_unet_dtype
from app.metrics.providers import (
    record_generation_error,
    record_generation_start,
    record_generation_success,
)
from app.services.image_service import ImageProcessingService

logger = logging.getLogger(__name__)


class DiffusersProvider(IImageProvider):
    """
    Diffusers-based provider that isolates application code from diffusers-specific implementation details.

    Handles device management, dtype alignment, IP-Adapter setup, and timeout enforcement.
    """

    provider_name = "diffusers"

    def __init__(
        self,
        get_pipeline_fn: Callable[[], Any] | None = None,
        get_pipeline_with_ip_fn: Callable[[], Any] | None = None,
        image_service: ImageProcessingService | None = None,
    ) -> None:
        # Imports to prevent circular dependencies and early model loading
        if get_pipeline_fn is None:
            from app.inference.pipeline import get_pipeline

            self._get_pipeline = get_pipeline
        else:
            self._get_pipeline = get_pipeline_fn

        if get_pipeline_with_ip_fn is None:
            from app.inference.pipeline import get_pipeline_with_ip

            self._get_pipeline_with_ip = get_pipeline_with_ip
        else:
            self._get_pipeline_with_ip = get_pipeline_with_ip_fn

        self._image_service = image_service or ImageProcessingService()

    async def submit(self, request: GenerationRequest) -> ProviderSubmission:
        return ProviderSubmission(
            provider_name=self.provider_name,
            provider_job_id=request.generation_id,
            provider_state={"request": _request_to_state(request)},
        )

    async def wait_for_result(self, submission: ProviderSubmission, timeout_sec: float) -> ProviderResult:
        request = _state_to_request(submission.provider_state.get("request") or {})
        result = await self._generate(request)
        return ProviderResult(
            provider_name=self.provider_name,
            image_path=result.image_path,
            provider_job_id=submission.provider_job_id,
            provider_state={"local": True, "artifact_kind": "canonical_local_path"},
            metadata=result.metadata,
            artifact_persisted=True,
        )

    async def cancel(self, submission: ProviderSubmission) -> None:
        return None

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        return await self._generate(request)

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Executes the generation pipeline.
        """
        provider_name = self.provider_name
        record_generation_start(provider_name)
        start_time = time.time()

        logger.info(
            "generation.started",
            extra={
                "event_type": "app",
                "prompt": request.prompt[:50] if request.prompt else None,
                "width": request.width,
                "height": request.height,
                "steps": request.steps,
            },
        )

        try:
            # 1. Prepare Pipeline
            logger.info("generation.resolving_pipeline", extra={"event_type": "app"})
            pipeline, use_ip = self._resolve_pipeline(request)
            logger.info("generation.pipeline_resolved", extra={"event_type": "app", "use_ip": use_ip})

            logger.info("generation.getting_device", extra={"event_type": "app"})
            device = self._get_device(pipeline)
            logger.info("generation.device_obtained", extra={"event_type": "app", "device": str(device)})

            logger.info("generation.preparing_pipeline_resources", extra={"event_type": "app"})
            unet_dtype = self._prepare_pipeline_resources(pipeline, device, request.seed)
            logger.info("generation.pipeline_resources_ready", extra={"event_type": "app", "dtype": str(unet_dtype)})

            # 2. Prepare Inputs (IP-Adapter, etc.)
            logger.info("generation.preparing_ip_adapter", extra={"event_type": "app"})
            extra_kwargs = self._prepare_ip_adapter(pipeline, request, use_ip, device, unet_dtype)
            logger.info(
                "generation.ip_adapter_ready", extra={"event_type": "app", "has_extra_kwargs": bool(extra_kwargs)}
            )

            # 3. Calculate dimensions
            logger.info("generation.resolving_dimensions", extra={"event_type": "app"})
            width, height = self._resolve_dimensions(request, device)
            # For CPU, reduce steps to speed up generation for testing
            base_steps = request.steps or 28
            if device.type == "cpu":
                # Reduce steps for CPU to make generation faster (can be increased later)
                steps = min(base_steps, 10)
            else:
                steps = base_steps
            logger.info(
                "generation.dimensions_resolved",
                extra={"event_type": "app", "width": width, "height": height, "steps": steps, "device": str(device)},
            )

            # 4. Run Inference (Thread-offloaded)
            # We pass a timeout slightly larger than the internal deadline to catch hangs
            # For CPU, increase timeout significantly as generation is much slower
            base_timeout = float(settings.generation_timeout_seconds)
            if device.type == "cpu":
                # CPU generation is much slower: ~10 sec/step, so for 28 steps we need ~280 sec minimum
                # Add extra buffer for safety
                timeout_sec = max(base_timeout, steps * 12) + 60.0
            else:
                timeout_sec = base_timeout + 2.0

            logger.info(
                "generation.starting_inference",
                extra={
                    "event_type": "app",
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "device": str(device),
                    "dtype": str(unet_dtype),
                },
            )

            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._run_inference_sync,
                    pipeline=pipeline,
                    request=request,
                    width=width,
                    height=height,
                    steps=steps,
                    device=device,
                    dtype=unet_dtype,
                    extra_kwargs=extra_kwargs,
                ),
                timeout=timeout_sec,
            )

            logger.info("generation.inference_completed", extra={"event_type": "app"})

            # 5. Process Result
            return self._process_result(result, request, width, height, steps, device, unet_dtype, use_ip, start_time)

        except TimeoutError as e:
            logger.exception("generation.timeout", extra={"event_type": "app"})
            record_generation_error(provider_name, "timeout")
            raise RuntimeError("Generation timed out") from e

        except RuntimeError as e:
            # Handle known runtime errors (OOM, timeout signaled from inside)
            msg = str(e).lower()
            if "generation_timeout" in msg:
                record_generation_error(provider_name, "timeout")
                raise RuntimeError("Generation timed out") from e

            if "out of memory" in msg or ("cuda" in msg and "memory" in msg):
                logger.error(f"OOM Error: {e}")
                record_generation_error(provider_name, "out_of_memory")
                raise ValueError("CUDA out of memory: reduce width/height or steps") from e

            logger.exception("generation.runtime_error", extra={"event_type": "app", "error_message": str(e)})
            record_generation_error(provider_name, "runtime_error")
            raise e

        except Exception as e:
            logger.exception("generation.exception", extra={"event_type": "app", "error_message": str(e)})
            record_generation_error(provider_name, "exception")
            raise RuntimeError(f"Generation failed: {e}") from e

        finally:
            self._cleanup_resources()

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
        except Exception as exc:
            logger.debug(
                "generation.supports_features_probe_failed",
                extra={"event_type": "app", "error_message": str(exc)},
            )
        return features.issubset(supported)

    # --- Private Helpers ---

    def _resolve_pipeline(self, request: GenerationRequest) -> tuple[Any, bool]:
        use_ip = bool(request.ref_image_b64)
        try:
            logger.info(
                "generation._resolve_pipeline.calling_get_pipeline", extra={"event_type": "app", "use_ip": use_ip}
            )
            pipeline = self._get_pipeline_with_ip() if use_ip else self._get_pipeline()
            logger.info("generation._resolve_pipeline.pipeline_obtained", extra={"event_type": "app"})
            logger.info("generation._resolve_pipeline.setting_quality_mode", extra={"event_type": "app"})
            self._set_quality_mode(pipeline)
            logger.info("generation._resolve_pipeline.quality_mode_set", extra={"event_type": "app"})
            return pipeline, use_ip
        except Exception as e:
            logger.warning(
                f"IP-Adapter unavailable, falling back to standard pipeline: {e}", extra={"event_type": "app"}
            )
            logger.info("generation._resolve_pipeline.fallback_to_standard", extra={"event_type": "app"})
            pipeline = self._get_pipeline()
            self._set_quality_mode(pipeline)
            return pipeline, False

    def _get_device(self, pipeline: Any) -> torch.device:
        try:
            return torch.device(str(next(pipeline.unet.parameters()).device))
        except Exception:
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _prepare_pipeline_resources(self, pipeline: Any, device: torch.device, seed: int | None) -> Any:
        logger.info("generation._prepare_pipeline_resources.getting_dtype", extra={"event_type": "app"})
        unet_dtype = get_unet_dtype(pipeline)
        logger.info(
            "generation._prepare_pipeline_resources.dtype_obtained",
            extra={"event_type": "app", "dtype": str(unet_dtype)},
        )

        # Move models to device
        logger.info(
            "generation._prepare_pipeline_resources.moving_unet", extra={"event_type": "app", "device": str(device)}
        )
        if getattr(pipeline, "unet", None) is not None:
            pipeline.unet.to(device=device, dtype=unet_dtype)
        logger.info("generation._prepare_pipeline_resources.unet_moved", extra={"event_type": "app"})

        logger.info("generation._prepare_pipeline_resources.moving_vae", extra={"event_type": "app"})
        if getattr(pipeline, "vae", None) is not None:
            pipeline.vae.to(device=device, dtype=unet_dtype)
        logger.info("generation._prepare_pipeline_resources.vae_moved", extra={"event_type": "app"})

        # Text encoder usually stays on CPU if VRAM is tight, or moves to GPU
        # Ideally this logic matches `net_guard` or `pipeline.py` loading strategy
        logger.info("generation._prepare_pipeline_resources.moving_text_encoder", extra={"event_type": "app"})
        if getattr(pipeline, "text_encoder", None) is not None:
            target_dev = "cpu" if torch.cuda.is_available() else device
            pipeline.text_encoder.to(device=target_dev, dtype=torch.float32)
        logger.info("generation._prepare_pipeline_resources.text_encoder_moved", extra={"event_type": "app"})

        return unet_dtype

    def _prepare_ip_adapter(
        self, pipeline: Any, request: GenerationRequest, use_ip: bool, device: torch.device, dtype: torch.dtype
    ) -> dict[str, Any]:
        if not (use_ip and request.ref_image_b64):
            return {}

        try:
            ref_image = self._image_service.prepare_reference_image(request.ref_image_b64, target_size=512)

            ip_scale = 0.55 if request.ip_scale is None else float(request.ip_scale)
            ip_scale = max(0.0, min(1.5, ip_scale))

            if hasattr(pipeline, "set_ip_adapter_scale"):
                try:
                    pipeline.set_ip_adapter_scale(ip_scale)
                except Exception as exc:
                    logger.debug(
                        "generation.ip_adapter_scale_failed",
                        extra={"event_type": "app", "error_message": str(exc)},
                    )

            # Ensure encoders are on correct device for processing
            try:
                if hasattr(pipeline, "image_encoder") and pipeline.image_encoder is not None:
                    pipeline.image_encoder.to(device="cpu", dtype=torch.float32)
            except Exception:
                logger.warning("Failed to guard IP-Adapter device")

            image_embeds = None

            # Method A: encode_image (newer diffusers)
            if hasattr(pipeline, "encode_image"):
                embeds = pipeline.encode_image(ref_image, device=device, num_images_per_prompt=1)
                if isinstance(embeds, torch.Tensor):
                    image_embeds = align_to_unet_dtype(embeds.to(device=device), pipeline)
                else:
                    image_embeds = embeds

            # Method B: Manual processing
            elif hasattr(pipeline, "image_encoder"):
                enc = pipeline.image_encoder
                proc = getattr(pipeline, "image_processor", None) or getattr(pipeline, "feature_extractor", None)
                if proc is None:
                    raise RuntimeError("IP-Adapter: image processor not found")

                with torch.inference_mode():
                    proc_out = proc(images=ref_image, return_tensors="pt")
                    pixel = proc_out["pixel_values"].to(device="cpu", dtype=torch.float32)

                    enc = enc.to(device="cpu", dtype=torch.float32).eval()
                    image_embeds = enc(pixel)
                    image_embeds = image_embeds.to(device=device, dtype=dtype)

            if image_embeds is None:
                raise RuntimeError("Failed to prepare image embeddings")

            return {"image_embeds": image_embeds}

        except Exception as e:
            logger.exception(f"IP-Adapter preparation failed: {e}")
            return {}

    def _resolve_dimensions(self, request: GenerationRequest, device: torch.device) -> tuple[int, int]:
        use_width = int(request.width or 512)
        use_height = int(request.height or 512)

        # CPU-specific constraints to prevent long wait times
        if device.type == "cpu":
            max_side = 640
            if max(use_width, use_height) > max_side:
                ratio = max_side / float(max(use_width, use_height))
                use_width = int(round(use_width * ratio / 8) * 8)
                use_height = int(round(use_height * ratio / 8) * 8)

        return use_width, use_height

    def _run_inference_sync(
        self,
        pipeline: Any,
        request: GenerationRequest,
        width: int,
        height: int,
        steps: int,
        device: torch.device,
        dtype: torch.dtype,
        extra_kwargs: dict[str, Any],
    ) -> Any:
        """
        Blocking inference call. Must be run in a separate thread.
        """
        generator = None
        if request.seed is not None:
            generator = torch.Generator(device=str(device)).manual_seed(int(request.seed))

        # Setup autocast context
        ctx = torch.autocast(device_type=device.type, dtype=dtype) if device.type == "cuda" else nullcontext()

        # Setup Scheduler Timesteps (if needed)
        try:
            if not bool(getattr(pipeline.scheduler.config, "use_karras_sigmas", False)):
                pipeline.scheduler.set_timesteps(steps, device=device)
        except Exception as exc:
            logger.debug(
                "generation.scheduler_timestep_setup_failed",
                extra={"event_type": "app", "error_message": str(exc)},
            )

        # Prepare kwargs
        call_kwargs: dict[str, Any] = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt or "",
            "num_inference_steps": steps,
            "width": width,
            "height": height,
            "guidance_scale": float(request.guidance_scale or 7.5),
            "generator": generator,
            "noise_offset": 0.02,
        }

        # Add callback for timeout checking
        soft_deadline = time.time() + float(settings.generation_timeout_seconds) - 1.0

        def _timeout_callback(pipe: Any, step: int, timestep: Any, callback_kwargs: dict) -> dict:
            if time.time() > soft_deadline:
                raise RuntimeError("generation_timeout")
            return {}

        call_kwargs["callback_on_step_end"] = _timeout_callback
        call_kwargs["callback_on_step_end_tensor_inputs"] = []

        with torch.inference_mode(), ctx:
            # Merge extra args (IP-Adapter)
            call_kwargs.update(extra_kwargs)

            # Execute
            try:
                logger.info("generation.calling_pipeline", extra={"event_type": "app"})
                result = pipeline(**call_kwargs)
                logger.info("generation.pipeline_returned", extra={"event_type": "app"})
                return result
            except TypeError as e:
                # Fallback for older diffusers versions that don't support some args
                logger.warning(f"generation.pipeline_typeerror: {e}, trying fallback", extra={"event_type": "app"})
                call_kwargs.pop("noise_offset", None)
                call_kwargs.pop("callback_on_step_end", None)
                call_kwargs.pop("callback_on_step_end_tensor_inputs", None)
                result = pipeline(**call_kwargs)
                logger.info("generation.pipeline_fallback_returned", extra={"event_type": "app"})
                return result
            except Exception as e:
                logger.exception("generation.pipeline_error", extra={"event_type": "app", "error_message": str(e)})
                raise

    def _process_result(
        self,
        result: Any,
        request: GenerationRequest,
        width: int,
        height: int,
        steps: int,
        device: torch.device,
        dtype: torch.dtype,
        used_ip: bool,
        start_time: float,
    ) -> GenerationResult:
        logger.info("generation.extracting_image", extra={"event_type": "app"})
        image = self._image_service.extract_image_from_result(result)

        stem = request.generation_id
        output_path: str
        if stem:
            artifact_service = get_artifact_service()
            output_path = str(artifact_service.canonical_path(stem, default_ext="png"))
            logger.info("generation.saving_image", extra={"event_type": "app", "path": output_path, "canonical": True})
            image.save(output_path)
        else:
            from app.utils import prompt_hash

            p_hash = prompt_hash(request.prompt, request.negative_prompt or "")
            logger.info("generation.saving_image", extra={"event_type": "app", "hash": p_hash})
            output_path = self._image_service.save_image(image, p_hash)
        logger.info("generation.image_saved", extra={"event_type": "app", "path": output_path})

        duration = time.time() - start_time
        record_generation_success("diffusers", duration)

        return GenerationResult(
            image_path=output_path,
            metadata={
                "width": width,
                "height": height,
                "steps": int(request.steps or 28),
                "effective_steps": steps,
                "guidance_scale": float(request.guidance_scale or 7.5),
                "seed": request.seed,
                "device": str(device),
                "dtype": str(dtype),
                "ip_adapter_used": used_ip,
                "duration": f"{duration:.2f}s",
            },
        )

    def _set_quality_mode(self, pipeline: Any) -> None:
        if hasattr(pipeline, "enable_vae_tiling"):
            pipeline.enable_vae_tiling()
        if hasattr(pipeline, "enable_vae_slicing"):
            pipeline.enable_vae_slicing()
        try:
            if hasattr(pipeline, "enable_model_cpu_offload"):
                pipeline.enable_model_cpu_offload()
        except Exception as exc:
            logger.debug("generation.cpu_offload_unavailable", extra={"event_type": "app", "error_message": str(exc)})

    def _cleanup_resources(self) -> None:
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as exc:
            logger.debug(
                "generation.cuda_cache_cleanup_failed",
                extra={"event_type": "app", "error_message": str(exc)},
            )
        gc.collect()


def _request_to_state(request: GenerationRequest) -> dict[str, Any]:
    return {
        "generation_id": request.generation_id,
        "prompt": request.prompt,
        "negative_prompt": request.negative_prompt,
        "seed": request.seed,
        "width": request.width,
        "height": request.height,
        "steps": request.steps,
        "guidance_scale": request.guidance_scale,
        "ref_image_b64": request.ref_image_b64,
        "ip_scale": request.ip_scale,
        "style": request.style,
    }


def _state_to_request(state: dict[str, Any]) -> GenerationRequest:
    return GenerationRequest(
        generation_id=state.get("generation_id"),
        prompt=state["prompt"],
        negative_prompt=state.get("negative_prompt"),
        seed=state.get("seed"),
        width=state.get("width", 768),
        height=state.get("height", 1152),
        steps=state.get("steps"),
        guidance_scale=state.get("guidance_scale"),
        ref_image_b64=state.get("ref_image_b64"),
        ip_scale=state.get("ip_scale"),
        style=state.get("style", "anime"),
    )
