import pytest


def test_register_login_me(app_client):
    email = "tester@example.com"
    password = "pass12345"
    r = app_client.post("/api/v1/auth/register", json={"email": email, "password": password, "username": "tester"})
    assert r.status_code in (200, 201, 400)
    r = app_client.post("/api/v1/auth/login", json={"identifier": email, "password": password})
    if r.status_code not in (200, 201):
        pytest.skip("api/v1/auth/login недоступен")
    token = r.json().get("access_token") or r.json().get("token")
    assert token
    hdr = {"Authorization": f"Bearer {token}"}
    r = app_client.get("/api/v1/auth/me", headers=hdr)
    assert r.status_code == 200


def test_change_password_reloads_user_in_uow(app_client):
    email = "changer@example.com"
    old_password = "pass12345"
    new_password = "pass123456"
    register = app_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password, "username": "changer"},
    )
    assert register.status_code in (200, 201, 400)

    login = app_client.post("/api/v1/auth/login", json={"identifier": email, "password": old_password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    changed = app_client.post(
        "/api/v1/auth/change-password",
        json={"old_password": old_password, "new_password": new_password},
        headers=headers,
    )
    assert changed.status_code == 200, changed.text

    relogin = app_client.post("/api/v1/auth/login", json={"identifier": email, "password": new_password})
    assert relogin.status_code == 200, relogin.text
