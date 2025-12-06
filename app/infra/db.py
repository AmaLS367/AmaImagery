from __future__ import annotations
import subprocess
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine.url import make_url
from app.config import settings


def _make_async_url(url: str) -> str:
    """
    Converts sync database URL to async URL.
    
    Replaces postgresql:// with postgresql+asyncpg:// for async driver.
    For SQLite, uses aiosqlite driver.
    """
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("sqlite+aiosqlite:///"):
        return url
    if url.startswith("postgresql+asyncpg://"):
        return url
    return url


async_engine = create_async_engine(
    _make_async_url(settings.database_url),
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    """
    Dependency for FastAPI to get async database session.
    
    Yields an async session and closes it after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def run_pending_migrations() -> None:
    backend = make_url(settings.database_url).get_backend_name()
    if backend not in ("postgresql", "postgresql+psycopg", "postgresql+psycopg2"):
        raise RuntimeError("Only PostgreSQL is supported for pending migrations. Set DATABASE_URL to Postgres.")
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Alembic failed: {r.stdout}\n{r.stderr}")

