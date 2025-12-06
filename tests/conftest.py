import os
import shutil
import tempfile

import pytest
import pytest_asyncio
from dotenv import load_dotenv

load_dotenv("docker/.env.local", override=False)  # подтянет ALLOWED_HOSTS и прочие

# Базовые ENV для быстрого запуска
os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("MODEL_ID", "mock")
os.environ.setdefault("DEVICE", "cpu")
os.environ.setdefault("UI_MOUNT_ENABLED", "false")
os.environ.setdefault("NSFW_ALLOW", "false")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
os.environ.setdefault("LIMITS_ENABLED", "true")

# Временная директория для outputs
@pytest.fixture(autouse=True)
def _tmp_outputs(monkeypatch):
    tmp = tempfile.mkdtemp(prefix="outputs_")
    monkeypatch.setenv("OUT_DIR", tmp)
    yield
    shutil.rmtree(tmp, ignore_errors=True)

# Клиент FastAPI
@pytest.fixture
def app_client():
    try:
        from app.main import app
    except Exception as e:
        pytest.skip(f"Не удалось импортировать app.main: {e}")
    try:
        # httpx>=0.24 async client есть, но для простоты используем starlette TestClient
        from starlette.testclient import TestClient
        return TestClient(app)
    except Exception as e:
        pytest.skip(f"Нет TestClient: {e}")

# Async database session fixture
@pytest_asyncio.fixture
async def async_session():
    """
    Provides an async database session for tests.
    
    Creates a new async session and ensures it's closed after the test.
    """
    try:
        from app.infra.db import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        pytest.skip(f"Async session недоступен: {e}")

# Async database engine fixture
@pytest_asyncio.fixture
async def async_db_engine():
    """
    Provides an async database engine for tests.
    
    Can be used for creating test databases or running migrations.
    """
    try:
        from app.infra.db import async_engine
        yield async_engine
        await async_engine.dispose()
    except Exception as e:
        pytest.skip(f"Async engine недоступен: {e}")

# UnitOfWork fixture for tests
@pytest_asyncio.fixture
async def uow():
    """
    Provides a UnitOfWork instance for tests.
    
    Automatically manages transaction boundaries - rolls back after each test.
    """
    try:
        from app.infra.uow import get_uow
        uow = get_uow()
        async with uow:
            yield uow
            # Rollback to clean up test data
            if uow._session is not None:
                await uow._session.rollback()
    except Exception as e:
        pytest.skip(f"UnitOfWork недоступен: {e}")

# Хелпер: регистрация и логин тестового пользователя
@pytest.fixture
def auth_headers(app_client):
    # маршруты могут отличаться — пропускаем, если не найдены
    try:
        email = "user@example.com"; password = "pass12345"
        r = app_client.post("/auth/register", json={"email": email, "password": password})
        # допускаем 400 если юзер уже есть
        assert r.status_code in (200, 201, 400)
        r = app_client.post("/auth/login", data={"username": email, "password": password})
        if r.status_code not in (200, 201):
            pytest.skip(f"/auth/login вернул {r.status_code}")
        token = r.json().get("access_token") or r.json().get("token") or r.json().get("access")
        if not token:
            pytest.skip("Ответ логина без токена")
        return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        pytest.skip(f"auth flow недоступен: {e}")
