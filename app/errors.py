from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

log = logging.getLogger(__name__)

def install_error_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(request: Request, exc: StarletteHTTPException):
        # Без утечек стека/версий; единый формат
        return JSONResponse(
            {"error": "http_error", "status": exc.status_code, "message": exc.detail or "error"},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exc_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            {"error": "validation_error", "status": 422, "details": exc.errors()},
            status_code=422,
        )

    @app.middleware("http")
    async def hide_server_version(request: Request, call_next):
        # Единая точка логирования и удаление потенциальных версий из заголовков
        try:
            resp = await call_next(request)
        except Exception:
            log.exception("unhandled_error")  # в логи — без ответа стеком
            return JSONResponse({"error": "internal_error"}, status_code=500)
        # Очистка server header, если кто-то выставил
        if "server" in resp.headers:
            resp.headers["server"] = "nginx"
        return resp
