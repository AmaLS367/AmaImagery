from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin

import httpx

from app.config import settings


class ComfyUIClient:
    def __init__(
        self,
        base_url: str | None = None,
        websocket_url: str | None = None,
        poll_interval_sec: float | None = None,
    ) -> None:
        root = (base_url or settings.comfyui_base_url or "").rstrip("/")
        if not root:
            raise RuntimeError("COMFYUI_BASE_URL is not configured")
        self.base_url = f"{root}/"
        self.websocket_url = websocket_url or settings.comfyui_websocket_url
        self.poll_interval_sec = float(poll_interval_sec or settings.comfyui_poll_interval_sec)
        self._client = httpx.AsyncClient(timeout=settings.comfyui_timeout_sec)

    async def submit_prompt(self, workflow: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post(urljoin(self.base_url, "prompt"), json={"prompt": workflow})
        response.raise_for_status()
        return response.json()

    async def fetch_history(self, prompt_id: str) -> dict[str, Any]:
        response = await self._client.get(urljoin(self.base_url, f"history/{prompt_id}"))
        response.raise_for_status()
        return response.json()

    async def fetch_image_bytes(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        response = await self._client.get(
            urljoin(self.base_url, "view"),
            params={"filename": filename, "subfolder": subfolder, "type": folder_type},
        )
        response.raise_for_status()
        return response.content

    async def wait_for_completion(self, prompt_id: str, timeout_sec: float) -> dict[str, Any]:
        try:
            history = await self._wait_for_completion_ws(prompt_id, timeout_sec)
            if history:
                return history
        except Exception:
            pass
        return await self._wait_for_completion_poll(prompt_id, timeout_sec)

    async def _wait_for_completion_poll(self, prompt_id: str, timeout_sec: float) -> dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + timeout_sec
        while asyncio.get_running_loop().time() < deadline:
            history = await self.fetch_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
            await asyncio.sleep(self.poll_interval_sec)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish in time")

    async def _wait_for_completion_ws(self, prompt_id: str, timeout_sec: float) -> dict[str, Any] | None:
        if not self.websocket_url:
            return None
        try:
            import websockets  # type: ignore
        except Exception:
            return None
        deadline = asyncio.get_running_loop().time() + timeout_sec
        async with websockets.connect(self.websocket_url) as websocket:  # type: ignore[attr-defined]
            while asyncio.get_running_loop().time() < deadline:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=self.poll_interval_sec)
                except asyncio.TimeoutError:
                    history = await self.fetch_history(prompt_id)
                    if prompt_id in history:
                        return history[prompt_id]
                    continue
                if isinstance(message, bytes):
                    continue
                if prompt_id in str(message) and "executed" in str(message):
                    history = await self.fetch_history(prompt_id)
                    if prompt_id in history:
                        return history[prompt_id]
        return None
