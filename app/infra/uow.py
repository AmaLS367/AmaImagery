"""
Unit of Work pattern for managing database transactions.

Provides a context manager that coordinates repositories and transaction boundaries.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import AsyncSessionLocal
from app.infra.repositories import SqlAlchemyGenerationRepository, SqlAlchemyUserRepository
from app.domain.repositories import IGenerationRepository, IUserRepository


class SqlAlchemyUnitOfWork:
    """
    Unit of Work implementation for async SQLAlchemy.
    
    Manages transaction boundaries and provides access to repositories.
    Commits on successful exit, rolls back on exceptions.
    """
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self._session: Optional[AsyncSession] = session
        self._owns_session = session is None
        self.users: IUserRepository
        self.generations: IGenerationRepository
    
    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        if self._session is None:
            self._session = AsyncSessionLocal()
        
        self.users = SqlAlchemyUserRepository(self._session)
        self.generations = SqlAlchemyGenerationRepository(self._session)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._session.commit()
        else:
            await self._session.rollback()
        
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None
        
        return False


def get_uow(session: Optional[AsyncSession] = None) -> SqlAlchemyUnitOfWork:
    """
    Dependency injection function for UnitOfWork.
    
    Returns a new UnitOfWork instance. If session is provided, it will be reused;
    otherwise, a new async session will be created and managed by the UnitOfWork.
    """
    return SqlAlchemyUnitOfWork(session=session)

