"""
Redis client management for infrastructure layer.

Handles connection lifecycle (init/close) and provides a global accessor.
"""

import logging
from typing import Any

try:
    from redis.asyncio import Redis
    _REDIS_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only in minimal test envs
    Redis = Any  # type: ignore[assignment]
    _REDIS_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def init_redis() -> None:
    global _redis_client
    
    if settings.no_redis:
        logger.info("Redis disabled via configuration (NO_REDIS=True).")
        return
    if not _REDIS_AVAILABLE:
        logger.warning("Redis package is not installed; Redis features are disabled.")
        return

    if _redis_client is not None:
        return

    logger.info(f"Connecting to Redis at {settings.redis_url}...")
    try:
        # Create async Redis client
        client = Redis.from_url(
            settings.redis_url, 
            encoding="utf-8", 
            decode_responses=True
        )
        # Fail fast: Ping to ensure connection works immediately
        # Note: In redis.asyncio, ping() is a coroutine that returns bool
        ping_result = await client.ping()  # type: ignore[awaitable-is-not-awaitable]
        if not ping_result:
            raise RuntimeError("Redis ping returned False")
        _redis_client = client
        logger.info("Redis connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed.")
        _redis_client = None


def get_redis() -> Redis | None:
    return _redis_client
