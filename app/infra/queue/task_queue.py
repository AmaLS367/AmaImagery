"""
Task queue abstraction for asynchronous job processing.

Provides a unified interface for enqueueing tasks and tracking their status,
with Redis-based implementation for distributed task processing.
"""

import uuid
from typing import Protocol, Dict, Any, Optional
import json
import time

from app.infra.redis import get_redis


class TaskQueue(Protocol):
    """
    Protocol enabling switching between queue implementations without changing application code.
    """
    
    async def enqueue(self, payload: Dict[str, Any]) -> str:
        ...
    
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        ...
    
    async def update_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        ...


class RedisTaskQueue:
    """
    Redis implementation using List for queue and Hash for status storage.
    
    This design enables concurrent task consumption by multiple workers
    while preserving task state across worker restarts.
    """
    
    def __init__(self, redis_client=None, queue_key: str = "tasks:queue", status_prefix: str = "task:"):
        self.redis = redis_client
        self.queue_key = queue_key
        self.status_prefix = status_prefix
    
    def _get_redis(self):
        if self.redis is None:
            self.redis = get_redis()
        if self.redis is None:
            raise RuntimeError("Redis is not available. Set REDIS_URL or disable NO_REDIS.")
        return self.redis
    
    def _status_key(self, task_id: str) -> str:
        return f"{self.status_prefix}{task_id}"
    
    async def enqueue(self, payload: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        redis = self._get_redis()
        
        status_data = {
            "task_id": task_id,
            "status": "queued",
            "created_at": int(time.time()),
            "payload": json.dumps(payload),
        }
        
        status_key = self._status_key(task_id)
        
        await redis.hset(status_key, mapping=status_data)
        await redis.expire(status_key, 86400)
        
        await redis.lpush(self.queue_key, task_id)
        
        return task_id
    
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        redis = self._get_redis()
        status_key = self._status_key(task_id)
        
        data = await redis.hgetall(status_key)
        if not data:
            return None
        
        result = {
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
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        redis = self._get_redis()
        status_key = self._status_key(task_id)
        
        updates: Dict[str, Any] = {"status": status}
        
        if status == "running" and not await redis.hexists(status_key, "started_at"):
            updates["started_at"] = int(time.time())
        
        if status in ("completed", "failed"):
            updates["completed_at"] = int(time.time())
        
        if result is not None:
            updates["result"] = json.dumps(result)
        
        if error is not None:
            updates["error"] = error
        
        await redis.hset(status_key, mapping=updates)
    
    async def dequeue(self, timeout: float = 0.0) -> Optional[str]:
        redis = self._get_redis()
        if timeout > 0:
            result = await redis.brpop(self.queue_key, timeout=int(timeout))
            if result:
                return result[1]
        else:
            return await redis.rpop(self.queue_key)
        return None
    
    async def mark_completed(self, task_id: str, result: Dict[str, Any]) -> None:
        await self.update_status(task_id, "completed", result=result)
    
    async def mark_failed(self, task_id: str, error: str) -> None:
        await self.update_status(task_id, "failed", error=error)


_task_queue: Optional[RedisTaskQueue] = None


def get_task_queue() -> TaskQueue:
    """
    Returns singleton TaskQueue instance using existing Redis client.
    
    Raises RuntimeError if Redis is not available.
    """
    global _task_queue
    if _task_queue is None:
        _task_queue = RedisTaskQueue()
    return _task_queue

