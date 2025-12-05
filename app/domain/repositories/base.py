"""
Repository interfaces for domain entities.

Defines protocols for data access that isolate domain logic from infrastructure.
"""

from typing import Protocol, TypeVar, Optional, List, Any
from uuid import UUID

from app.domain.models import Generation, User, UserSettings

T = TypeVar("T")


class IRepository(Protocol[T]):
    """
    Generic repository protocol enabling switching between data access implementations
    without changing domain code.
    """
    
    async def add(self, entity: T) -> None:
        ...
    
    async def get(self, id: UUID | str) -> Optional[T]:
        ...
    
    async def list(self, **filters: Any) -> List[T]:
        ...
    
    async def delete(self, id: UUID | str) -> None:
        ...


class IGenerationRepository(IRepository[Generation]):
    async def list_by_user(self, user_id: UUID | str, limit: Optional[int] = None, offset: int = 0) -> List[Generation]:
        ...


class IUserRepository(IRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]:
        ...
    
    async def get_by_username(self, username: str) -> Optional[User]:
        ...
    
    async def get_by_email_or_username(self, email: str, username: str) -> Optional[User]:
        ...
    
    async def get_settings(self, user_id: UUID | str) -> Optional["UserSettings"]:
        ...
    
    async def save_settings(self, settings: "UserSettings") -> None:
        ...
