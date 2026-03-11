from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.entrypoints.generation_worker import init_worker_infrastructure


@pytest.mark.asyncio
async def test_worker_init_supports_no_redis_mode(monkeypatch):
    logger = Mock()
    monkeypatch.setattr("app.entrypoints.generation_worker.settings.no_redis", True)

    with (
        patch("app.entrypoints.generation_worker.lg", Mock(return_value=logger)),
        patch("app.entrypoints.generation_worker.init_redis", AsyncMock()),
        patch("app.entrypoints.generation_worker.get_task_queue", Mock()),
        patch("app.entrypoints.generation_worker.get_redis", Mock(return_value=None)),
    ):
        await init_worker_infrastructure()

    logger.warning.assert_called()
    logger.info.assert_called()
