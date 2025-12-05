"""
SQLAlchemy implementation of User repository.
"""

from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.domain.models import User, UserSettings
from app.domain.repositories import IUserRepository


class SqlAlchemyUserRepository:
    """
    SQLAlchemy implementation of User repository.
    
    Uses async Session for non-blocking database operations.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, entity: User) -> None:
        self.session.add(entity)
        await self.session.flush()
    
    async def get(self, id: UUID | str) -> Optional[User]:
        return await self.session.get(User, id)
    
    async def list(self, **filters: Any) -> List[User]:
        stmt = select(User)
        for key, value in filters.items():
            stmt = stmt.filter(getattr(User, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete(self, id: UUID | str) -> None:
        entity = await self.session.get(User, id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).filter(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).filter(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(self, email: str, username: str) -> Optional[User]:
        stmt = select(User).filter(
            or_(User.email == email, User.username == username)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_settings(self, user_id: UUID | str) -> Optional[UserSettings]:
        return await self.session.get(UserSettings, user_id)
    
    async def save_settings(self, settings: UserSettings) -> None:
        self.session.add(settings)
        await self.session.flush()

