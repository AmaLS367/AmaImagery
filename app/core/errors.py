from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from app.config import settings

_DEBUG = bool(getattr(settings, "debug", False))

def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


def _base_payload(request: Request, error: str, message: str | None = None) -> dict:
    payload = {
        "error": error,
        "path": request.url.path,
        "method": request.method,
        "request_id": _req_id(request),
    }
    if message:
        payload["message"] = message
    return payload


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _starlette_http(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if exc.detail else exc.__class__.__name__
        payload = _base_payload(request, "http_error", str(detail))
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else exc.__class__.__name__
        payload = _base_payload(request, "http_error", detail)
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        payload = _base_payload(request, "validation_error", "Request validation failed")
        if _DEBUG:
            payload["fields"] = exc.errors()
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        message = exc.__class__.__name__ if _DEBUG else "Internal Server Error"
        payload = _base_payload(request, "internal_error", message)
        return JSONResponse(status_code=500, content=payload)
