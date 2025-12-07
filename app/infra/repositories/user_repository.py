"""
SQLAlchemy implementation of User repository.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User, UserSettings
from app.domain.repositories import IUserRepository


class SqlAlchemyUserRepository(IUserRepository):
    """
    SQLAlchemy implementation of User repository.
    
    Uses async Session for non-blocking database operations.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def add(self, entity: User) -> None:
        self.session.add(entity)
        await self.session.flush()
    
    async def get(self, id: UUID | str) -> User | None:
        return await self.session.get(User, id)
    
    async def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> list[User]:
        stmt = select(User)
        
        for key, value in filters.items():
            if hasattr(User, key):
                stmt = stmt.filter(getattr(User, key) == value)
        
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(User)
        
        for key, value in filters.items():
            if hasattr(User, key):
                stmt = stmt.filter(getattr(User, key) == value)
                
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def delete(self, id: UUID | str) -> None:
        entity = await self.session.get(User, id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
    
    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).filter(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).filter(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(self, email: str, username: str) -> User | None:
        stmt = select(User).filter(
            or_(User.email == email, User.username == username)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_settings(self, user_id: UUID | str) -> UserSettings | None:
        return await self.session.get(UserSettings, user_id)
    
    async def save_settings(self, settings: UserSettings) -> None:
        self.session.add(settings)
        await self.session.flush()