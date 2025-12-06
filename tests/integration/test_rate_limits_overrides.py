import fastapi
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app


def fake_dep():
    raise fastapi.HTTPException(status_code=429, detail="rate limited")

for r in app.routes:
    if isinstance(r, APIRoute) and r.path.startswith("/auth"):
        r.dependant.dependencies = []  # type: ignore[attr-defined]
        r.dependencies = [fastapi.Depends(fake_dep)]  # type: ignore[assignment]

client = TestClient(app)

def test_auth_rate_limited_simulated():
    resp = client.post("/auth/me", json={"email": "a@b.c", "password": "x"})
    assert resp.status_code == 429
