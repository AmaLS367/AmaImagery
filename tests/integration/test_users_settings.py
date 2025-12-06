import pytest


def test_patch_user_settings(app_client, auth_headers):
    r = app_client.get("/me/settings", headers=auth_headers)
    if r.status_code != 200:
        pytest.skip("/me/settings недоступен")
    s = r.json()
    new = {"nsfw_allow": not s.get("nsfw_allow", False)}
    r = app_client.patch("/me/settings", json=new, headers=auth_headers)
    assert r.status_code in (200,204)
