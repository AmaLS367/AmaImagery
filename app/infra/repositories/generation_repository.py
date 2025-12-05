"""
SQLAlchemy implementation of Generation repository.
"""

import asyncio
from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domain.models import Generation
from app.domain.repositories import IGenerationRepository


class SqlAlchemyGenerationRepository:
    """
    SQLAlchemy implementation of Generation repository.
    
    Uses synchronous Session internally, wrapping DB calls in asyncio.to_thread
    to avoid blocking the event loop.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    async def add(self, entity: Generation) -> None:
        def _add():
            self.session.add(entity)
            self.session.flush()
        
        await asyncio.to_thread(_add)
    
    async def get(self, id: UUID | str) -> Optional[Generation]:
        def _get():
            return self.session.get(Generation, id)
        
        return await asyncio.to_thread(_get)
    
    async def list(self, **filters: Any) -> List[Generation]:
        def _list():
            query = self.session.query(Generation)
            for key, value in filters.items():
                query = query.filter(getattr(Generation, key) == value)
            return query.all()
        
        return await asyncio.to_thread(_list)
    
    async def delete(self, id: UUID | str) -> None:
        def _delete():
            entity = self.session.get(Generation, id)
            if entity:
                self.session.delete(entity)
                self.session.flush()
        
        await asyncio.to_thread(_delete)
    
    async def list_by_user(self, user_id: UUID | str, limit: Optional[int] = None, offset: int = 0) -> List[Generation]:
        def _list_by_user():
            query = self.session.query(Generation).filter(
                Generation.user_id == user_id
            ).order_by(desc(Generation.created_at))
            
            if limit is not None:
                query = query.limit(limit)
            query = query.offset(offset)
            
            return query.all()
        
        return await asyncio.to_thread(_list_by_user)
    
    async def update_status(self, id: UUID | str, status: str) -> None:
        def _update_status():
            entity = self.session.get(Generation, id)
            if entity and hasattr(entity, 'status'):
                entity.status = status
                self.session.flush()
        
        await asyncio.to_thread(_update_status)
    
    async def count_by_user(self, user_id: UUID | str) -> int:
        def _count_by_user():
            return self.session.query(Generation).filter(
                Generation.user_id == user_id
            ).count()
        
        return await asyncio.to_thread(_count_by_user)
