"""
Tests for TaskQueue implementation.

Tests task enqueueing, status tracking, and status transitions.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
import json
import time

from app.infra.queue.task_queue import RedisTaskQueue


@pytest_asyncio.fixture
async def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    
    # Mock storage for queue and status
    redis._queue = []
    redis._status = {}
    
    # Mock lpush (add to queue)
    async def lpush(key, value):
        redis._queue.insert(0, value)
        return len(redis._queue)
    
    redis.lpush = Mock(side_effect=lpush)
    
    # Mock rpop (remove from queue, non-blocking)
    async def rpop(key):
        if redis._queue:
            return redis._queue.pop()
        return None
    
    redis.rpop = Mock(side_effect=rpop)
    
    # Mock brpop (remove from queue, blocking)
    async def brpop(key, timeout):
        if redis._queue:
            return (key, redis._queue.pop())
        await asyncio.sleep(min(timeout, 0.1))  # Simulate timeout
        return None
    
    redis.brpop = Mock(side_effect=brpop)
    
    # Mock llen (queue length)
    async def llen(key):
        return len(redis._queue)
    
    redis.llen = Mock(side_effect=llen)
    
    # Mock hset (set hash field)
    async def hset(key, mapping=None, **kwargs):
        if key not in redis._status:
            redis._status[key] = {}
        if mapping:
            redis._status[key].update(mapping)
        if kwargs:
            redis._status[key].update(kwargs)
        return len(redis._status[key])
    
    redis.hset = Mock(side_effect=hset)
    
    # Mock hgetall (get all hash fields)
    async def hgetall(key):
        return redis._status.get(key, {})
    
    redis.hgetall = Mock(side_effect=hgetall)
    
    # Mock hexists (check if hash field exists)
    async def hexists(key, field):
        return field in redis._status.get(key, {})
    
    redis.hexists = Mock(side_effect=hexists)
    
    # Mock expire (set expiration)
    async def expire(key, seconds):
        return True
    
    redis.expire = Mock(side_effect=expire)
    
    return redis


@pytest_asyncio.fixture
async def task_queue(mock_redis):
    """Create a TaskQueue instance with mocked Redis."""
    return RedisTaskQueue(redis_client=mock_redis)


@pytest.mark.asyncio
async def test_task_queue_enqueue(task_queue, mock_redis):
    """Test enqueueing a task."""
    payload = {"prompt": "test prompt", "width": 512, "height": 512}
    
    task_id = await task_queue.enqueue(payload)
    
    assert task_id is not None
    assert isinstance(task_id, str)
    
    # Verify task was added to queue
    queue_len = await mock_redis.llen("tasks:queue")
    assert queue_len == 1
    
    # Verify status was created
    status = await task_queue.get_status(task_id)
    assert status is not None
    assert status["task_id"] == task_id
    assert status["status"] == "queued"
    assert "created_at" in status
    assert status["payload"] == payload


@pytest.mark.asyncio
async def test_task_queue_get_status(task_queue, mock_redis):
    """Test retrieving task status."""
    payload = {"prompt": "test"}
    task_id = await task_queue.enqueue(payload)
    
    status = await task_queue.get_status(task_id)
    
    assert status is not None
    assert status["task_id"] == task_id
    assert status["status"] == "queued"
    assert status["payload"] == payload
    
    # Test non-existent task
    non_existent = await task_queue.get_status("non-existent-id")
    assert non_existent is None


@pytest.mark.asyncio
async def test_task_queue_update_status(task_queue, mock_redis):
    """Test updating task status."""
    payload = {"prompt": "test"}
    task_id = await task_queue.enqueue(payload)
    
    # Update to running
    await task_queue.update_status(task_id, "running")
    status = await task_queue.get_status(task_id)
    assert status["status"] == "running"
    assert "started_at" in status
    
    # Update to completed with result
    result = {"image_path": "/path/to/image.png"}
    await task_queue.update_status(task_id, "completed", result=result)
    status = await task_queue.get_status(task_id)
    assert status["status"] == "completed"
    assert "completed_at" in status
    assert status["result"] == result
    
    # Update to failed with error
    await task_queue.update_status(task_id, "failed", error="Generation failed")
    status = await task_queue.get_status(task_id)
    assert status["status"] == "failed"
    assert status["error"] == "Generation failed"


@pytest.mark.asyncio
async def test_task_queue_status_transitions(task_queue):
    """Test status transitions: queued -> running -> completed."""
    payload = {"prompt": "test"}
    task_id = await task_queue.enqueue(payload)
    
    # Initial status: queued
    status = await task_queue.get_status(task_id)
    assert status["status"] == "queued"
    
    # Transition to running
    await task_queue.update_status(task_id, "running")
    status = await task_queue.get_status(task_id)
    assert status["status"] == "running"
    assert "started_at" in status
    
    # Transition to completed
    result = {"image_path": "/path/to/image.png"}
    await task_queue.update_status(task_id, "completed", result=result)
    status = await task_queue.get_status(task_id)
    assert status["status"] == "completed"
    assert "completed_at" in status
    assert status["result"] == result


@pytest.mark.asyncio
async def test_task_queue_dequeue_non_blocking(task_queue):
    """Test dequeueing a task (non-blocking)."""
    payload = {"prompt": "test"}
    task_id = await task_queue.enqueue(payload)
    
    # Dequeue should return the task
    dequeued_id = await task_queue.dequeue(timeout=0.0)
    assert dequeued_id == task_id
    
    # Queue should be empty now
    dequeued_id = await task_queue.dequeue(timeout=0.0)
    assert dequeued_id is None


@pytest.mark.asyncio
async def test_task_queue_dequeue_blocking(task_queue):
    """Test dequeueing a task (blocking)."""
    import asyncio
    
    payload = {"prompt": "test"}
    task_id = await task_queue.enqueue(payload)
    
    # Dequeue with timeout should return the task
    dequeued_id = await task_queue.dequeue(timeout=1.0)
    assert dequeued_id == task_id
    
    # Dequeue with timeout when queue is empty should return None
    dequeued_id = await task_queue.dequeue(timeout=0.1)
    assert dequeued_id is None


@pytest.mark.asyncio
async def test_task_queue_mark_completed(task_queue):
    """Test marking a task as completed."""
    payload = {"prompt": "test"}
    task_id = await task_queue.enqueue(payload)
    
    result = {
        "image_path": "/path/to/image.png",
        "image_filename": "image.png",
        "metadata": {"width": 512, "height": 512},
    }
    
    await task_queue.mark_completed(task_id, result)
    
    status = await task_queue.get_status(task_id)
    assert status["status"] == "completed"
    assert status["result"] == result
    assert "completed_at" in status


@pytest.mark.asyncio
async def test_task_queue_mark_failed(task_queue):
    """Test marking a task as failed."""
    payload = {"prompt": "test"}
    task_id = await task_queue.enqueue(payload)
    
    error_msg = "Generation failed: out of memory"
    await task_queue.mark_failed(task_id, error_msg)
    
    status = await task_queue.get_status(task_id)
    assert status["status"] == "failed"
    assert status["error"] == error_msg
    assert "completed_at" in status


@pytest.mark.asyncio
async def test_task_queue_multiple_tasks(task_queue):
    """Test handling multiple tasks in queue."""
    task_ids = []
    for i in range(3):
        payload = {"prompt": f"test {i}"}
        task_id = await task_queue.enqueue(payload)
        task_ids.append(task_id)
    
    # All tasks should be in queue
    for task_id in task_ids:
        status = await task_queue.get_status(task_id)
        assert status is not None
        assert status["status"] == "queued"
    
    # Dequeue should return tasks (rpop takes from end of list)
    # lpush adds to front, rpop takes from end, so FIFO
    dequeued = await task_queue.dequeue(timeout=0.0)
    assert dequeued in task_ids  # Should be one of the enqueued tasks

