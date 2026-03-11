"""
Repository interfaces for domain entities.
"""

from abc import abstractmethod
from typing import Any, Protocol, TypeVar
from uuid import UUID

from app.domain.models import Generation, User, UserSettings

T = TypeVar("T")


class IRepository(Protocol[T]):
    """
    Base contract for data access using Dependency Inversion.

    Allows the Domain to remain agnostic of the underlying database implementation
    (SQLAlchemy, Mongo, Mock, etc.).
    """

    async def add(self, entity: T) -> None: ...

    async def get(self, id: UUID | str) -> T | None: ...

    # Enforcing pagination in the contract prevents accidental full-table loads in Production.
    async def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> list[T]: ...

    async def count(self, **filters: Any) -> int: ...

    async def delete(self, id: UUID | str) -> None: ...


class IGenerationRepository(IRepository[Generation]):
    """
    Extended contract for Generation access patterns.
    """

    @abstractmethod
    async def list_by_user(self, user_id: UUID | str, limit: int | None = None, offset: int = 0) -> list[Generation]: ...

    @abstractmethod
    async def count_by_user(self, user_id: UUID | str) -> int: ...

    @abstractmethod
    async def update_status(self, id: UUID | str, status: str) -> None: ...

    @abstractmethod
    async def update_fields(self, id: UUID | str, **fields: Any) -> Generation | None: ...


class IUserRepository(IRepository[User]):
    """
    Extended contract for User authentication lookups.
    """

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None: ...

    async def get_by_email_or_username(self, email: str, username: str) -> User | None: ...

    async def get_settings(self, user_id: UUID | str) -> UserSettings | None: ...

    async def save_settings(self, settings: UserSettings) -> None: ...


class IUnitOfWork(Protocol):
    """
    Contract for Unit of Work pattern.

    Ensures atomicity of business transactions across multiple repositories.
    """

    users: IUserRepository
    generations: IGenerationRepository

    async def __aenter__(self) -> "IUnitOfWork": ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
