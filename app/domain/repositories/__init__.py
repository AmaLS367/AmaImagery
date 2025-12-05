"""
Domain repositories package.

Exports repository interfaces for domain entities.
"""

from app.domain.repositories.base import (
    IRepository,
    IGenerationRepository,
    IUserRepository,
)

__all__ = [
    "IRepository",
    "IGenerationRepository",
    "IUserRepository",
]
