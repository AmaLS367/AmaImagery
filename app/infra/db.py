from __future__ import annotations

import subprocess  # nosec B404
import sys
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


def _make_async_url(url: str) -> str:
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


def _build_engine_kwargs(url: str) -> dict[str, Any]:
    backend = make_url(url).get_backend_name()
    kwargs: dict[str, Any] = {
        "pool_pre_ping": True,
        "echo": False,
    }

    if backend == "sqlite":
        # File-backed SQLite is heavily used in local tests. A pooled async
        # connection can keep the database locked between fixture resets on
        # Windows, so prefer one-shot connections for sqlite URLs.
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 5}
        kwargs["poolclass"] = NullPool
        kwargs["pool_pre_ping"] = False
    elif backend.startswith("postgres") and settings.debug:
        # TestClient and ad-hoc asyncio.run() calls in debug/test workflows can
        # cross event-loop boundaries. Avoid reusing asyncpg connections there.
        kwargs["poolclass"] = NullPool
        kwargs["pool_pre_ping"] = False

    return kwargs


async_engine = create_async_engine(
    _make_async_url(settings.database_url),
    **_build_engine_kwargs(settings.database_url),
)

AsyncSessionLocal = async_sessionmaker[AsyncSession](
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
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
    """
    Applies pending database migrations using Alembic.

    Executed via subprocess to ensure isolation from the running asyncio loop,
    preventing 'Event loop is already running' errors common with async Alembic env.py.
    """
    backend = make_url(settings.database_url).get_backend_name()

    # Strict production requirement: PostgreSQL only
    if not backend.startswith("postgres"):
        raise RuntimeError(f"Migrations are strictly restricted to PostgreSQL (current: {backend}).")

    try:
        r = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(settings.root_dir),
        )  # nosec B603
        if r.returncode != 0:
            raise RuntimeError(f"Alembic migration failed (code {r.returncode}):\n{r.stdout}\n{r.stderr}")

    except FileNotFoundError as exc:
        raise RuntimeError("Python executable not found for migration subprocess.") from exc
    except Exception as e:
        raise RuntimeError(f"Failed to launch migration subprocess: {e}") from e
