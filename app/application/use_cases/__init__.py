"""
Use cases for application scenarios.

Use cases represent business operations and coordinate between domain logic,
repositories, and external services.
"""

from app.application.use_cases.base import Command, UseCase, UseCaseResult
from app.application.use_cases.generate_image import (
    GenerateImageCommand,
    GenerateImageResult,
    GenerateImageUseCase,
)
from app.application.use_cases.get_generation_status import (
    GenerationStatusResult,
    GetGenerationStatusCommand,
    GetGenerationStatusUseCase,
)

__all__ = [
    "Command",
    "UseCaseResult",
    "UseCase",
    "GenerateImageCommand",
    "GenerateImageUseCase",
    "GenerateImageResult",
    "GetGenerationStatusCommand",
    "GetGenerationStatusUseCase",
    "GenerationStatusResult",
]
