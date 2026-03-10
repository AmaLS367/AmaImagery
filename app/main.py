"""
Main FastAPI application entry point.

Orchestrates application startup, middleware configuration, and infrastructure initialization.
"""

from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from typing import Any

import torch
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import api_v1
from app.api.v1.auth.deps import optional_user
from app.config import settings
from app.core.errors import install_error_handlers
from app.core.logging import (
    AccessLogMiddleware,
    install_exception_handlers,
    logger,
    setup_logging,
)
from app.domain.models import User
from app.inference.net_guard import apply as apply_net_guard
from app.infra.db import run_pending_migrations
from app.infra.queue import RedisTaskQueue
from app.infra.redis import close_redis, get_redis, init_redis
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_limits import RequestLimitsMiddleware
from app.services.rate_limiting import RateLimitLoggingMiddleware

# ==================== Application Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle events (startup and shutdown).
    Initializes infrastructure components (DB, Redis, Queue).
    """
    # 1. Database Migrations
    if not settings.debug:
        logger.info("Running pending database migrations...")
        run_pending_migrations()

    # 2. Infrastructure Initialization
    await init_redis()
    
    # 3. Task Queue Setup
    # We initialize the queue with the global redis client and attach it to app state
    # so it can be accessed by dependencies via request.app.state.task_queue
    redis_client = get_redis()
    if redis_client:
        app.state.task_queue = RedisTaskQueue(redis_client)
        logger.info("TaskQueue initialized.")
    else:
        logger.warning("Redis not available. TaskQueue disabled.")
        app.state.task_queue = None

    try:
        yield
    finally:
        # 5. Graceful Shutdown
        logger.info("Shutting down application...")
        await close_redis()


# ==================== Configuration Helpers ====================

def _configure_system() -> None:
    """Configures low-level system settings (Network, PyTorch)."""
    if settings.no_network:
        apply_net_guard()

    # PyTorch Optimization
    try:
        torch.set_num_threads(max(1, int(settings.torch_threads)))
        if torch.cuda.is_available():
            torch.cuda.set_per_process_memory_fraction(float(settings.cuda_vram_fraction))
        if hasattr(torch.backends, "cudnn"):
            torch.backends.cudnn.benchmark = False
    except Exception as e:
        logger.error(f"Failed to configure PyTorch: {e}")


def _setup_security_logging() -> None:
    """Configures filters to redact sensitive information from logs."""
    auth_pattern = re.compile(r"(Authorization:\s*Bearer\s+)([A-Za-z0-9\-\._]+)", re.IGNORECASE)

    class AuthMaskingFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not settings.log_mask_auth:
                return True
            message = str(record.getMessage())
            masked_message = auth_pattern.sub(r"\1[REDACTED]", message)
            record.msg = masked_message
            return True

    logging.getLogger().addFilter(AuthMaskingFilter())


# ==================== Middleware ====================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security-related headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")

        if settings.enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
        return response


def _setup_middleware(application: FastAPI) -> None:
    """Registers middleware stack."""
    
    # 1. Trusted Host (Security)
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )

    # 2. Security Headers
    application.add_middleware(SecurityHeadersMiddleware)

    # 3. Request ID (Correlation)
    application.add_middleware(RequestIDMiddleware)

    # 4. Limits (Shaping)
    application.add_middleware(RequestLimitsMiddleware)

    # 5. Rate Limit Logging
    application.add_middleware(RateLimitLoggingMiddleware)

    # 6. Access Logging
    application.add_middleware(AccessLogMiddleware)

    # 7. CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=True,
    )


def _setup_exceptions(application: FastAPI) -> None:
    """Registers error handlers."""
    if not (settings.is_development or settings.debug):
        install_exception_handlers(application)
    install_error_handlers(application)


# ==================== Initialization ====================

_configure_system()
_setup_security_logging()
setup_logging(level=settings.log_level)

# Test logging to ensure it works
from app.core.logging import logger
logger.info("Logging system initialized", extra={"log_level": settings.log_level, "debug": settings.debug})

app = FastAPI(
    title="AmaImagery",
    version="0.2.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=settings.docs_url,
)

_setup_middleware(app)
_setup_exceptions(app)


# ==================== Routes & Root ====================

@app.get("/", include_in_schema=False, response_model=None)
async def root(user: User | None = Depends(optional_user)) -> dict[str, Any] | RedirectResponse:
    if user and user.is_superuser:
        return RedirectResponse(url="/admin/")
    
    return {
        "app": "AmaImagery",
        "version": "0.1.0",
        "docs_url": settings.docs_url,
        "frontend_url": settings.frontend_origin,
    }

app.include_router(api_v1, prefix="/api/v1")
