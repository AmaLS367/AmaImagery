"""
Infrastructure repositories package.

Exports SQLAlchemy implementations of domain repository interfaces.
"""

from app.infra.repositories.generation_repository import SqlAlchemyGenerationRepository

__all__ = [
    "SqlAlchemyGenerationRepository",
]

