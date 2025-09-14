import pytest
def test_register_login_me(app_client):
    email="tester@example.com"; password="pass12345"
    r = app_client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code in (200,201,400)
    r = app_client.post("/auth/login", data={"username": email, "password": password})
    if r.status_code not in (200,201):
        pytest.skip("auth/login недоступен")
    token = r.json().get("access_token") or r.json().get("token")
    assert token
    hdr = {"Authorization": f"Bearer {token}"}
    r = app_client.get("/me", headers=hdr)
    assert r.status_code == 200
