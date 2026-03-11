"""
Redis implementation of the TaskQueue interface.
"""

import asyncio
import importlib.util
import logging
from typing import TYPE_CHECKING, Any, TypeAlias, cast

from app.domain.providers.interfaces import ITaskQueue
from app.metrics.queue import update_queue_size

_REDIS_AVAILABLE = importlib.util.find_spec("redis.asyncio") is not None

if TYPE_CHECKING:
    from redis.asyncio import Redis as RedisClient
else:
    RedisClient: TypeAlias = Any

logger = logging.getLogger(__name__)

# Type alias for TaskQueue interface
TaskQueue = ITaskQueue


class RedisTaskQueue(ITaskQueue):
    """
    Redis implementation using a list as a pure transport queue.
    """

    def __init__(self, redis_client: RedisClient, queue_key: str = "tasks:queue") -> None:
        self.redis = redis_client
        self.queue_key = queue_key

    async def enqueue(self, generation_id: str) -> str:
        await cast(Any, self.redis.lpush(self.queue_key, generation_id))

        try:
            queue_len = int(await cast(Any, self.redis.llen(self.queue_key)))
            update_queue_size("generation", queue_len)
        except Exception as exc:
            logger.debug("queue_metric_update_failed", extra={"queue_key": self.queue_key, "error": str(exc)})

        logger.info("Task %s enqueued.", generation_id)
        return generation_id

    async def dequeue(self, timeout: float = 0.0) -> str | None:
        try:
            if timeout > 0:
                # brpop requires integer timeout (seconds), not float
                timeout_int = int(timeout)
                # brpop returns (key, value) tuple or None
                blocking_result = cast(
                    tuple[str, str] | None,
                    await cast(Any, self.redis.brpop([self.queue_key], timeout=timeout_int)),
                )
                if blocking_result:
                    task_id = blocking_result[1]
                    await self._update_metrics()
                    logger.debug(f"Dequeued task {task_id} from {self.queue_key}")
                    return task_id
            else:
                popped_task_id = cast(str | None, await cast(Any, self.redis.rpop(self.queue_key)))
                if popped_task_id:
                    await self._update_metrics()
                    logger.debug(f"Dequeued task {popped_task_id} from {self.queue_key}")
                    return popped_task_id
        except Exception as e:
            logger.exception(f"Error during dequeue: {e}")
            raise
        return None

    async def _update_metrics(self) -> None:
        try:
            queue_len = int(await cast(Any, self.redis.llen(self.queue_key)))
            update_queue_size("generation", queue_len)
        except Exception as exc:
            logger.debug("queue_metric_update_failed", extra={"queue_key": self.queue_key, "error": str(exc)})


class InMemoryTaskQueue(ITaskQueue):
    """Process-local queue fallback for dev/test environments without Redis."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def enqueue(self, generation_id: str) -> str:
        await self._queue.put(generation_id)
        try:
            update_queue_size("generation", self._queue.qsize())
        except Exception as exc:
            logger.debug("queue_metric_update_failed", extra={"queue_key": "in_memory", "error": str(exc)})
        logger.warning("TaskQueue fallback in use; enqueued %s in memory.", generation_id)
        return generation_id

    async def dequeue(self, timeout: float = 0.0) -> str | None:
        try:
            if timeout > 0:
                generation_id = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            else:
                generation_id = self._queue.get_nowait()
        except TimeoutError:
            return None
        except asyncio.QueueEmpty:
            return None

        try:
            update_queue_size("generation", self._queue.qsize())
        except Exception as exc:
            logger.debug("queue_metric_update_failed", extra={"queue_key": "in_memory", "error": str(exc)})
        return generation_id


# Global instance cache
_task_queue_instance: ITaskQueue | None = None


def get_task_queue() -> ITaskQueue:
    """
    Factory function that returns a singleton TaskQueue instance.

    Creates the queue using the global Redis client if available.
    """
    global _task_queue_instance

    if _task_queue_instance is None:
        if not _REDIS_AVAILABLE:
            logger.warning("Redis package is unavailable. Falling back to InMemoryTaskQueue.")
            _task_queue_instance = InMemoryTaskQueue()
            return _task_queue_instance
        from app.infra.redis import get_redis

        redis_client = get_redis()
        if redis_client is None:
            logger.warning("Redis client is unavailable. Falling back to InMemoryTaskQueue.")
            _task_queue_instance = InMemoryTaskQueue()
            return _task_queue_instance

        _task_queue_instance = RedisTaskQueue(redis_client)

    return _task_queue_instance
