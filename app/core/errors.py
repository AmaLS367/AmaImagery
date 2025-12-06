from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
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
    async def _starlette_http(request: Request, exc: StarletteHTTPException):
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
            logger.bind(event_type="error", scope="http", status=404, path=request.url.path).info("Not found")
            return JSONResponse(status_code=404, content=payload)
        
        # Handle other StarletteHTTPException
        detail = exc.detail if exc.detail else exc.__class__.__name__
        payload = {
            "error": {
                "code": "http_error",
                "message": str(detail),
                "details": {},
            },
            "request_id": _req_id(request),
        }
        logger.bind(event_type="error", scope="http", status=exc.status_code, path=request.url.path).info("HTTP error")
        return JSONResponse(status_code=exc.status_code, content=payload)
    
    @app.exception_handler(DomainException)
    async def _domain_exception(request: Request, exc: DomainException):
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
    async def _http(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else exc.__class__.__name__
        payload = {
            "error": {
                "code": "http_error",
                "message": detail,
                "details": {},
            },
            "request_id": _req_id(request),
        }
        logger.bind(event_type="error", scope="http_fastapi", status=exc.status_code, path=request.url.path).info("HTTPException")
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        payload = {
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": {},
            },
            "request_id": _req_id(request),
        }
        if _is_debug():
            payload["error"]["details"]["fields"] = exc.errors()
        logger.bind(event_type="error", scope="validation", path=request.url.path).warning("Validation error")
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
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

