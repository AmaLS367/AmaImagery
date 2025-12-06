from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_docs_off_in_prod():
    r = client.get("/docs")
    assert r.status_code in (404, 403)
    r = client.get("/openapi.json")
    assert r.status_code in (404, 403)

def test_cors_negative_preflight():
    # Запрещённый Origin — не должен отражаться обратно
    r = client.options("/api/healthz", headers={
        "Origin": "http://evil",
        "Access-Control-Request-Method": "GET",
    })
    assert "access-control-allow-origin" not in r.headers
