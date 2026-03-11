"""
SQLAlchemy implementation of Generation repository.
"""

import builtins
from typing import Any
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
        return await self.session.get(Generation, _uuid_value(id))

    async def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> list[Generation]:
        stmt = select(Generation)

        for key, value in filters.items():
            if hasattr(Generation, key):
                stmt = stmt.filter(getattr(Generation, key) == _coerce_filter_value(key, value))

        # Apply default ordering
        stmt = stmt.order_by(desc(Generation.created_at))

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(Generation)

        for key, value in filters.items():
            if hasattr(Generation, key):
                stmt = stmt.filter(getattr(Generation, key) == _coerce_filter_value(key, value))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def delete(self, id: UUID | str) -> None:
        entity = await self.session.get(Generation, _uuid_value(id))
        if entity:
            await self.session.delete(entity)
            await self.session.flush()

    async def list_by_user(
        self, user_id: UUID | str, limit: int | None = None, offset: int = 0
    ) -> builtins.list[Generation]:
        stmt = (
            select(Generation).filter(Generation.user_id == _uuid_value(user_id)).order_by(desc(Generation.created_at))
        )

        if limit is not None:
            stmt = stmt.limit(limit)
        stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, id: UUID | str, status: str) -> None:
        entity = await self.session.get(Generation, _uuid_value(id))
        if entity and hasattr(entity, "status"):
            entity.status = status
            await self.session.flush()

    async def update_fields(self, id: UUID | str, **fields: Any) -> Generation | None:
        entity = await self.session.get(Generation, _uuid_value(id))
        if entity is None:
            return None
        for key, value in fields.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.session.flush()
        return entity

    async def count_by_user(self, user_id: UUID | str) -> int:
        stmt = select(func.count()).select_from(Generation).filter(Generation.user_id == _uuid_value(user_id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0


def _uuid_value(value: UUID | str) -> UUID | str:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except Exception:
        return value


def _coerce_filter_value(key: str, value: Any) -> Any:
    if key.endswith("_id") or key == "id":
        return _uuid_value(value)
    return value
