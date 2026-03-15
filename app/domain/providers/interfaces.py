"""
Provider abstraction layer that decouples the application from specific image generation implementations.
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Style = Literal["realistic", "anime"]


@dataclass
class GenerationRequest:
    """
    Provider-agnostic request DTO that isolates application code from provider-specific parameter formats.
    """

    prompt: str
    generation_id: str | None = None
    negative_prompt: str | None = None
    seed: int | None = None
    width: int = 768
    height: int = 1152
    steps: int | None = None
    guidance_scale: float | None = None
    ref_image_b64: str | None = None
    ip_scale: float | None = None
    style: Style = "realistic"

    def __post_init__(self):
        if not self.prompt or len(self.prompt.strip()) == 0:
            raise ValueError("Prompt cannot be empty")
        if self.width < 1 or self.height < 1:
            raise ValueError("Width and height must be positive")
        if self.steps is not None and self.steps < 1:
            raise ValueError("Steps must be positive")
        if self.guidance_scale is not None and self.guidance_scale < 0:
            raise ValueError("Guidance scale must be non-negative")


@dataclass
class GenerationResult:
    """
    Provider-agnostic result DTO that normalizes output from different providers.

    metadata may contain provider-specific information that callers should not depend on.
    """

    image_path: str
    metadata: dict[str, Any]

    def __post_init__(self):
        if not self.image_path:
            raise ValueError("Image path cannot be empty")


@dataclass
class ProviderSubmission:
    """Normalized provider submission state persisted after submit()."""

    provider_name: str
    provider_job_id: str | None = None
    provider_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResult:
    """Normalized provider result returned after wait_for_result()."""

    provider_name: str
    image_path: str
    provider_job_id: str | None = None
    provider_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    artifact_persisted: bool = False

    def __post_init__(self) -> None:
        if not self.image_path:
            raise ValueError("Image path cannot be empty")


class IImageProvider(Protocol):
    """
    Abstraction that allows the application to work with any image generation provider
    through a unified interface, enabling provider switching without code changes.
    """

    async def submit(self, request: GenerationRequest) -> ProviderSubmission:
        """
        May raise RuntimeError if provider is unavailable or submission fails.
        Raises ValueError if request validation fails at provider level.
        """
        ...

    async def wait_for_result(self, submission: ProviderSubmission, timeout_sec: float) -> ProviderResult: ...

    async def cancel(self, submission: ProviderSubmission) -> None: ...

    async def health_check(self) -> bool: ...

    def supports_features(self, features: set[str]) -> bool:
        """
        Used by the registry to route feature-specific requests to compatible providers.
        """
        ...


class IEmailSender(Protocol):
    """
    Abstraction for email sending services.
    """

    async def send_mail(self, subject: str, to: str | list[str], text: str, html: str | None = None) -> bool:
        """Sends an email asynchronously."""
        ...


class ITaskQueue(Protocol):
    """
    Contract for asynchronous task queue operations used as a transport only.
    """

    async def enqueue(self, generation_id: str) -> str:
        """Enqueue a generation ID and return the same ID."""
        ...

    async def dequeue(self, timeout: float = 0.0) -> str | None:
        """Wait for and retrieve the next task ID."""
        ...
