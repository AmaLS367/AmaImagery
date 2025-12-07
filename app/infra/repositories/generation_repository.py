"""
SQLAlchemy implementation of Generation repository.
"""

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Generation
from app.domain.repositories import IGenerationRepository


class SqlAlchemyGenerationRepository(IGenerationRepository):
    """
    SQLAlchemy implementation of Generation repository.
    
    Uses async Session for non-blocking database operations.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def add(self, entity: Generation) -> None:
        self.session.add(entity)
        await self.session.flush()
    
    async def get(self, id: UUID | str) -> Generation | None:
        return await self.session.get(Generation, id)
    
    async def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> List[Generation]:
        stmt = select(Generation)
        
        for key, value in filters.items():
            if hasattr(Generation, key):
                stmt = stmt.filter(getattr(Generation, key) == value)
        
        # Apply default ordering
        stmt = stmt.order_by(desc(Generation.created_at))
        
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(Generation)
        
        for key, value in filters.items():
            if hasattr(Generation, key):
                stmt = stmt.filter(getattr(Generation, key) == value)
                
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
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
            setattr(entity, 'status', status)  # type: ignore[attr-defined]
            await self.session.flush()
    
    async def count_by_user(self, user_id: UUID | str) -> int:
        stmt = select(func.count()).select_from(Generation).filter(
            Generation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0