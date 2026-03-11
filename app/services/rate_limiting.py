from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.auth.deps import get_user_or_ip_identifier
from app.core.logging import sec
from app.infra.redis import get_redis


class RateLimitLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            sec("rate_limited", path=str(request.url.path))
        return response


def create_rate_limiter(limit: int, window_sec: int) -> Callable:
    async def _dep(
        request: Request,
        redis_client: Any = Depends(get_redis),
        user_key: str = Depends(get_user_or_ip_identifier),
    ) -> None:
        if redis_client is None:
            return
        now = int(time.time())
        bucket = now // window_sec
        key = f"ratelimit:{user_key}:{bucket}"

        retry_after = (bucket + 1) * window_sec - now

        try:
            pipe = redis_client.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, window_sec + 1)
            count, _ = await pipe.execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": "rate_limit_backend_unavailable"}
            ) from e

        try:
            current = int(count) if not isinstance(count, int) else count
        except Exception:
            current = limit + 1

        if current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "rate_limited", "key": user_key, "limit": limit, "window": window_sec},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        return

    return _dep
