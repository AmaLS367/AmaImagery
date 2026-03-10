"""
Redis implementation of the TaskQueue interface.
"""

import logging

from typing import Any

try:
    from redis.asyncio import Redis
    _REDIS_AVAILABLE = True
except Exception:  # pragma: no cover - minimal env fallback
    Redis = Any  # type: ignore[assignment]
    _REDIS_AVAILABLE = False

from app.domain.providers.interfaces import ITaskQueue
from app.metrics.queue import update_queue_size

logger = logging.getLogger(__name__)

# Type alias for TaskQueue interface
TaskQueue = ITaskQueue


class RedisTaskQueue(ITaskQueue):
    """
    Redis implementation using a list as a pure transport queue.
    """
    
    def __init__(self, redis_client: Redis, queue_key: str = "tasks:queue") -> None:
        self.redis = redis_client
        self.queue_key = queue_key
    
    async def enqueue(self, generation_id: str) -> str:
        await self.redis.lpush(self.queue_key, generation_id)
        
        try:
            queue_len = await self.redis.llen(self.queue_key)  # type: ignore[awaitable-is-not-awaitable]
            update_queue_size("generation", queue_len)
        except Exception:
            pass
        
        logger.info("Task %s enqueued.", generation_id)
        return generation_id
    
    async def dequeue(self, timeout: float = 0.0) -> str | None:
        try:
            if timeout > 0:
                # brpop requires integer timeout (seconds), not float
                timeout_int = int(timeout)
                # brpop returns (key, value) tuple or None
                res = await self.redis.brpop([self.queue_key], timeout=timeout_int)  # type: ignore[awaitable-is-not-awaitable]
                if res:
                    task_id = res[1]  # type: ignore[index]
                    await self._update_metrics()
                    logger.debug(f"Dequeued task {task_id} from {self.queue_key}")
                    return task_id  # type: ignore[return-value]
            else:
                res = await self.redis.rpop(self.queue_key)  # type: ignore[awaitable-is-not-awaitable]
                if res:
                    await self._update_metrics()
                    logger.debug(f"Dequeued task {res} from {self.queue_key}")
                    return res  # type: ignore[return-value]
        except Exception as e:
            logger.exception(f"Error during dequeue: {e}")
            raise
        return None
    
    async def _update_metrics(self) -> None:
        try:
            queue_len = await self.redis.llen(self.queue_key)  # type: ignore[awaitable-is-not-awaitable]
            update_queue_size("generation", queue_len)
        except Exception:
            pass


# Global instance cache
_task_queue_instance: RedisTaskQueue | None = None


def get_task_queue() -> RedisTaskQueue:
    """
    Factory function that returns a singleton TaskQueue instance.
    
    Creates the queue using the global Redis client if available.
    """
    global _task_queue_instance
    
    if _task_queue_instance is None:
        if not _REDIS_AVAILABLE:
            raise RuntimeError("Redis package is not available. Cannot create TaskQueue.")
        from app.infra.redis import get_redis
        
        redis_client = get_redis()
        if redis_client is None:
            raise RuntimeError("Redis client is not available. Cannot create TaskQueue.")
        
        _task_queue_instance = RedisTaskQueue(redis_client)
    
    return _task_queue_instance
