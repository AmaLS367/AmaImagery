from __future__ import annotations

import time
from typing import Callable, Optional
import redis.asyncio as redis 
from fastapi import Depends, HTTPException, Request, status

from app.config import settings
from app.auth.deps import get_user_or_ip_identifier

_redis: Optional[redis.Redis] = None

async def _get_redis() -> redis.Redis:
    global _redis
    if _redis is not None:
        return _redis
    try:
        client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        # быстрый ping — гарантируем доступность backend'а до начала лимитов
        await client.ping()
        _redis = client
        return _redis
    except Exception as e:
        if settings.limits_enabled:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail={"error": "rate_limit_backend_unavailable"}) from e
        # Если лимиты выключены, зависимость использовать нельзя.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error": "rate_limiter_misconfigured"})

def create_rate_limiter(limit: int, window_sec: int) -> Callable:
    async def _dep(
        request: Request,
        redis_client: redis.Redis = Depends(_get_redis),
        user_key: str = Depends(get_user_or_ip_identifier),
    ) -> None:
        now = int(time.time())
        bucket = now // window_sec
        key = f"ratelimit:{user_key}:{bucket}"
        # время до конца окна — полезно для Retry-After
        retry_after = (bucket + 1) * window_sec - now

        try:
            # INCR + EXPIRE атомарно через пайплайн
            pipe = redis_client.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, window_sec + 1)
            count, _ = await pipe.execute()
        except Exception as e:
            # при включённых лимитах backend обязателен
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail={"error": "rate_limit_backend_unavailable"}) from e

        try:
            current = int(count) if not isinstance(count, int) else count
        except Exception:
            current = limit + 1  # страхуемся: лучше перелимитить, чем пропустить

        if current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "rate_limited", "key": user_key, "limit": limit, "window": window_sec},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        # иначе — пропускаем запрос без возврата значения
        return

    return _dep
