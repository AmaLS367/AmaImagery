""" Main FastAPI application module. """

import asyncio
import logging, os, re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Any

import redis.asyncio as redis
import torch
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
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
from app.infra.db import Base, engine, get_db
from app.middleware.request_id import RequestIDMiddleware
from app.core.errors import install_error_handlers

from app.inference.net_guard import apply as apply_net_guard
from app.core.limits import get_gen_semaphore
from app.core.logging import setup_logging, AccessLogMiddleware, install_exception_handlers, logger, sec
from app.middleware.request_limits import RequestLimitsMiddleware
from app.domain.schemas import GenReq, GenResp
from app.services.rate_limiting import create_rate_limiter
from app.services.generation_service import GenerationService
from app.api.v1.nsfw import router as nsfw_router

# ==================== Application Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not _is_production():
        Base.metadata.create_all(bind=engine)
    redis_client = await _initialize_redis()

    # make redis visible for routers
    app.state.redis_client = redis_client

    try:
        yield
    finally:
        # drop from state and close
        if hasattr(app.state, "redis_client"):
            app.state.redis_client = None
        if redis_client:
            await redis_client.aclose()



def _is_production() -> bool:
    return not bool(getattr(settings, "debug", False))

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
        logger.info("Redis client initialized")
        return redis_client
    except Exception as e:
        if _is_production():
            logger.error(f"Failed to initialize rate limiter in production: {e}")
            raise
        logger.warning(f"Rate limiter disabled in development: {e}")
        return None

# ==================== Application Setup ====================

def _configure_network_security() -> None:
    if settings.no_network:
        apply_net_guard()


def _configure_pytorch() -> None:
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
    return None if not bool(getattr(settings, "debug", False)) else "/docs"

def _get_redoc_url() -> Optional[str]:
    return None if not bool(getattr(settings, "debug", False)) else "/redoc"

def _get_openapi_url() -> Optional[str]:
    return None if not bool(getattr(settings, "debug", False)) else "/openapi.json"

# Initialize application
_configure_network_security()
_configure_pytorch()
setup_logging()

app = FastAPI(
    title="AI Image Generator",
    version="0.2.0",
    debug=bool(getattr(settings, "debug", False)),
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
    if not (getattr(settings, "env", "").lower() in ("dev", "development") or getattr(settings, "debug", 0) == 1):
        install_exception_handlers(app)
    install_error_handlers(app)



# Apply middleware and error handlers
_add_middleware()
_setup_error_handlers()

# ==================== Security Configuration ====================

def _setup_logging_filters() -> None:
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

# Это поменять на точный путь, никакие проверки не нужны, мы точно знаем, где фронт
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

_mount_static_files()

# ==================== Application Constants ====================

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")

# ==================== Generation Functions ====================

@app.post(
    "/generate_legacy",
    response_model=GenResp,
    dependencies=[Depends(create_rate_limiter(limit=settings.gen_per_user_per_min, window_sec=60))]
)
async def generate_legacy(
    request: GenReq,
    db: Session = Depends(get_db),
    user: Optional[Any] = Depends(optional_user),
    semaphore: asyncio.Semaphore = Depends(get_gen_semaphore),
) -> GenResp:
    queue_timeout = min(
        max(15.0, settings.keepalive_timeout_seconds + 10),
        float(getattr(settings, "generation_timeout_sec", 120)) / 2,
    )
    await asyncio.wait_for(semaphore.acquire(), timeout=queue_timeout)
    try:
        service = GenerationService(db)
        return await service.generate_image(request, user)
    finally:
        try:
            semaphore.release()
        except Exception:
            pass

# ==================== Routes Configuration ====================

def _add_routes() -> None:
    # Authentication routes
    app.include_router(auth_router)
    app.include_router(users_router)
    
    # API routes
    app.include_router(generation_router)
    app.include_router(health_router)
    app.include_router(files_router)
    
    app.include_router(nsfw_router)

_add_routes()

