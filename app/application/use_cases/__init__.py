"""
Use cases for application scenarios.

Use cases represent business operations and coordinate between domain logic,
repositories, and external services.
"""

from app.application.use_cases.base import Command, UseCaseResult, UseCase

__all__ = ["Command", "UseCaseResult", "UseCase"]

