import asyncio
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.responses import JSONResponse
from app.config import settings

class _BodyTooLarge(Exception):
    pass

class RequestLimitsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.max_body = int(settings.max_body_bytes)
        self.max_q_len = int(settings.max_query_value_len)
        self.timeout = int(settings.request_timeout_seconds)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        # Query-string limits
        qs = scope.get("query_string", b"")
        if qs:
            try:
                for pair in qs.decode("utf-8", "ignore").split("&"):
                    if "=" in pair:
                        _, v = pair.split("=", 1)
                        if len(v) > self.max_q_len:
                            return await JSONResponse(
                                {"error": "request_too_large", "message": "query value too long"},
                                status_code=413,
                            )(scope, receive, send)
            except Exception:
                # If parsing fails, treat as bad request size
                return await JSONResponse(
                    {"error": "bad_request", "message": "malformed query string"},
                    status_code=400,
                )(scope, receive, send)

        consumed = 0

        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"")
                consumed += len(body)
                if consumed > self.max_body:
                    while message.get("more_body"):
                        message = await receive()
                    raise _BodyTooLarge()
            return message

        path = scope.get("path", "") or ""
        effective_timeout = self.timeout
        if path == "/generate":
            # Keep public behavior: extend a bit for generation endpoint
            effective_timeout = max(self.timeout, int(settings.generation_timeout_seconds) + 10)

        async def call_next():
            await self.app(scope, limited_receive, send)

        try:
            await asyncio.wait_for(call_next(), timeout=effective_timeout)
        except _BodyTooLarge:
            resp = JSONResponse(
                {"error": "request_too_large", "message": "request body exceeds limit"},
                status_code=413,
            )
            await resp(scope, receive, send)
        except asyncio.TimeoutError:
            resp = JSONResponse(
                {"error": "request_timeout", "message": f"request exceeded time limit ({effective_timeout}s)"},
                status_code=408,
            )
            await resp(scope, receive, send)
