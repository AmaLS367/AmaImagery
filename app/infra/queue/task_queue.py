"""
Redis implementation of the TaskQueue interface.
"""

import json
import logging
import time
import uuid
from typing import Any

from redis.asyncio import Redis

from app.domain.providers.interfaces import ITaskQueue
from app.metrics.queue import update_queue_size

logger = logging.getLogger(__name__)


class RedisTaskQueue(ITaskQueue):
    """
    Redis implementation using List for queue and Hash for status storage.
    
    This design enables concurrent task consumption by multiple workers
    while preserving task state across worker restarts.
    """
    
    def __init__(self, redis_client: Redis, queue_key: str = "tasks:queue", status_prefix: str = "task:") -> None:
        self.redis = redis_client
        self.queue_key = queue_key
        self.status_prefix = status_prefix
    
    def _status_key(self, task_id: str) -> str:
        return f"{self.status_prefix}{task_id}"
    
    async def enqueue(self, payload: dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        
        status_data = {
            "task_id": task_id,
            "status": "queued",
            "created_at": int(time.time()),
            "payload": json.dumps(payload),
        }
        
        status_key = self._status_key(task_id)
        
        # Pipeline ensures atomicity of status creation and enqueueing
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(status_key, mapping=status_data) # type: ignore
            pipe.expire(status_key, 86400)  # 24h retention
            pipe.lpush(self.queue_key, task_id)
            await pipe.execute()
        
        # Metrics update is best-effort, done outside transaction
        try:
            queue_len = await self.redis.llen(self.queue_key)  # type: ignore[awaitable-is-not-awaitable]
            update_queue_size("generation", queue_len)
        except Exception:
            pass
        
        logger.info(f"Task {task_id} enqueued.")
        return task_id
    
    async def get_status(self, task_id: str) -> dict[str, Any] | None:
        status_key = self._status_key(task_id)
        
        data = await self.redis.hgetall(status_key)  # type: ignore[awaitable-is-not-awaitable]
        if not data:
            return None
        
        # Convert bytes to logic types safely
        result: dict[str, Any] = {
            "task_id": data.get("task_id"),
            "status": data.get("status", "unknown"),
            "created_at": int(data.get("created_at", 0)),
        }
        
        if "started_at" in data:
            result["started_at"] = int(data["started_at"])
        if "completed_at" in data:
            result["completed_at"] = int(data["completed_at"])
            
        if "result" in data:
            try:
                result["result"] = json.loads(data["result"])
            except (json.JSONDecodeError, TypeError):
                result["result"] = data["result"]
                
        if "error" in data:
            result["error"] = data["error"]
            
        if "payload" in data:
            try:
                result["payload"] = json.loads(data["payload"])
            except (json.JSONDecodeError, TypeError):
                result["payload"] = data["payload"]
        
        return result
    
    async def update_status(
        self,
        task_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        status_key = self._status_key(task_id)
        
        updates: dict[str, Any] = {"status": status}
        current_time = int(time.time())
        
        # Logic to set timestamps only once
        if status == "running":
            # Only set started_at if not already set (concurrency safety)
            if not await self.redis.hexists(status_key, "started_at"):  # type: ignore[awaitable-is-not-awaitable]
                updates["started_at"] = current_time
        
        if status in ("completed", "failed"):
            updates["completed_at"] = current_time
        
        if result is not None:
            updates["result"] = json.dumps(result)
        
        if error is not None:
            updates["error"] = error
        
        await self.redis.hset(status_key, mapping=updates) # type: ignore
    
    async def dequeue(self, timeout: float = 0.0) -> str | None:
        if timeout > 0:
            # brpop returns (key, value) tuple or None
            res = await self.redis.brpop([self.queue_key], timeout=timeout)  # type: ignore[awaitable-is-not-awaitable]
            if res:
                task_id = res[1]  # type: ignore[index]
                await self._update_metrics()
                return task_id  # type: ignore[return-value]
        else:
            res = await self.redis.rpop(self.queue_key)  # type: ignore[awaitable-is-not-awaitable]
            if res:
                await self._update_metrics()
                return res  # type: ignore[return-value]
        return None

    async def _update_metrics(self) -> None:
        try:
            queue_len = await self.redis.llen(self.queue_key)  # type: ignore[awaitable-is-not-awaitable]
            update_queue_size("generation", queue_len)
        except Exception:
            pass