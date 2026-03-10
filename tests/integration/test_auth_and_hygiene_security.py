def test_query_token_auth_is_rejected(app_client, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]

    response = app_client.get(f"/api/v1/auth/me?access_token={token}")

    assert response.status_code == 401


def test_hygiene_mode_requires_auth(app_client):
    response = app_client.get("/api/v1/users/me/hygiene-mode")

    assert response.status_code == 401


def test_hygiene_mode_is_owner_scoped(app_client, auth_headers):
    get_response = app_client.get("/api/v1/users/me/hygiene-mode", headers=auth_headers)
    assert get_response.status_code == 200
    user_id = get_response.json()["user_id"]

    patch_response = app_client.patch(
        "/api/v1/users/me/hygiene-mode",
        headers=auth_headers,
        json={"mode": "AUTO"},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["user_id"] == user_id
    assert patch_response.json()["mode"] == "AUTO"
