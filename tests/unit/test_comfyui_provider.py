from unittest.mock import AsyncMock, patch

import pytest

from app.domain.providers.errors import ProviderOperationError
from app.domain.providers.interfaces import GenerationRequest, ProviderSubmission
from app.infra.providers.comfyui_client import ComfyUIArtifactError, ComfyUICompletion, ComfyUIExecutionTimeout
from app.infra.providers.comfyui_provider import ComfyUIProvider


class _FakeClient:
    def __init__(self) -> None:
        self.submit_prompt = AsyncMock()
        self.wait_for_completion = AsyncMock()
        self.fetch_image_bytes = AsyncMock()
        self.ping = AsyncMock(return_value=True)


@pytest.mark.asyncio
async def test_comfyui_submit_wraps_transport_failure():
    client = _FakeClient()
    client.submit_prompt.side_effect = RuntimeError("socket reset")
    provider = ComfyUIProvider(client=client)

    with (
        patch("app.infra.providers.comfyui_provider.load_workflow_bundle", return_value=({"1": {}}, {})),
        patch("app.infra.providers.comfyui_provider.inject_request", return_value={"1": {}}),
        pytest.raises(ProviderOperationError) as exc_info,
    ):
        await provider.submit(GenerationRequest(prompt="hello", generation_id="gen-1"))

    assert exc_info.value.stage == "submit"
    assert exc_info.value.error_code == "submit_failed"
    assert exc_info.value.provider_job_id is None


@pytest.mark.asyncio
async def test_comfyui_wait_timeout_preserves_provider_job_id():
    client = _FakeClient()
    client.wait_for_completion.side_effect = ComfyUIExecutionTimeout("timed out")
    provider = ComfyUIProvider(client=client)

    submission = ProviderSubmission(
        provider_name="comfyui",
        provider_job_id="prompt-1",
        provider_state={"prompt_id": "prompt-1", "generation_id": "gen-1"},
    )

    with pytest.raises(ProviderOperationError) as exc_info:
        await provider.wait_for_result(submission, timeout_sec=0.01)

    assert exc_info.value.error_code == "execution_timeout"
    assert exc_info.value.provider_job_id == "prompt-1"
    assert exc_info.value.provider_state["prompt_id"] == "prompt-1"


@pytest.mark.asyncio
async def test_comfyui_wait_result_missing_is_explicit_failure():
    client = _FakeClient()
    client.wait_for_completion.return_value = ComfyUICompletion(
        history={"outputs": {}},
        wait_strategy="polling",
        websocket_error=None,
    )
    provider = ComfyUIProvider(client=client)

    submission = ProviderSubmission(
        provider_name="comfyui",
        provider_job_id="prompt-2",
        provider_state={"prompt_id": "prompt-2", "generation_id": "gen-2"},
    )

    with pytest.raises(ProviderOperationError) as exc_info:
        await provider.wait_for_result(submission, timeout_sec=1.0)

    assert exc_info.value.error_code == "result_missing"
    assert exc_info.value.provider_job_id == "prompt-2"


@pytest.mark.asyncio
async def test_comfyui_wait_artifact_failure_is_explicit():
    client = _FakeClient()
    client.wait_for_completion.return_value = ComfyUICompletion(
        history={"outputs": {"9": {"images": [{"filename": "out.png", "type": "output", "subfolder": ""}]}}},
        wait_strategy="polling",
        websocket_error=None,
    )
    client.fetch_image_bytes.side_effect = ComfyUIArtifactError("missing artifact")
    provider = ComfyUIProvider(client=client)

    submission = ProviderSubmission(
        provider_name="comfyui",
        provider_job_id="prompt-3",
        provider_state={"prompt_id": "prompt-3", "generation_id": "gen-3"},
    )

    with pytest.raises(ProviderOperationError) as exc_info:
        await provider.wait_for_result(submission, timeout_sec=1.0)

    assert exc_info.value.error_code == "artifact_retrieval_failed"
    assert exc_info.value.provider_job_id == "prompt-3"
