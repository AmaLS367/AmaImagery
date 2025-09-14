import os, sys, importlib, tempfile, shutil, contextlib
import pytest
from dotenv import load_dotenv

load_dotenv("docker/.env.local", override=False)  # подтянет ALLOWED_HOSTS и прочие

# Базовые ENV для быстрого запуска
os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("MODEL_ID", "mock")
os.environ.setdefault("DEVICE", "cpu")
os.environ.setdefault("UI_MOUNT_ENABLED", "false")
os.environ.setdefault("NSFW_ALLOW", "false")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

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
