from __future__ import annotations

import contextvars
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger as _logger
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.config import settings

# -------- context --------
_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
_gen_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("gen_id", default=None)
_client_ip: contextvars.ContextVar[str | None] = contextvars.ContextVar("client_ip", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(v: str | None) -> None:
    _request_id.set(v)


def get_gen_id() -> str | None:
    return _gen_id.get()


def set_gen_id(v: str | None) -> None:
    _gen_id.set(v)


def new_gen_id() -> str:
    gid = str(uuid.uuid4())
    _gen_id.set(gid)
    return gid


def set_client_ip(v: str | None) -> None:
    _client_ip.set(v)


def get_client_ip() -> str | None:
    return _client_ip.get()


def _console_sink(message: str) -> None:
    import sys

    # Write to stderr to avoid buffering issues and ensure visibility
    sys.stderr.write(_mask_text(message))
    sys.stderr.flush()


# -------- secret sanitizer --------
_SECRET_RX = re.compile(
    r"(?P<bearer>Authorization:\s*Bearer\s+)[A-Za-z0-9\-\._~\+/]+=*|(?P<key>(?:api|token|secret|password)\s*=\s*)[^,\s]+|(?P<cookie>Set-Cookie:\s*session=)[^;\s]+",
    re.IGNORECASE,
)

# public logger (will be patched in setup_logging)
logger = _logger


# -------- intercept standard logging -> loguru --------
class InterceptHandler(logging.Handler):
    @staticmethod
    def _safe_message(record: logging.LogRecord) -> str:
        try:
            return record.getMessage()
        except Exception:
            try:
                base = str(record.msg)
            except Exception:
                base = "<log-format-error>"
            try:
                if record.args:
                    return f"{base} | args={tuple(map(repr, record.args))}"
            except Exception:
                return base
            return base

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int
            try:
                level = logger.level(record.levelname).name
            except Exception:
                level = record.levelno
            msg = self._safe_message(record)
            logger.bind(event_type="app").opt(depth=6, exception=record.exc_info).log(level, msg)
        except Exception:
            try:
                logger.opt(exception=True).warning("logging_emit_failed")
            except Exception:
                logging.Handler.handleError(self, record)


def _patch_std_logging() -> None:
    logging.root.handlers = [InterceptHandler()]
    # Set root level to DEBUG to capture all logs, filtering happens at sink level
    logging.root.setLevel(logging.DEBUG)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "asyncio", "gunicorn"):
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False
        # Set to DEBUG to ensure all logs are captured
        logging.getLogger(name).setLevel(logging.DEBUG)


# ==============================================
def _mask_text(text: str) -> str:
    try:

        def replace_match(m: re.Match[str]) -> str:
            if m.group("bearer"):
                return m.group("bearer") + "****"
            elif m.group("key"):
                return m.group("key") + "****"
            elif m.group("cookie"):
                return m.group("cookie") + "****"
            return ""

        return _SECRET_RX.sub(replace_match, text)
    except Exception:
        return text


# -------- setup sinks --------
def setup_logging(level: str = "INFO") -> None:
    """
    DEV (ENV=dev): print traceback to console (backtrace/diagnose + {exception}).
    PROD: no traceback in console.
    Plus: intercept stdlib logging into loguru.
    """
    global logger

    # Reset all sinks
    try:
        _logger.remove()
    except Exception:
        logger.debug("logging.remove_failed")

    is_dev = bool(getattr(settings, "debug", False))

    # Parse log level to ensure it's valid
    try:
        log_level = level.upper()
        if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            log_level = "INFO"
    except Exception:
        log_level = "INFO"

    # Console sink - always use stderr for better visibility
    if is_dev:
        # DEV: maximum diagnostics + traceback in output
        _logger.add(
            sink=_console_sink,
            level=log_level,
            backtrace=True,
            diagnose=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | {message} | {extra}\n{exception}",
            colorize=True,
        )
    else:
        # PROD: clean output without traceback
        _logger.add(
            sink=_console_sink,
            level=log_level,
            backtrace=False,
            diagnose=False,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message} | {extra}",
            colorize=True,
        )

    _patch_std_logging()
    logger = _logger


# -------- Access middleware --------
class AccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all incoming HTTP requests with duration, status, and size."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(rid)
        set_client_ip(request.client.host if request.client else None)

        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)

            # Get response body for byte counting
            body = []
            try:
                # Use getattr for safe access to body_iterator
                body_iterator = getattr(response, "body_iterator", None)
                if body_iterator is not None:
                    body = [section async for section in body_iterator]
                    setattr(response, "body_iterator", iterate_in_threadpool(iter(body)))
            except (AttributeError, TypeError):
                # If body_iterator is unavailable, skip byte counting
                pass
            bytes_out = sum(len(b) for b in body) if body else 0

            logger.bind(
                event_type="access",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
                bytes_in=int(request.headers.get("content-length") or 0),
                bytes_out=bytes_out,
                user_agent=request.headers.get("user-agent"),
            ).info("Access")
            response.headers["X-Request-ID"] = rid
            return response
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.bind(
                event_type="access",
                method=request.method,
                path=request.url.path,
                status=500,
                duration_ms=duration_ms,
                user_agent=request.headers.get("user-agent"),
            ).error("Access error")
            raise


# -------- Exception handlers --------
def install_exception_handlers(app: FastAPI) -> None:
    """
    DEV (ENV=dev): don't intercept stack will be provided by ServerErrorMiddleware/run_dev.
    PROD: hide details, log stack, return compact JSON.
    """
    if bool(getattr(settings, "debug", False)):
        return

    # PROD handlers
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # In DEV don't suppress provide full traceback to console/uvicorn
        if getattr(settings, "env", "").lower() in ("dev", "development") or getattr(settings, "debug", 0) == 1:
            raise exc

        # In prod log and return safe 500 without details
        logger.bind(
            event_type="error",
            scope="unhandled",
            error_type=type(exc).__name__,
        ).exception("Unhandled exception")
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.bind(
            event_type="error",
            scope="validation",
            errors=exc.errors(),
        ).warning("Validation error")
        return JSONResponse({"detail": exc.errors()}, status_code=HTTP_422_UNPROCESSABLE_ENTITY)


# -------- helpers --------
def lg(kind: str) -> Any:
    return logger.bind(event_type=kind)


def save_prompt_raw(prompt_hash: str, original: str, negative: str | None) -> None:
    if not settings.prompts_raw:
        return
    p = Path(settings.log_dir) / "prompts" / "raw" / f"{prompt_hash}.txt"
    try:
        p.write_text(f"PROMPT:\n{original}\n\nNEGATIVE:\n{negative or ''}\n", encoding="utf-8")
        os.chmod(p, 0o600)
    except Exception:
        logger.bind(event_type="app").warning("Failed to save raw prompt", extra={"prompt_hash": prompt_hash})


def sec(event: str, **fields: Any) -> None:
    payload = {"event": event}
    payload.update(fields)
    logger.bind(event_type="security", **payload).info("security")
