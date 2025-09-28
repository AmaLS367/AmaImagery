from __future__ import annotations
import json, logging, re, uuid, time
import os, contextvars, sys
from pathlib import Path
from typing import Any, Callable, Optional, Dict, Union
from loguru import logger as _logger

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.concurrency import iterate_in_threadpool
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings

# -------- контекст --------
_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
_gen_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("gen_id", default=None)
_client_ip: contextvars.ContextVar[str | None] = contextvars.ContextVar("client_ip", default=None)

_MASK_PATTERNS = (
    (re.compile(r'(?i)(Authorization:\s*Bearer\s+)[A-Za-z0-9._-]+'), r'\1***'),
    (re.compile(r'(?i)(\bBearer\s+)[A-Za-z0-9._-]+'), r'\1***'),
    (re.compile(r'(?i)(api[-_ ]?key\s*[:=]\s*)[A-Za-z0-9._-]+'), r'\1***'),
    (re.compile(r'(?i)(secret[_-]?key\s*[:=]\s*)[A-Za-z0-9._-]+'), r'\1***'),
)

def get_request_id() -> str | None: return _request_id.get()
def set_request_id(v: str | None) -> None: _request_id.set(v)
def get_gen_id() -> str | None: return _gen_id.get()
def set_gen_id(v: str | None) -> None: _gen_id.set(v)
def new_gen_id() -> str:
    gid = str(uuid.uuid4())
    _gen_id.set(gid)
    return gid
def set_client_ip(v: str | None) -> None: _client_ip.set(v)
def get_client_ip() -> str | None: return _client_ip.get()

# -------- санитайзер секретов --------
_SECRET_RX = re.compile(
    r"(?P<bearer>Authorization:\s*Bearer\s+)[A-Za-z0-9\-\._~\+/]+=*|(?P<key>(?:api|token|secret|password)\s*=\s*)[^,\s]+",
    re.IGNORECASE,
)
def _sanitize(obj: Any) -> Any:
    try:
        s = json.dumps(obj, ensure_ascii=False)

        def _repl(m: re.Match) -> str:
            if m.group("bearer"):
                return m.group("bearer") + "***"
            if m.group("key"):
                return m.group("key") + "***"
            return "***"

        s = _SECRET_RX.sub(_repl, s)
        return json.loads(s)
    except Exception:
        return obj

# -------- фильтры --------
def _event_filter(expected: str) -> Callable[[Any], bool]:
    def _f(rec: Any) -> bool:
        return rec["extra"].get("event_type") == expected
    return _f

def _app_filter(rec: Any) -> bool:
    et = rec["extra"].get("event_type")
    return et not in {"access","generation","prompt","metrics"} or et == "error"

# публичный логгер (будет пропатчен в setup_logging)
logger = _logger

# -------- перехват стандартного logging -> loguru --------
# ПОСЛЕ
class InterceptHandler(logging.Handler):
    @staticmethod
    def _safe_message(record):
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
                pass
            return base

    def emit(self, record):
        try:
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
                pass

def _patch_std_logging():
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "asyncio", "gunicorn"):
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False
        
# ==============================================
def _mask_text(text: str) -> str:
    # использует уже объявленный _SECRET_RX
    try:
        return _SECRET_RX.sub(lambda m: (m.group("bearer") or m.group("key") or "") + "***", str(text))
    except Exception:
        return str(text)


# -------- настройка sinks --------
def setup_logging(level: str = "INFO") -> None:
    """
    DEV (ENV=dev): печатаем traceback в консоль (backtrace/diagnose + {exception}).
    PROD: без traceback в консоли.
    Плюс: перехватываем stdlib logging в loguru.
    """
    global logger

    # 1) Сбрасываем все sinks (важно при reload)
    try:
        _logger.remove()
    except Exception:
        pass

    is_dev = str(os.getenv("ENV", "")).lower() == "dev"

    # 2) Консольный sink
    if is_dev:
        # DEV: максимум диагностики + traceback в выводе
        _logger.add(
            sink=lambda m: print(_mask_text(m), end=""),
            level=level,
            backtrace=True,
            diagnose=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | {message} | {extra}\n{exception}",
        )
    else:
        # PROD: аккуратный вывод без traceback
        _logger.add(
            sink=lambda m: print(_mask_text(m), end=""),
            level=level,
            backtrace=False,
            diagnose=False,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | {message} | {extra}",
        )

    # 3) Проксируем стандартный logging → loguru, чтобы все логгеры (uvicorn, fastapi, и т.д.) шли через InterceptHandler
    _patch_std_logging()

    # 4) Экспортируем выбранный логгер в глобал
    logger = _logger


# -------- Access middleware --------
class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(rid)
        set_client_ip(request.client.host if request.client else None)

        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)

            # Получаем тело ответа для подсчета байтов
            body = []
            try:
                # Используем getattr для безопасного доступа к body_iterator
                body_iterator = getattr(response, 'body_iterator', None)
                if body_iterator is not None:
                    body = [section async for section in body_iterator]
                    setattr(response, 'body_iterator', iterate_in_threadpool(iter(body)))
            except (AttributeError, TypeError):
                # Если body_iterator недоступен, пропускаем подсчет байтов
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
    DEV (ENV=dev): не перехватываем — стек отдадут ServerErrorMiddleware/run_dev.
    PROD: скрываем детали, логируем стек, возвращаем компактный JSON.
    """
    if str(os.getenv("ENV", "")).lower() == "dev":
        return

    # PROD-хендлеры
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # В DEV не глушим — даём полноценный traceback в консоль/uvicorn
        if getattr(settings, "env", "").lower() in ("dev", "development") or getattr(settings, "debug", 0) == 1:
            raise exc

        # В prod логируем и возвращаем безопасный 500 без деталей
        logger.bind(
            event_type="error",
            scope="unhandled",
            error_type=type(exc).__name__,
        ).exception("Unhandled exception")
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        logger.bind(
            event_type="error",
            scope="validation",
            errors=exc.errors(),
        ).warning("Validation error")
        return JSONResponse({"detail": exc.errors()}, status_code=HTTP_422_UNPROCESSABLE_ENTITY)


# -------- helper: логгер по типу --------
def lg(kind: str):
    return logger.bind(event_type=kind)

# -------- helper: сохранение raw-промпта (по флагу) --------
def save_prompt_raw(prompt_hash: str, original: str, negative: str | None) -> None:
    if int(settings.prompts_raw or 0) != 1:
        return
    p = Path(settings.log_dir) / "prompts" / "raw" / f"{prompt_hash}.txt"
    try:
        p.write_text(f"PROMPT:\n{original}\n\nNEGATIVE:\n{negative or ''}\n", encoding="utf-8")
        os.chmod(p, 0o600)
    except Exception:
        logger.bind(event_type="app").warning("Failed to save raw prompt", extra={"prompt_hash": prompt_hash})

# -------- helper для security-событий --------
def sec(event: str, **fields):
    payload = {"event": event}
    payload.update(fields)
    logger.bind(event_type="security", **payload).info("security")
