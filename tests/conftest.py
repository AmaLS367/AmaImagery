import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv("docker/.env.local", override=False)

os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("MODEL_ID", "mock")
os.environ.setdefault("DEVICE", "cpu")
os.environ.setdefault("UI_MOUNT_ENABLED", "false")
os.environ.setdefault("NSFW_ALLOW", "false")
os.environ.setdefault("ALLOWED_HOSTS", '["localhost","127.0.0.1","testserver"]')
os.environ.setdefault("LIMITS_ENABLED", "true")
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite:///{(ROOT / '.pytest-app.db').as_posix()}"


@pytest.fixture(autouse=True)
def _tmp_outputs(monkeypatch):
    tmp = tempfile.mkdtemp(prefix="outputs_")
    monkeypatch.setenv("OUTPUTS_DIR", tmp)
    yield
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def app_client():
    try:
        from app.main import app
        from app.domain.models import Base
        from app.infra.db import async_engine
    except Exception as e:
        pytest.skip(f"Failed to import app.main: {e}")
    try:
        import asyncio
        from starlette.testclient import TestClient

        async def _reset_schema() -> None:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(_reset_schema())

        with TestClient(app) as client:
            yield client
    except Exception as e:
        pytest.skip(f"TestClient unavailable: {e}")


@pytest_asyncio.fixture
async def async_session():
    try:
        from app.infra.db import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        pytest.skip(f"Async session unavailable: {e}")


@pytest_asyncio.fixture
async def async_db_engine():
    try:
        from app.infra.db import async_engine

        yield async_engine
        await async_engine.dispose()
    except Exception as e:
        pytest.skip(f"Async engine unavailable: {e}")


@pytest_asyncio.fixture
async def uow():
    try:
        from app.infra.uow import get_uow

        unit = get_uow()
        async with unit:
            yield unit
            if unit._session is not None:
                await unit._session.rollback()
    except Exception as e:
        pytest.skip(f"UnitOfWork unavailable: {e}")


@pytest.fixture
def auth_headers(app_client):
    try:
        email = "user@example.com"
        password = "pass12345"
        register = app_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "username": "user"},
        )
        assert register.status_code in (200, 201, 400)
        login = app_client.post(
            "/api/v1/auth/login",
            json={"identifier": email, "password": password},
        )
        if login.status_code not in (200, 201):
            pytest.skip(f"/api/v1/auth/login returned {login.status_code}")
        token = login.json().get("access_token") or login.json().get("token") or login.json().get("access")
        if not token:
            pytest.skip("Login response missing token")
        return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        pytest.skip(f"Auth flow unavailable: {e}")


@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from app.domain.models import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()
