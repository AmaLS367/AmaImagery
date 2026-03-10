import fastapi
from fastapi.routing import APIRoute

from app.main import app


def fake_dep():
    raise fastapi.HTTPException(status_code=429, detail="rate limited")


def test_auth_rate_limited_simulated(app_client):
    overrides = {}
    for route in app.routes:
        if not isinstance(route, APIRoute) or route.path != "/api/v1/auth/login":
            continue
        for dependency in route.dependant.dependencies:
            if dependency.call is not None:
                overrides[dependency.call] = fake_dep
        break

    app.dependency_overrides.update(overrides)
    try:
        resp = app_client.post("/api/v1/auth/login", json={"identifier": "a@b.c", "password": "pass12345"})
        assert resp.status_code == 429
    finally:
        for dependency in overrides:
            app.dependency_overrides.pop(dependency, None)
