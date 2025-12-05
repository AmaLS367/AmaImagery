"""
SQLAlchemy implementation of User repository.
"""

import asyncio
from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models import User, UserSettings
from app.domain.repositories import IUserRepository


class SqlAlchemyUserRepository:
    """
    SQLAlchemy implementation of User repository.
    
    Uses synchronous Session internally, wrapping DB calls in asyncio.to_thread
    to avoid blocking the event loop.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    async def add(self, entity: User) -> None:
        def _add():
            self.session.add(entity)
            self.session.flush()
        
        await asyncio.to_thread(_add)
    
    async def get(self, id: UUID | str) -> Optional[User]:
        def _get():
            return self.session.get(User, id)
        
        return await asyncio.to_thread(_get)
    
    async def list(self, **filters: Any) -> List[User]:
        def _list():
            query = self.session.query(User)
            for key, value in filters.items():
                query = query.filter(getattr(User, key) == value)
            return query.all()
        
        return await asyncio.to_thread(_list)
    
    async def delete(self, id: UUID | str) -> None:
        def _delete():
            entity = self.session.get(User, id)
            if entity:
                self.session.delete(entity)
                self.session.flush()
        
        await asyncio.to_thread(_delete)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        def _get_by_email():
            return self.session.query(User).filter(User.email == email).first()
        
        return await asyncio.to_thread(_get_by_email)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        def _get_by_username():
            return self.session.query(User).filter(User.username == username).first()
        
        return await asyncio.to_thread(_get_by_username)
    
    async def get_by_email_or_username(self, email: str, username: str) -> Optional[User]:
        def _get_by_email_or_username():
            return self.session.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
        
        return await asyncio.to_thread(_get_by_email_or_username)
    
    async def get_settings(self, user_id: UUID | str) -> Optional[UserSettings]:
        def _get_settings():
            return self.session.get(UserSettings, user_id)
        
        return await asyncio.to_thread(_get_settings)
    
    async def save_settings(self, settings: UserSettings) -> None:
        def _save_settings():
            self.session.add(settings)
            self.session.flush()
        
        await asyncio.to_thread(_save_settings)

