"""
Unit of Work pattern for managing database transactions.

Provides a context manager that coordinates repositories and transaction boundaries.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import AsyncSessionLocal
from app.infra.repositories.generation_repository import SqlAlchemyGenerationRepository
from app.infra.repositories.user_repository import SqlAlchemyUserRepository
from app.domain.repositories import IUnitOfWork, IUserRepository, IGenerationRepository

logger = logging.getLogger(__name__)


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    Unit of Work implementation for async SQLAlchemy.
    
    Manages transaction boundaries and provides access to repositories.
    Commits on successful exit, rolls back on exceptions.
    """
    
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session: AsyncSession | None = session
        self._owns_session: bool = session is None
        self.users: IUserRepository
        self.generations: IGenerationRepository
    
    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        if self._session is None:
            self._session = AsyncSessionLocal()
        
        self.users = SqlAlchemyUserRepository(self._session)
        self.generations = SqlAlchemyGenerationRepository(self._session)
        
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            logger.error(f"Transaction failed: {exc_val}")
            await self.rollback()
        else:
            await self.commit()
        
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None
            
    async def commit(self) -> None:
        """
        Commits the current transaction.
        """
        if self._session:
            await self._session.commit()
            
    async def rollback(self) -> None:
        """
        Rolls back the current transaction.
        """
        if self._session:
            await self._session.rollback()


def get_uow(session: AsyncSession | None = None) -> SqlAlchemyUnitOfWork:
    """
    Dependency injection function for UnitOfWork.
    
    Returns a new UnitOfWork instance. If session is provided, it will be reused;
    otherwise, a new async session will be created and managed by the UnitOfWork.
    """
    return SqlAlchemyUnitOfWork(session=session)