from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.config import settings
from app.core.exceptions import DomainException, map_exception_to_http
from app.core.logging import logger


def _is_debug() -> bool:
    return bool(getattr(settings, "debug", False))


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _starlette_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Handle 404 specifically
        if exc.status_code == 404:
            payload = {
                "error": {
                    "code": "not_found",
                    "message": "Resource not found",
                    "details": {},
                },
                "request_id": _req_id(request),
            }
            logger.bind(
                event_type="error",
                scope="http",
                status=404,
                path=request.url.path,
                method=request.method,
                query_params=str(request.query_params),
            ).warning(f"404 Not Found: {request.method} {request.url.path}")
            return JSONResponse(status_code=404, content=payload)

        # Handle other StarletteHTTPException
        detail = exc.detail if exc.detail else exc.__class__.__name__
        payload = {
            "error": {
                "code": "http_error",
                "message": detail,
                "details": {},
            },
            "request_id": _req_id(request),
        }
        logger.bind(event_type="error", scope="http", status=exc.status_code, path=request.url.path).info("HTTP error")
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(DomainException)
    async def _domain_exception(request: Request, exc: DomainException) -> JSONResponse:
        status_code, response_data = map_exception_to_http(exc)

        payload = {
            **response_data,
            "request_id": _req_id(request),
        }

        logger.bind(
            event_type="error",
            scope="domain",
            status=status_code,
            code=exc.code,
            path=request.url.path,
        ).info("Domain exception")

        return JSONResponse(status_code=status_code, content=payload)

    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else exc.__class__.__name__
        payload = {
            "error": {
                "code": "http_error",
                "message": detail,
                "details": {},
            },
            "request_id": _req_id(request),
        }
        # Use error level for 5xx, warning for 4xx (except 404), info for others
        # Always log with exception details for debugging
        log_context = {
            "event_type": "error",
            "scope": "http_fastapi",
            "status": exc.status_code,
            "path": request.url.path,
            "detail": detail,
            "method": request.method,
        }
        if exc.status_code >= 500:
            logger.bind(**log_context).error("HTTPException")
        elif exc.status_code >= 400 and exc.status_code != 404:
            logger.bind(**log_context).warning("HTTPException")
        else:
            logger.bind(**log_context).info("HTTPException")
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        details: dict[str, object] = {}
        if _is_debug():
            details["fields"] = list(exc.errors())
        payload = {
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": details,
            },
            "request_id": _req_id(request),
        }
        logger.bind(event_type="error", scope="validation", path=request.url.path).warning("Validation error")
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Don't handle HTTPException here - it's already handled by specific handlers
        if isinstance(exc, (HTTPException, StarletteHTTPException)):
            raise exc

        status_code, response_data = map_exception_to_http(exc)

        payload = {
            **response_data,
            "request_id": _req_id(request),
        }

        logger.bind(
            event_type="error",
            scope="unhandled",
            error_type=type(exc).__name__,
            path=request.url.path,
        ).exception("Unhandled exception")

        return JSONResponse(status_code=status_code, content=payload)
