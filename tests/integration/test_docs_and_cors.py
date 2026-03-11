from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_docs_off_in_prod():
    r = client.get("/docs")
    if settings.docs_url:
        assert r.status_code == 200
    else:
        assert r.status_code in (404, 403)
    r = client.get("/openapi.json")
    if settings.docs_url:
        assert r.status_code == 200
    else:
        assert r.status_code in (404, 403)


def test_cors_negative_preflight():
    # Запрещённый Origin — не должен отражаться обратно
    r = client.options(
        "/api/v1/healthz",
        headers={
            "Origin": "http://evil",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in r.headers
