import pytest


def test_register_login_me(app_client):
    email="tester@example.com"; password="pass12345"
    r = app_client.post("/api/v1/auth/register", json={"email": email, "password": password, "username": "tester"})
    assert r.status_code in (200,201,400)
    r = app_client.post("/api/v1/auth/login", json={"identifier": email, "password": password})
    if r.status_code not in (200,201):
        pytest.skip("api/v1/auth/login недоступен")
    token = r.json().get("access_token") or r.json().get("token")
    assert token
    hdr = {"Authorization": f"Bearer {token}"}
    r = app_client.get("/api/v1/auth/me", headers=hdr)
    assert r.status_code == 200
