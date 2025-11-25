from __future__ import annotations
import os
import typing as t
import redis.asyncio as redis
from app.config import settings
_redis: t.Any = None

def init_redis() -> t.Any:
    global _redis
    if _redis is not None:
        return _redis

    url = os.getenv("REDIS_URL") or os.getenv("REDIS_DSN") or settings.redis_url
    if not url or redis is None:
        _redis = None
        return _redis

    _redis = redis.from_url(url, encoding="utf-8", decode_responses=True)
    return _redis

def get_redis() -> t.Any:
    return init_redis()
