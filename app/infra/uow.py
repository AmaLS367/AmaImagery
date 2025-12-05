"""
Unit of Work pattern for managing database transactions.

Provides a context manager that coordinates repositories and transaction boundaries.
"""

import asyncio
from typing import Optional

from sqlalchemy.orm import Session

from app.infra.db import SessionLocal
from app.infra.repositories import SqlAlchemyGenerationRepository, SqlAlchemyUserRepository
from app.domain.repositories import IGenerationRepository, IUserRepository


class SqlAlchemyUnitOfWork:
    """
    Unit of Work implementation for SQLAlchemy.
    
    Manages transaction boundaries and provides access to repositories.
    Commits on successful exit, rolls back on exceptions.
    """
    
    def __init__(self, session: Optional[Session] = None):
        self._session: Optional[Session] = session
        self._owns_session = session is None
        self.users: IUserRepository
        self.generations: IGenerationRepository
    
    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        if self._session is None:
            self._session = SessionLocal()
        
        self.users = SqlAlchemyUserRepository(self._session)
        self.generations = SqlAlchemyGenerationRepository(self._session)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            def _commit():
                self._session.commit()
            await asyncio.to_thread(_commit)
        else:
            def _rollback():
                self._session.rollback()
            await asyncio.to_thread(_rollback)
        
        if self._owns_session and self._session:
            def _close():
                self._session.close()
            await asyncio.to_thread(_close)
            self._session = None
        
        return False


def get_uow(session: Optional[Session] = None) -> SqlAlchemyUnitOfWork:
    """
    Dependency injection function for UnitOfWork.
    
    Returns a new UnitOfWork instance. If session is provided, it will be reused;
    otherwise, a new session will be created and managed by the UnitOfWork.
    """
    return SqlAlchemyUnitOfWork(session=session)

