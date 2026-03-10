from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urljoin

import httpx

from app.config import settings


class ComfyUIError(RuntimeError):
    """Base error for ComfyUI transport and payload failures."""


class ComfyUIConfigurationError(ComfyUIError):
    pass


class ComfyUISubmitError(ComfyUIError):
    pass


class ComfyUIHistoryError(ComfyUIError):
    pass


class ComfyUIArtifactError(ComfyUIError):
    pass


class ComfyUIWebsocketError(ComfyUIError):
    pass


class ComfyUIExecutionTimeout(ComfyUIError):
    pass


@dataclass
class ComfyUICompletion:
    history: dict[str, Any]
    wait_strategy: str
    websocket_error: str | None = None


class ComfyUIClient:
    def __init__(
        self,
        base_url: str | None = None,
        websocket_url: str | None = None,
        poll_interval_sec: float | None = None,
        http_client: httpx.AsyncClient | None = None,
        websocket_connect: Callable[..., Any] | None = None,
    ) -> None:
        root = (base_url or settings.comfyui_base_url or "").rstrip("/")
        if not root:
            raise ComfyUIConfigurationError("COMFYUI_BASE_URL is not configured")
        self.base_url = f"{root}/"
        self.websocket_url = websocket_url or settings.comfyui_websocket_url
        self.poll_interval_sec = float(poll_interval_sec or settings.comfyui_poll_interval_sec)
        self._client = http_client or httpx.AsyncClient(timeout=settings.comfyui_timeout_sec)
        self._websocket_connect = websocket_connect

    async def submit_prompt(self, workflow: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post(urljoin(self.base_url, "prompt"), json={"prompt": workflow})
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ComfyUISubmitError("ComfyUI prompt submit timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise ComfyUISubmitError(f"ComfyUI prompt submit returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ComfyUISubmitError(f"ComfyUI prompt submit failed: {exc}") from exc
        payload = self._decode_json(response, "prompt submit", ComfyUISubmitError)
        if not isinstance(payload, dict):
            raise ComfyUISubmitError("ComfyUI prompt submit returned malformed payload")
        return payload

    async def fetch_history(self, prompt_id: str) -> dict[str, Any]:
        try:
            response = await self._client.get(urljoin(self.base_url, f"history/{prompt_id}"))
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ComfyUIHistoryError(f"ComfyUI history lookup timed out for prompt {prompt_id}") from exc
        except httpx.HTTPStatusError as exc:
            raise ComfyUIHistoryError(
                f"ComfyUI history lookup returned HTTP {exc.response.status_code} for prompt {prompt_id}"
            ) from exc
        except httpx.RequestError as exc:
            raise ComfyUIHistoryError(f"ComfyUI history lookup failed for prompt {prompt_id}: {exc}") from exc
        payload = self._decode_json(response, "history lookup", ComfyUIHistoryError)
        if not isinstance(payload, dict):
            raise ComfyUIHistoryError(f"ComfyUI history payload is malformed for prompt {prompt_id}")
        return payload

    async def fetch_image_bytes(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        try:
            response = await self._client.get(
                urljoin(self.base_url, "view"),
                params={"filename": filename, "subfolder": subfolder, "type": folder_type},
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ComfyUIArtifactError(f"ComfyUI image download timed out for {filename}") from exc
        except httpx.HTTPStatusError as exc:
            raise ComfyUIArtifactError(f"ComfyUI image download returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ComfyUIArtifactError(f"ComfyUI image download failed for {filename}: {exc}") from exc
        return response.content

    async def wait_for_completion(self, prompt_id: str, timeout_sec: float) -> ComfyUICompletion:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_sec
        websocket_error: str | None = None

        if self.websocket_url:
            try:
                history = await self._wait_for_completion_ws(prompt_id, deadline)
                if history is not None:
                    return ComfyUICompletion(history=history, wait_strategy="websocket")
            except ComfyUIWebsocketError as exc:
                websocket_error = str(exc)

        history = await self._wait_for_completion_poll(prompt_id, deadline)
        return ComfyUICompletion(history=history, wait_strategy="polling", websocket_error=websocket_error)

    async def _wait_for_completion_poll(self, prompt_id: str, deadline: float) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        last_history_error: str | None = None

        while loop.time() < deadline:
            try:
                history = await self.fetch_history(prompt_id)
            except ComfyUIHistoryError as exc:
                last_history_error = str(exc)
                await asyncio.sleep(self.poll_interval_sec)
                continue

            if prompt_id in history:
                entry = history[prompt_id]
                if not isinstance(entry, dict):
                    raise ComfyUIHistoryError(f"ComfyUI history entry is malformed for prompt {prompt_id}")
                return entry

            await asyncio.sleep(self.poll_interval_sec)

        detail = f" Last history error: {last_history_error}" if last_history_error else ""
        raise ComfyUIExecutionTimeout(f"ComfyUI prompt {prompt_id} did not finish in time.{detail}")

    async def _wait_for_completion_ws(self, prompt_id: str, deadline: float) -> dict[str, Any] | None:
        if not self.websocket_url:
            return None

        connector = self._websocket_connect
        if connector is None:
            try:
                import websockets  # type: ignore
            except Exception as exc:
                raise ComfyUIWebsocketError("ComfyUI websocket support is unavailable") from exc
            connector = websockets.connect  # type: ignore[attr-defined]

        try:
            context = connector(self.websocket_url)
        except Exception as exc:
            raise ComfyUIWebsocketError(f"ComfyUI websocket connection failed: {exc}") from exc

        async with context as websocket:
            loop = asyncio.get_running_loop()
            while loop.time() < deadline:
                remaining = max(deadline - loop.time(), 0.0)
                recv_timeout = min(self.poll_interval_sec, remaining) or self.poll_interval_sec
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=recv_timeout)
                except asyncio.TimeoutError:
                    try:
                        history = await self.fetch_history(prompt_id)
                    except ComfyUIHistoryError:
                        continue
                    if prompt_id in history and isinstance(history[prompt_id], dict):
                        return history[prompt_id]
                    continue
                except Exception as exc:
                    raise ComfyUIWebsocketError(f"ComfyUI websocket receive failed: {exc}") from exc

                if isinstance(message, bytes):
                    continue

                if self._message_mentions_prompt_completion(message, prompt_id):
                    history = await self.fetch_history(prompt_id)
                    if prompt_id in history:
                        entry = history[prompt_id]
                        if not isinstance(entry, dict):
                            raise ComfyUIHistoryError(f"ComfyUI history entry is malformed for prompt {prompt_id}")
                        return entry

        return None

    def _decode_json(
        self,
        response: httpx.Response,
        operation: str,
        error_cls: type[ComfyUIError],
    ) -> Any:
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise error_cls(f"ComfyUI {operation} returned invalid JSON") from exc

    def _message_mentions_prompt_completion(self, message: str, prompt_id: str) -> bool:
        try:
            payload = json.loads(message)
        except Exception:
            return prompt_id in message and "execut" in message.lower()

        if not isinstance(payload, dict):
            return False

        event_type = str(payload.get("type") or "").lower()
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        payload_prompt_id = str(data.get("prompt_id") or payload.get("prompt_id") or "")

        if payload_prompt_id and payload_prompt_id != prompt_id:
            return False

        if event_type in {"executed", "execution_success"}:
            return True

        if event_type == "executing" and data.get("node") is None:
            return True

        return False
