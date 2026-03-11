import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from app.infra.queue.task_queue import RedisTaskQueue


@pytest_asyncio.fixture
async def mock_redis():
    redis = AsyncMock()
    redis._queue = []

    async def lpush(key, value):
        redis._queue.insert(0, value)
        return len(redis._queue)

    async def rpop(key):
        if redis._queue:
            return redis._queue.pop()
        return None

    async def brpop(keys, timeout):
        if redis._queue:
            return (keys[0], redis._queue.pop())
        await asyncio.sleep(min(timeout, 0.05))
        return None

    async def llen(key):
        return len(redis._queue)

    redis.lpush = Mock(side_effect=lpush)
    redis.rpop = Mock(side_effect=rpop)
    redis.brpop = Mock(side_effect=brpop)
    redis.llen = Mock(side_effect=llen)
    return redis


@pytest_asyncio.fixture
async def task_queue(mock_redis):
    return RedisTaskQueue(redis_client=mock_redis)


@pytest.mark.asyncio
async def test_task_queue_enqueue_returns_generation_id(task_queue, mock_redis):
    generation_id = "gen-123"

    result = await task_queue.enqueue(generation_id)

    assert result == generation_id
    assert await mock_redis.llen("tasks:queue") == 1


@pytest.mark.asyncio
async def test_task_queue_dequeue_non_blocking(task_queue):
    generation_id = "gen-123"
    await task_queue.enqueue(generation_id)

    dequeued = await task_queue.dequeue(timeout=0.0)

    assert dequeued == generation_id
    assert await task_queue.dequeue(timeout=0.0) is None


@pytest.mark.asyncio
async def test_task_queue_dequeue_blocking(task_queue):
    generation_id = "gen-456"
    await task_queue.enqueue(generation_id)

    dequeued = await task_queue.dequeue(timeout=1.0)

    assert dequeued == generation_id
    assert await task_queue.dequeue(timeout=0.1) is None
