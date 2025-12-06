
import pytest


@pytest.mark.e2e
def test_health_and_generate(app_client):
    r = app_client.get("/healthz")
    assert r.status_code == 200
    r = app_client.post("/generate", json={"prompt":"test","steps":5,"width":256,"height":256})
    assert r.status_code in (200,201)
