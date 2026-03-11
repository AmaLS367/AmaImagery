
import pytest


@pytest.mark.e2e
def test_health_and_generate(app_client):
    alive = app_client.get("/api/v1/health")
    assert alive.status_code == 200
    assert alive.json()["status"] == "alive"

    r = app_client.get("/api/v1/healthz")
    if r.status_code == 503:
        payload = r.json()
        assert payload["status"] == "not_ready"
        assert payload["generation_ready"] is False
        pytest.skip("Generation provider is not ready in the current test environment.")

    assert r.status_code == 200
    r = app_client.post("/api/v1/images/generate", json={"prompt":"test","steps":5,"width":256,"height":256})
    assert r.status_code in (200,201)
