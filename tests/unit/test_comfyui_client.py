import httpx
import pytest

from app.infra.providers.comfyui_client import (
    ComfyUIArtifactError,
    ComfyUIClient,
    ComfyUIExecutionTimeout,
    ComfyUIHistoryError,
    ComfyUISubmitError,
)


class _FakeWebsocket:
    def __init__(self, messages):
        self._messages = iter(messages)

    async def recv(self):
        item = next(self._messages)
        if isinstance(item, Exception):
            raise item
        return item


class _FakeWebsocketContext:
    def __init__(self, messages):
        self._websocket = _FakeWebsocket(messages)

    async def __aenter__(self):
        return self._websocket

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_submit_prompt_raises_normalized_error_on_http_failure():
    async def handler(request: httpx.Request):
        return httpx.Response(status_code=503, json={"detail": "down"})

    client = ComfyUIClient(
        base_url="http://comfy.local",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ComfyUISubmitError):
        await client.submit_prompt({"1": {"inputs": {}}})


@pytest.mark.asyncio
async def test_wait_for_completion_falls_back_to_polling_after_websocket_failure():
    responses = [
        httpx.Response(status_code=200, json={}),
        httpx.Response(status_code=200, json={"prompt-1": {"outputs": {"9": {"images": [{"filename": "x.png"}]}}}}),
    ]

    async def handler(request: httpx.Request):
        return responses.pop(0)

    client = ComfyUIClient(
        base_url="http://comfy.local",
        websocket_url="ws://comfy.local/ws",
        poll_interval_sec=0.01,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        websocket_connect=lambda url: _FakeWebsocketContext([RuntimeError("ws disconnected")]),
    )

    completion = await client.wait_for_completion("prompt-1", timeout_sec=0.1)

    assert completion.wait_strategy == "polling"
    assert completion.websocket_error is not None
    assert "prompt-1" not in completion.history
    assert "outputs" in completion.history


@pytest.mark.asyncio
async def test_wait_for_completion_times_out_with_normalized_error():
    async def handler(request: httpx.Request):
        return httpx.Response(status_code=200, json={})

    client = ComfyUIClient(
        base_url="http://comfy.local",
        poll_interval_sec=0.01,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ComfyUIExecutionTimeout):
        await client.wait_for_completion("prompt-1", timeout_sec=0.03)


@pytest.mark.asyncio
async def test_fetch_history_rejects_malformed_payload():
    async def handler(request: httpx.Request):
        return httpx.Response(status_code=200, content=b"[]", headers={"content-type": "application/json"})

    client = ComfyUIClient(
        base_url="http://comfy.local",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ComfyUIHistoryError):
        await client.fetch_history("prompt-1")


@pytest.mark.asyncio
async def test_fetch_image_bytes_normalizes_http_error():
    async def handler(request: httpx.Request):
        return httpx.Response(status_code=404, json={"detail": "missing"})

    client = ComfyUIClient(
        base_url="http://comfy.local",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ComfyUIArtifactError):
        await client.fetch_image_bytes("missing.png")
