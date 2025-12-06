""" Main FastAPI application module. """

from __future__ import annotations

import logging
import re
import torch
from contextlib import asynccontextmanager

from typing import Optional
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import api_v1
from app.api.v1.auth.deps import optional_user

from app.config import settings
from app.core.errors import install_error_handlers
from app.core.logging import (
    setup_logging,
    AccessLogMiddleware,
    install_exception_handlers,
    logger,
)
from app.inference.net_guard import apply as apply_net_guard
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_limits import RequestLimitsMiddleware
from app.services.rate_limiting import RateLimitLoggingMiddleware
from app.infra.db import run_pending_migrations
from app.domain.models import User


# ==================== Application Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.debug:
        run_pending_migrations()
    try:
        yield
    finally:
        pass


# ==================== Application Setup ====================

def _configure_network_security() -> None:
    if settings.no_network:
        apply_net_guard()


def _configure_pytorch() -> None:
    try:
        torch.set_num_threads(max(1, int(settings.torch_threads)))
        if torch.cuda.is_available():
            torch.cuda.set_per_process_memory_fraction(float(settings.cuda_vram_fraction))
        if hasattr(torch.backends, "cudnn"):
            torch.backends.cudnn.benchmark = False
    except Exception as e:
        logger.error(f"Failed to configure PyTorch: {e}")


# Initialize application
_configure_network_security()
_configure_pytorch()
setup_logging()

app = FastAPI(
    title="AmaImagery",
    version="0.2.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=settings.docs_url,
)


# ==================== Middleware Configuration ====================

def _add_middleware() -> None:
    # Security middleware (trusted hosts)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )

    # Correlation first
    app.add_middleware(RequestIDMiddleware)

    # Request shaping
    app.add_middleware(RequestLimitsMiddleware)

    # Rate limit logs (uses request_id if logger picks from state)
    app.add_middleware(RateLimitLoggingMiddleware)

    # Access log after core context is established
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
    if not (settings.env in ("dev", "development") or settings.debug):
        install_exception_handlers(app)
    install_error_handlers(app)


# Apply middleware and error handlers
_add_middleware()
_setup_error_handlers()


# ==================== Security Headers ====================

def _setup_logging_filters() -> None:
    AUTH_PATTERN = re.compile(r"(Authorization:\s*Bearer\s+)([A-Za-z0-9\-\._]+)", re.IGNORECASE)

    class AuthMaskingFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not settings.log_mask_auth:
                return True
            message = str(record.getMessage())
            masked_message = AUTH_PATTERN.sub(r"\1[REDACTED]", message)
            record.msg = masked_message
            return True

    logging.getLogger().addFilter(AuthMaskingFilter())


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")

        # Add HSTS header if enabled
        if settings.enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )
        return response


# Apply security configuration
_setup_logging_filters()
app.add_middleware(SecurityHeadersMiddleware)


# ==================== Application Constants ====================

@app.get("/", include_in_schema=False)
async def root(user: Optional[User] = Depends(optional_user)):
    if user and getattr(user, "is_superuser", False):
        return RedirectResponse(url="/admin/")
    
    return {
        "app": "AmaImagery",
        "version": "0.1.0",
        "docs_url": settings.docs_url,
        "frontend_url": settings.frontend_origin,
    }


# ==================== Routes Configuration ====================
app.include_router(api_v1, prefix="/api/v1")