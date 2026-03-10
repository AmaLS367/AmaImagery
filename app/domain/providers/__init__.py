"""
Domain providers package.

Exports the core provider abstractions, DTOs, and registry.
"""

from app.domain.providers.interfaces import (
    GenerationRequest,
    GenerationResult,
    IImageProvider,
    ProviderResult,
    ProviderSubmission,
    Style,
)
from app.domain.providers.registry import (
    ProviderRegistry,
    get_provider_registry,
)

__all__ = [
    "GenerationRequest",
    "GenerationResult",
    "IImageProvider",
    "ProviderResult",
    "ProviderSubmission",
    "Style",
    "ProviderRegistry",
    "get_provider_registry",
]

