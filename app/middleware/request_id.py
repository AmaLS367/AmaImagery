import uuid
from starlette.types import ASGIApp, Receive, Scope, Send

class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        req_id = None
        for k, v in scope.get("headers", []):
            if k == b"x-request-id" and v:
                req_id = v.decode()
                break
        if not req_id:
            req_id = uuid.uuid4().hex

        scope.setdefault("state", {})["request_id"] = req_id

        async def send_with_req_id(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((b"x-request-id", req_id.encode()))
            await send(message)

        await self.app(scope, receive, send_with_req_id)
