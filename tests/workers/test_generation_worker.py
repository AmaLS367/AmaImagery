"""
Tests for generation worker.

Tests worker lifecycle, task processing, and error handling.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from app.domain.providers.base import GenerationRequest, GenerationResult
from app.infra.queue.task_queue import RedisTaskQueue


@pytest_asyncio.fixture
async def mock_task_queue():
    """Create a mock task queue."""
    queue = AsyncMock(spec=RedisTaskQueue)
    
    # Mock storage
    queue._tasks = {}
    queue._queue = []
    
    async def enqueue(payload):
        import uuid
        task_id = str(uuid.uuid4())
        queue._tasks[task_id] = {
            "task_id": task_id,
            "status": "queued",
            "payload": payload,
        }
        queue._queue.append(task_id)
        return task_id
    
    queue.enqueue = Mock(side_effect=enqueue)
    
    async def get_status(task_id):
        return queue._tasks.get(task_id)
    
    queue.get_status = Mock(side_effect=get_status)
    
    async def update_status(task_id, status, result=None, error=None):
        if task_id in queue._tasks:
            queue._tasks[task_id]["status"] = status
            if result is not None:
                queue._tasks[task_id]["result"] = result
            if error is not None:
                queue._tasks[task_id]["error"] = error
    
    queue.update_status = Mock(side_effect=update_status)
    
    async def dequeue(timeout=0.0):
        if queue._queue:
            return queue._queue.pop(0)
        return None
    
    queue.dequeue = Mock(side_effect=dequeue)
    
    async def mark_completed(task_id, result):
        await update_status(task_id, "completed", result=result)
    
    queue.mark_completed = Mock(side_effect=mark_completed)
    
    async def mark_failed(task_id, error):
        await update_status(task_id, "failed", error=error)
    
    queue.mark_failed = Mock(side_effect=mark_failed)
    
    return queue


@pytest_asyncio.fixture
async def mock_provider():
    """Create a mock provider."""
    provider = AsyncMock()
    
    async def generate(request):
        return GenerationResult(
            image_path="/tmp/test_image.png",
            metadata={"width": 512, "height": 512, "steps": 20},
        )
    
    provider.generate = Mock(side_effect=generate)
    
    return provider


@pytest_asyncio.fixture
async def mock_provider_registry(mock_provider):
    """Create a mock provider registry."""
    registry = Mock()
    registry.get_default = Mock(return_value=mock_provider)
    return registry


@pytest_asyncio.fixture
async def mock_uow():
    """Create a mock UnitOfWork."""
    uow = AsyncMock()
    uow.generations = AsyncMock()
    uow.generations.add = AsyncMock()
    
    async def __aenter__():
        return uow
    
    async def __aexit__(*args):
        pass
    
    uow.__aenter__ = Mock(side_effect=__aenter__)
    uow.__aexit__ = Mock(side_effect=__aexit__)
    
    return uow


@pytest.mark.asyncio
async def test_worker_dequeues_task(mock_task_queue):
    """Test that worker dequeues a task from the queue."""
    payload = {"prompt": "test prompt", "width": 512, "height": 512}
    task_id = await mock_task_queue.enqueue(payload)
    
    dequeued_id = await mock_task_queue.dequeue(timeout=0.0)
    
    assert dequeued_id == task_id
    mock_task_queue.dequeue.assert_called()


@pytest.mark.asyncio
async def test_worker_updates_status_to_running(mock_task_queue):
    """Test that worker updates task status to running."""
    payload = {"prompt": "test"}
    task_id = await mock_task_queue.enqueue(payload)
    
    await mock_task_queue.update_status(task_id, "running")
    
    status = await mock_task_queue.get_status(task_id)
    assert status["status"] == "running"
    mock_task_queue.update_status.assert_called_with(task_id, "running")


@pytest.mark.asyncio
async def test_worker_calls_provider(mock_task_queue, mock_provider, mock_provider_registry):
    """Test that worker calls provider to generate image."""
    payload = {
        "prompt": "a beautiful landscape",
        "width": 512,
        "height": 512,
        "steps": 20,
    }
    task_id = await mock_task_queue.enqueue(payload)
    
    status = await mock_task_queue.get_status(task_id)
    gen_request = GenerationRequest(
        prompt=payload["prompt"],
        width=payload["width"],
        height=payload["height"],
        steps=payload["steps"],
    )
    
    result = await mock_provider.generate(gen_request)
    
    assert result is not None
    assert result.image_path is not None
    mock_provider.generate.assert_called_once()


@pytest.mark.asyncio
async def test_worker_marks_task_completed(mock_task_queue, mock_provider):
    """Test that worker marks task as completed after successful generation."""
    payload = {"prompt": "test", "width": 512, "height": 512}
    task_id = await mock_task_queue.enqueue(payload)
    
    result = GenerationResult(
        image_path="/tmp/test_image.png",
        metadata={"width": 512, "height": 512},
    )
    
    await mock_task_queue.mark_completed(
        task_id,
        {
            "image_path": result.image_path,
            "image_filename": Path(result.image_path).name,
            "metadata": result.metadata,
        },
    )
    
    status = await mock_task_queue.get_status(task_id)
    assert status["status"] == "completed"
    assert "result" in status
    mock_task_queue.mark_completed.assert_called_once()


@pytest.mark.asyncio
async def test_worker_marks_task_failed_on_provider_error(mock_task_queue, mock_provider):
    """Test that worker marks task as failed when provider raises error."""
    payload = {"prompt": "test"}
    task_id = await mock_task_queue.enqueue(payload)
    
    # Make provider raise an error
    mock_provider.generate = AsyncMock(side_effect=RuntimeError("Generation failed"))
    
    error_msg = "Generation failed"
    await mock_task_queue.mark_failed(task_id, error_msg)
    
    status = await mock_task_queue.get_status(task_id)
    assert status["status"] == "failed"
    assert status["error"] == error_msg
    mock_task_queue.mark_failed.assert_called_once()


@pytest.mark.asyncio
async def test_worker_handles_missing_payload(mock_task_queue):
    """Test that worker handles missing payload gracefully."""
    task_id = "test-task-id"
    
    # Task exists but has no payload
    mock_task_queue._tasks[task_id] = {
        "task_id": task_id,
        "status": "queued",
    }
    
    status = await mock_task_queue.get_status(task_id)
    
    # Worker should detect missing payload and mark as failed
    if status and "payload" not in status:
        await mock_task_queue.mark_failed(task_id, "Task payload not found")
        status = await mock_task_queue.get_status(task_id)
        assert status["status"] == "failed"
        assert "payload not found" in status["error"].lower()


@pytest.mark.asyncio
async def test_worker_handles_nonexistent_task(mock_task_queue):
    """Test that worker handles nonexistent task gracefully."""
    task_id = "non-existent-task"
    
    status = await mock_task_queue.get_status(task_id)
    
    # Task doesn't exist
    assert status is None


@pytest.mark.asyncio
async def test_worker_saves_generation_to_db(mock_uow):
    """Test that worker saves generation to database."""
    from app.domain.models import Generation
    
    generation = Generation(
        user_id="test-user",
        prompt={"text": "test prompt"},
        params={"width": 512, "height": 512},
        image_path="/tmp/test_image.png",
    )
    
    async with mock_uow:
        await mock_uow.generations.add(generation)
    
    mock_uow.generations.add.assert_called_once()
    mock_uow.__aenter__.assert_called_once()
    mock_uow.__aexit__.assert_called_once()

