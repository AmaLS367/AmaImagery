""" Main FastAPI application module. """

import logging, os, re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import torch
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.auth.router import router as auth_router
from app.auth.users.router import router as users_router

from app.routes.generation import router as generation_router
from app.routes.health import router as health_router
from app.routes.files import router as files_router

from app.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.core.errors import install_error_handlers

from app.inference.net_guard import apply as apply_net_guard
from app.core.logging import setup_logging, AccessLogMiddleware, install_exception_handlers, logger, sec
from app.middleware.request_limits import RequestLimitsMiddleware
from app.api.v1.nsfw import router as nsfw_router
from app.services.rate_limiting import RateLimitLoggingMiddleware
from app.infra.db import run_dev_migrations

# ==================== Application Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not _is_production():
        run_dev_migrations()
    try:
        yield
    finally:
        pass

def _is_production() -> bool:
    return not bool(getattr(settings, "debug", False))

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
    return settings.docs_url

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
)

# ==================== Middleware Configuration ====================
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
    app.add_middleware(RateLimitLoggingMiddleware)
    
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
    return RedirectResponse(url="/admin/")

@app.post("/generate_legacy", include_in_schema=False)
async def generate_legacy_redirect(_: Request):
    return RedirectResponse(url="/generate", status_code=308)

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

