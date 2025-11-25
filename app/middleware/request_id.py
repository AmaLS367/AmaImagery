import re
import uuid
from starlette.types import ASGIApp, Receive, Scope, Send, Message

# Accept safe, bounded tokens only
_REQ_ID_RE = re.compile(r"^[A-Za-z0-9._\-]{8,128}$")

class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        req_id = None
        for k, v in scope.get("headers", []):
            if k == b"x-request-id" and v:
                candidate = v.decode("utf-8", "ignore")
                req_id = candidate if _REQ_ID_RE.match(candidate) else None
                break
        if not req_id:
            req_id = uuid.uuid4().hex

        scope.setdefault("state", {})["request_id"] = req_id

        async def send_with_req_id(message: Message) -> None:
            if message.get("type") == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((b"x-request-id", req_id.encode("utf-8")))
            await send(message)

        await self.app(scope, receive, send_with_req_id)
