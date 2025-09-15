"""
Main FastAPI application module.

This module contains the FastAPI application setup, middleware configuration,
and route definitions for the AI image generation service.
"""

import asyncio, gc, io
import logging, os, re, time
from contextlib import asynccontextmanager, nullcontext
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import base64
import hashlib
import hmac
import numpy as np
import redis.asyncio as redis # type: ignore
import torch
from fastapi import FastAPI, HTTPException, Response, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter # type: ignore
from fastapi_limiter.depends import RateLimiter # type: ignore
from PIL import Image, ImageOps
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.auth.deps import optional_user
from app.auth.router import router as auth_router
from app.auth.users.router import router as users_router

from app.routes.generation import router as generation_router
from app.routes.health import router as health_router
from app.routes.files import router as files_router

from app.config import settings
from app.db import Base, engine, get_db
from app.errors import install_error_handlers

from app.files.signing import make_signature, verify_signature, consume_once
from app.files.validators import safe_join, check_ext, check_mime
from app.infer.net_guard import apply as apply_net_guard
from app.inference.pipeline import get_pipeline, get_pipeline_with_ip
from app.limits import get_gen_semaphore
from app.logging_setup import (
    setup_logging, AccessLogMiddleware, install_exception_handlers, 
    lg, new_gen_id, save_prompt_raw, logger, sec
)
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_limits import RequestLimitsMiddleware
from app.models import Generation
from app.safety import is_blocked, is_blocked_forced
from app.schemas import GenReq, GenResp
from app.security import decode_access_token
from app.utils import prompt_hash, out_path
from app.utils_01.spell import build_spell, correct_prompt

# ==================== Application Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not _is_production():
        Base.metadata.create_all(bind=engine) 
    redis_client = await _initialize_redis()
    try:
        yield
    finally:
        if redis_client:
            await redis_client.aclose()


def _is_production() -> bool:
    return os.getenv("ENV", "prod").lower() == "prod"


async def _initialize_redis() -> Optional[redis.Redis]:
    if os.getenv("NO_REDIS", "0") == "1":
        logger.info("Redis disabled via NO_REDIS environment variable")
        return None
        
    try:
        redis_client = redis.from_url(
            settings.redis_url, 
            encoding="utf-8", 
            decode_responses=True
        )
        await FastAPILimiter.init(redis_client)
        logger.info("Rate limiter initialized successfully")
        return redis_client
    except Exception as e:
        if _is_production():
            logger.error(f"Failed to initialize rate limiter in production: {e}")
            raise
        logger.warning(f"Rate limiter disabled in development: {e}")
        return None

# ==================== Application Setup ====================

def _configure_network_security() -> None:
    """Configure network security settings."""
    if settings.no_network:
        apply_net_guard()


def _configure_pytorch() -> None:
    """Configure PyTorch settings for optimal performance."""
    try:
        torch.set_num_threads(max(1, int(settings.torch_threads)))
        
        if torch.cuda.is_available():
            try:
                torch.cuda.set_per_process_memory_fraction(
                    float(settings.cuda_vram_fraction)
                )
            except Exception:
                logger.warning("Failed to set CUDA memory fraction")
        
        # Disable cuDNN benchmark for stability
        try:
            torch.backends.cudnn.benchmark = False
        except Exception:
            logger.warning("Failed to configure cuDNN benchmark")
            
    except Exception as e:
        logger.error(f"Failed to configure PyTorch: {e}")


def _get_docs_url() -> Optional[str]:
    """Get docs URL based on environment."""
    if _is_production() or os.getenv("RUN_IN_DOCKER") == "1":
        return None
    return "/docs"


def _get_redoc_url() -> Optional[str]:
    """Get redoc URL based on environment."""
    if _is_production() or os.getenv("RUN_IN_DOCKER") == "1":
        return None
    return "/redoc"


def _get_openapi_url() -> Optional[str]:
    """Get OpenAPI URL based on environment."""
    if _is_production() or os.getenv("RUN_IN_DOCKER") == "1":
        return None
    return "/openapi.json"


# Initialize application
_configure_network_security()
_configure_pytorch()
setup_logging()

app = FastAPI(
    title="AI Image Generator",
    version="0.2.0",
    description="High-performance AI image generation service",
    lifespan=lifespan,
    docs_url=_get_docs_url(),
    redoc_url=_get_redoc_url(),
    openapi_url=_get_openapi_url(),
)

# ==================== Middleware Configuration ====================

@app.middleware("http")
async def rate_limit_logging_middleware(request: Request, call_next):
    """Log rate limiting events."""
    response = await call_next(request)
    if response.status_code == 429:
        sec("rate_limited", path=str(request.url.path))
    return response


def _add_middleware() -> None:
    """Add all middleware to the application."""
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.allowed_hosts
    )
    
    # Request processing middleware
    app.add_middleware(RequestLimitsMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AccessLogMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=True,
    )


def _setup_error_handlers() -> None:
    """Setup error handlers and exception handlers."""
    install_exception_handlers(app)
    install_error_handlers(app)


# Apply middleware and error handlers
_add_middleware()
_setup_error_handlers()

# ==================== Security Configuration ====================

def _setup_logging_filters() -> None:
    """Setup logging filters for security."""
    AUTH_PATTERN = re.compile(
        r"(Authorization:\s*Bearer\s+)([A-Za-z0-9\-\._]+)", 
        re.IGNORECASE
    )
    
    class AuthMaskingFilter(logging.Filter):
        """Filter to mask authorization tokens in logs."""
        
        def filter(self, record: logging.LogRecord) -> bool:
            """Mask authorization tokens in log messages."""
            if not settings.log_mask_auth:
                return True
                
            message = str(record.getMessage())
            masked_message = AUTH_PATTERN.sub(r"\1[REDACTED]", message)
            record.msg = masked_message
            return True
    
    logging.getLogger().addFilter(AuthMaskingFilter())


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to the response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        
        # Add HSTS header if enabled
        if settings.enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload"
            )
        
        return response


# Apply security configuration
_setup_logging_filters()
app.add_middleware(SecurityHeadersMiddleware)

# ==================== Static Files Configuration ====================

def _resolve_ui_directory() -> Optional[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    
    # Check custom directory first
    if settings.ui_static_dir:
        custom_path = (repo_root / settings.ui_static_dir).resolve()
        if custom_path.exists() and custom_path.is_dir():
            return custom_path
    
    # Check standard locations
    candidates = [
        repo_root / "frontend" / "dist",
        repo_root / "frontend",
        repo_root / "frontend" / "src",
    ]
    
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    
    return None


def _mount_static_files() -> None:
    if not settings.ui_mount_enabled:
        return
        
    ui_dir = _resolve_ui_directory()
    if ui_dir:
        app.mount(
            "/ui", 
            StaticFiles(directory=str(ui_dir), html=True), 
            name="ui"
        )
        logger.info(f"UI mounted at /ui from {ui_dir}")
    else:
        logger.warning("UI not mounted: static directory not found")


# Mount static files
_mount_static_files()

# ==================== Application Constants ====================

AUTOCORRECT_MODE = os.getenv("AUTOCORRECT", "on")  # on | warn | off
SPELL_CHECKER = build_spell(extra_words=[
    "bokeh", "karras", "euler", "dpmsolver", "lora", "vae",
    "anime", "photorealistic", "cinematic", "volumetric",
])
SPELL_WHITELIST = {"sd15", "sdxl", "lcm", "lora", "vae"} 

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")

class UpReq(BaseModel):
    path: str
    steps: int = 4
    noise_level: int = 20
    seed: int | None = None

@app.options("/health")
def health_options():
    return Response(status_code=200)


# ==================== Helper Functions ====================

def _prepare_reference_image(ref_image_b64: str, target_size: int = 512) -> Image.Image:
    """
    Prepare a reference image for IP-Adapter.
    
    Args:
        ref_image_b64: Base64 encoded reference image
        target_size: Target size for the image
        
    Returns:
        Processed PIL Image
    """
    # Decode base64 image
    image_data = base64.b64decode(ref_image_b64.split(",")[-1])
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    
    # Resize with letterboxing to preserve aspect ratio
    image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
    
    # Add padding if needed
    pad_w, pad_h = target_size - image.width, target_size - image.height
    if pad_w or pad_h:
        image = ImageOps.expand(
            image,
            border=(
                pad_w // 2, 
                pad_h // 2, 
                pad_w - pad_w // 2, 
                pad_h - pad_h // 2
            ),
            fill=(0, 0, 0),
        )
    
    return image


async def _get_user_or_ip_identifier(request: Request) -> str:
    """
    Get user ID or IP address for rate limiting.
    
    Args:
        request: FastAPI request object
        
    Returns:
        String identifier for rate limiting
    """
    # Try to get user from authorization header
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    
    # Fallback to IP address
    host = getattr(request.client, "host", "unknown")
    return f"ip:{host}"


def _create_rate_limiter(times: int, seconds: int) -> RateLimiter:
    return RateLimiter(
        times=times, 
        seconds=seconds, 
        identifier=_get_user_or_ip_identifier
    )


def _create_signed_url(file_name: str) -> Dict[str, Any]:
    exp = int(time.time()) + int(settings.file_download_ttl_sec)
    sig = make_signature(file_name, exp)
    return {"path": file_name, "exp": exp, "sig": sig}
# ==================== Generation Functions ====================

def _validate_generation_request(request: GenReq) -> None:
    """
    Validate generation request parameters.
    
    Args:
        request: Generation request to validate
        
    Raises:
        HTTPException: If validation fails
    """
    if request.width > settings.max_gen_width or request.height > settings.max_gen_height:
        raise HTTPException(status_code=400, detail="Image size too large")
    
    if request.steps > settings.max_gen_steps:
        raise HTTPException(status_code=400, detail="Steps too large")
    
    guidance = getattr(request, "guidance", 7.5)
    if guidance > settings.max_guidance:
        raise HTTPException(status_code=400, detail="Guidance too large")
    
    batch_size = getattr(request, "batch", 1)
    if batch_size > settings.max_batch:
        raise HTTPException(status_code=400, detail="Batch too large")


def _check_safety_policies(request: GenReq, user: Optional[Any]) -> None:
    """
    Check safety policies for the request.
    
    Args:
        request: Generation request
        user: Optional authenticated user
        
    Raises:
        HTTPException: If content is blocked by safety policy
    """
    # Determine if NSFW is allowed
    allow_global = settings.nsfw_allow
    allow_user = True
    
    if user is not None and hasattr(user, "nsfw_allow"):
        allow_user = bool(user.nsfw_allow)
    
    # Apply safety checks
    if not allow_global:
        # Global ban: forced blocklist applies to everyone
        if is_blocked_forced(request.prompt):
            raise HTTPException(status_code=400, detail="Blocked by safety policy.")
    else:
        # Global allow: apply blocklist only to users with NSFW disabled
        if not allow_user and is_blocked_forced(request.prompt):
            raise HTTPException(status_code=400, detail="Blocked by safety policy.")
    
    # Check regular blocklist
    if is_blocked(request.prompt) or is_blocked(request.negative_prompt):
        lg("error").bind(
            scope="safety",
            prompt_hash=prompt_hash(request.prompt, request.negative_prompt),
            reason="blocked_by_rules",
        ).error("safety.blocked")
        raise HTTPException(status_code=400, detail="Blocked by safety policy.")


def _process_prompt(request: GenReq) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Process and correct the prompt.
    
    Args:
        request: Generation request
        
    Returns:
        Tuple of (processed_prompt, corrections)
    """
    prompt = request.prompt
    corrections = []
    
    if AUTOCORRECT_MODE != "off":
        fixed, corrections = correct_prompt(
            prompt, 
            SPELL_CHECKER, 
            whitelist=SPELL_WHITELIST
        )
        if AUTOCORRECT_MODE == "on":
            prompt = fixed
    
    # Apply style
    style = getattr(request, 'style', 'anime')
    if style == 'anime':
        final_prompt = f"anime, illustration, clean lineart, cel shading, vibrant colors, key visual, {prompt}"
    else:
        final_prompt = f"photorealistic, natural lighting, detailed film look, {prompt}"
    
    return final_prompt, corrections


def _prepare_negative_prompt(request: GenReq) -> str:
    """Prepare negative prompt with defaults."""
    return request.negative_prompt or (
        "close-up, cropped, zoomed in, out of frame, bad composition, "
        "lowres, blurry, jpeg artifacts, extra fingers, extra limbs, bad hands, worst quality, low quality"
    )


@app.post(
    "/generate_legacy",
    response_model=GenResp, 
    dependencies=[Depends(_create_rate_limiter(getattr(settings, "gen_per_user_per_min", 60), 60))]
)
async def generate_legacy(
    request: GenReq, 
    db: Session = Depends(get_db), 
    user: Optional[Any] = Depends(optional_user), 
    semaphore: asyncio.Semaphore = Depends(get_gen_semaphore)
) -> GenResp:
    """
    Generate an AI image based on the provided prompt.
    
    Args:
        request: Generation parameters including prompt and settings
        db: Database session for storing generation metadata
        user: Optional authenticated user
        semaphore: Rate limiting semaphore
        
    Returns:
        GenerationResponse with generated image details
        
    Raises:
        HTTPException: For validation errors or generation failures
    """
    # Acquire semaphore with timeout
    queue_timeout = min( max(15.0, settings.keepalive_timeout_seconds + 10), float(getattr(settings, "generation_timeout_sec", 120)) / 2 )
    await asyncio.wait_for(semaphore.acquire(), timeout=queue_timeout)
    
    try:
        # Validate request parameters
        _validate_generation_request(request)
        
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
        _check_safety_policies(request, user)
        
        # Process prompt
        processed_prompt, corrections = _process_prompt(request)
        negative_prompt = _prepare_negative_prompt(request)
        
        # Log prompts
        prompt_logger.bind(
            prompt_hash=prompt_hash_value,
            original=request.prompt,
            negative=negative_prompt,
            corrected=processed_prompt,
            corrections=corrections,
        ).info("prompt.logged")
        save_prompt_raw(prompt_hash_value, request.prompt, negative_prompt)
        
        # Generate the image
        image = await _generate_image_async(
            request, 
            processed_prompt, 
            negative_prompt, 
            prompt_hash_value
        )
        
        # Save the image
        output_path = out_path(prompt_hash_value)
        image.save(output_path)
        
        # Save generation metadata to database
        _save_generation_metadata(request, user, output_path, prompt_hash_value, db)
        
        # Log completion
        gen_logger.bind(
            phase="completed",
            prompt_hash=prompt_hash_value,
            output_path=output_path,
            device=settings.device,
        ).success("generation.completed")
        
        # Create signed URL if enabled
        signed_url = _create_signed_url(Path(output_path).name) if settings.file_signing_enabled else None
        
        return GenResp(
            ok=True,
            path=Path(output_path).name,
            prompt_hash=prompt_hash_value,
            corrections=corrections,
            exp=signed_url["exp"] if signed_url else None,
            sig=signed_url["sig"] if signed_url else None,
        )
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except Exception as exc:
        # Log generation error
        lg("error").bind(
            scope="generation",
            prompt_hash=prompt_hash_value,
            error_type=type(exc).__name__,
        ).exception("generation.failed")
        raise
    finally:
        # Always release the semaphore
        try:
            semaphore.release()
        except Exception:
            pass  # Ignore errors when releasing semaphore


async def _generate_image_async(
    request: GenReq, 
    processed_prompt: str, 
    negative_prompt: str, 
    prompt_hash_value: str
) -> Image.Image:
    """
    Generate the image asynchronously.
    
    Args:
        request: Generation request
        processed_prompt: Processed prompt text
        negative_prompt: Negative prompt text
        prompt_hash_value: Prompt hash for logging
        
    Returns:
        Generated PIL Image
    """
    # Get the appropriate pipeline
    use_ip = bool(request.ref_image_b64)
    pipeline = get_pipeline_with_ip() if use_ip else get_pipeline()
    
    # Setup device and generator
    device = next(pipeline.unet.parameters()).device
    generator = None
    if request.seed is not None:
        generator = torch.Generator(device=str(device)).manual_seed(int(request.seed))
    
    # Setup autocast context
    ctx = (
        torch.autocast("cuda", dtype=torch.float16) 
        if device.type == "cuda" 
        else nullcontext()
    )
    
    # Prepare extra parameters
    extra = {}
    if use_ip and request.ref_image_b64:
        ref_image = _prepare_reference_image(request.ref_image_b64, 512)
        extra["ip_adapter_image"] = ref_image
        
        # Clamp ip_scale to valid range
        ip_scale = 0.6 if request.ip_scale is None else float(request.ip_scale)
        ip_scale = max(0.0, min(1.5, ip_scale))
        extra["ip_adapter_scale"] = ip_scale
    
    # Setup timeout callback
    deadline = time.time() + settings.generation_timeout_sec
    
    def timeout_callback(step, timestep=None, latents=None):
        if time.time() > deadline:
            raise RuntimeError("generation_timeout")
    
    # Generate the image
    def sync_generation():
        with torch.inference_mode(), ctx:
            return pipeline(
                prompt=processed_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=request.steps,
                width=request.width,
                height=request.height,
                guidance_scale=request.guidance_scale,
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
        image = _extract_image_from_result(result)
        return image
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except RuntimeError as e:
        if "generation_timeout" in str(e):
            raise HTTPException(status_code=504, detail="Generation timed out")
        raise
    finally:
        # Cleanup GPU memory
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        gc.collect()


def _extract_image_from_result(result: Any) -> Image.Image:
    try:
        # Try to get image from result.images
        if hasattr(result, "images"):
            image = result.images[0]
        else:
            # Fallback to first element if it's a list
            image = result[0]
    except (IndexError, AttributeError):
        # Create a black image as fallback
        return Image.new("RGB", (512, 512), color="black")
    
    # Ensure we have a PIL Image
    if not hasattr(image, "save"):
        image = _convert_to_pil_image(image)
    
    return image


def _convert_to_pil_image(image_data: Any) -> Image.Image:
    try:
        if isinstance(image_data, torch.Tensor):
            # Convert PyTorch tensor to numpy array
            array = image_data.detach().cpu().numpy()
            
            # Normalize to 0-255 range if needed
            if array.max() <= 1.0:
                array = (array * 255).astype(np.uint8)
            else:
                array = array.astype(np.uint8)
            
            return Image.fromarray(array)
        
        elif hasattr(image_data, '__array__'):
            # Handle numpy array
            array = np.array(image_data)
            
            # Normalize to 0-255 range if needed
            if array.dtype != np.uint8:
                if array.max() <= 1.0:
                    array = (array * 255).astype(np.uint8)
                else:
                    array = array.astype(np.uint8)
            
            return Image.fromarray(array)
        
        else:
            # Fallback: create black image
            return Image.new("RGB", (512, 512), color="black")
            
    except Exception as e:
        logger.warning(f"Failed to convert image to PIL: {e}")
        return Image.new("RGB", (512, 512), color="black")


def _save_generation_metadata(
    request: GenReq, 
    user: Optional[Any], 
    output_path: str, 
    prompt_hash_value: str, 
    db: Session
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
    
    db.add(generation)
    db.commit()

# ==================== Routes Configuration ====================

def _add_routes() -> None:
    # Authentication routes
    app.include_router(auth_router)
    app.include_router(users_router)
    
    # API routes
    app.include_router(generation_router)
    app.include_router(health_router)
    app.include_router(files_router)

_add_routes()

