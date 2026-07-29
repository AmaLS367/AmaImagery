import fastapi
from fastapi.routing import APIRoute

from app.api.v1.auth.router import router as auth_router
from app.main import app


def fake_dep():
    raise fastapi.HTTPException(status_code=429, detail="rate limited")


def test_auth_rate_limited_simulated(app_client):
    login_route = next(route for route in auth_router.routes if isinstance(route, APIRoute) and route.path == "/login")
    overrides = {
        dependency.call: fake_dep for dependency in login_route.dependant.dependencies if dependency.call is not None
    }

    app.dependency_overrides.update(overrides)
    try:
        resp = app_client.post("/api/v1/auth/login", json={"identifier": "a@b.c", "password": "pass12345"})
        assert resp.status_code == 429
    finally:
        for dependency in overrides:
            app.dependency_overrides.pop(dependency, None)
