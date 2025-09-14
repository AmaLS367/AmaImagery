import asyncio
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import settings

class RequestLimitsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.max_body = settings.max_body_bytes
        self.max_q_len = settings.max_query_value_len
        self.timeout = settings.request_timeout_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Быстрые проверки query string
        if scope.get("query_string"):
            qs = scope["query_string"].decode("utf-8", "ignore")
            # грубая проверка длины значений: v<=max_q_len
            for pair in qs.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    if len(v) > self.max_q_len:
                        return await JSONResponse(
                            {"error": "request_too_large", "message": "query value too long"},
                            status_code=413,
                        )(scope, receive, send)

        # Обёртка receive для контроля размера тела
        consumed = 0
        async def limited_receive():
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                consumed += len(body or b"")
                if consumed > self.max_body:
                    # съедаем остаток и отвечаем 413
                    while not message.get("more_body", False):
                        break
                    return {"type": "http.disconnect"}  # оборвать
            return message

        # Таймаут всей обработки запроса
        path = scope.get("path", "")
        effective_timeout = self.timeout
        try:
            if path == "/generate":
                from app.config import settings as _s
                effective_timeout = max(self.timeout, int(getattr(_s, "generation_timeout_sec", 120)) + 10)

            async def call_next():
                await self.app(scope, limited_receive, send)

            await asyncio.wait_for(call_next(), timeout=effective_timeout)
        except asyncio.TimeoutError:
            resp = JSONResponse(
                {"error": "request_timeout", "message": f"request exceeded time limit ({effective_timeout}s)"},
                status_code=408,
            )
            await resp(scope, receive, send)

