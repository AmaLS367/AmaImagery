"""
SQLAlchemy implementation of Generation repository.
"""

from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.domain.models import Generation
from app.domain.repositories import IGenerationRepository


class SqlAlchemyGenerationRepository:
    """
    SQLAlchemy implementation of Generation repository.
    
    Uses async Session for non-blocking database operations.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, entity: Generation) -> None:
        self.session.add(entity)
        await self.session.flush()
    
    async def get(self, id: UUID | str) -> Optional[Generation]:
        return await self.session.get(Generation, id)
    
    async def list(self, **filters: Any) -> List[Generation]:
        stmt = select(Generation)
        for key, value in filters.items():
            stmt = stmt.filter(getattr(Generation, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete(self, id: UUID | str) -> None:
        entity = await self.session.get(Generation, id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
    
    async def list_by_user(self, user_id: UUID | str, limit: Optional[int] = None, offset: int = 0) -> List[Generation]:
        stmt = select(Generation).filter(
            Generation.user_id == user_id
        ).order_by(desc(Generation.created_at))
        
        if limit is not None:
            stmt = stmt.limit(limit)
        stmt = stmt.offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_status(self, id: UUID | str, status: str) -> None:
        entity = await self.session.get(Generation, id)
        if entity and hasattr(entity, 'status'):
            entity.status = status
            await self.session.flush()
    
    async def count_by_user(self, user_id: UUID | str) -> int:
        stmt = select(func.count()).select_from(Generation).filter(
            Generation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
