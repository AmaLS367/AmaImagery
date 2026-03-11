"""
Domain repositories package.

Exports repository interfaces for domain entities.
"""

from app.domain.repositories.base import (
    IGenerationRepository,
    IRepository,
    IUnitOfWork,
    IUserRepository,
)

__all__ = [
    "IRepository",
    "IGenerationRepository",
    "IUserRepository",
    "IUnitOfWork",
]
