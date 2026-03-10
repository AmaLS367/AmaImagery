"""
Repository interfaces for domain entities.
"""

from typing import Protocol, TypeVar, Optional, List, Any
from uuid import UUID

from app.domain.models import Generation, User

T = TypeVar("T")


class IRepository(Protocol[T]):
    """
    Base contract for data access using Dependency Inversion.
    
    Allows the Domain to remain agnostic of the underlying database implementation 
    (SQLAlchemy, Mongo, Mock, etc.).
    """
    
    async def add(self, entity: T) -> None:
        ...
    
    async def get(self, id: UUID | str) -> Optional[T]:
        ...
    
    # Enforcing pagination in the contract prevents accidental full-table loads in Production.
    async def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> List[T]:
        ...
    
    async def count(self, **filters: Any) -> int:
        ...
    
    async def delete(self, id: UUID | str) -> None:
        ...


class IGenerationRepository(IRepository[Generation]):
    """
    Extended contract for Generation access patterns.
    """
    async def list_by_user(self, user_id: UUID | str, limit: Optional[int] = None, offset: int = 0) -> List[Generation]:
        ...

    async def update_fields(self, id: UUID | str, **fields: Any) -> Optional[Generation]:
        ...


class IUserRepository(IRepository[User]):
    """
    Extended contract for User authentication lookups.
    """
    async def get_by_email(self, email: str) -> Optional[User]:
        ...
    
    async def get_by_username(self, username: str) -> Optional[User]:
        ...
    
    async def get_by_email_or_username(self, email: str, username: str) -> Optional[User]:
        ...

class IUnitOfWork(Protocol):
    """
    Contract for Unit of Work pattern.
    
    Ensures atomicity of business transactions across multiple repositories.
    """
    users: IUserRepository
    generations: IGenerationRepository
    
    async def __aenter__(self) -> "IUnitOfWork":
        ...
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...
        
    async def commit(self) -> None:
        ...
        
    async def rollback(self) -> None:
        ...
