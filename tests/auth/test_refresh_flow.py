import os

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
REFRESH_URL = f"{BASE_URL}/api/v1/auth/refresh"
LOGOUT_URL = f"{BASE_URL}/api/v1/auth/logout"
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")

IDENTIFIER = os.getenv("TEST_IDENTIFIER", "tester")
PASSWORD = os.getenv("TEST_PASSWORD", "pass12345")


def _get_cookie_value(client: httpx.Client, name: str) -> str | None:
    for c in client.cookies.jar:  # type: ignore[attr-defined]
        if c.name == name:
            return c.value
    return None


def test_refresh_flow_end_to_end():
    client = httpx.Client(timeout=10.0, follow_redirects=False)

    # 1) Login -> access token in JSON and refresh cookie in headers
    try:
        r = client.post(LOGIN_URL, json={"identifier": IDENTIFIER, "password": PASSWORD})
    except httpx.ConnectError as exc:
        pytest.skip(f"live server unavailable: {exc}")
    assert r.status_code == 200, f"login failed: {r.status_code}, {r.text}"
    data = r.json()
    assert isinstance(data.get("access_token", ""), str) and len(data["access_token"]) > 20
    rt1 = _get_cookie_value(client, REFRESH_COOKIE_NAME)
    assert rt1 and len(rt1) > 20, "refresh cookie not set"

    # 2) Standard refresh -> new access token and rotated refresh cookie
    r2 = client.post(REFRESH_URL)
    assert r2.status_code == 200, f"refresh-1 failed: {r2.status_code}, {r2.text}"
    data2 = r2.json()
    assert data2.get("access_token") and data2["access_token"] != data["access_token"]
    rt2 = _get_cookie_value(client, REFRESH_COOKIE_NAME)
    assert rt2 and rt2 != rt1, "refresh cookie did not rotate"

    # 3) Token reuse attempt with old cookie -> 401 and revoke token family
    rogue = httpx.Client(timeout=10.0, follow_redirects=False)
    rogue.cookies.set(REFRESH_COOKIE_NAME, rt1, domain="127.0.0.1", path="/api/v1/auth")
    r3 = rogue.post(REFRESH_URL)
    assert r3.status_code == 401, f"reuse must be 401, got {r3.status_code}"

    # After family revocation, newer rt2 must also be rejected
    r4 = client.post(REFRESH_URL)
    assert r4.status_code == 401, f"family should be revoked after reuse, got {r4.status_code}"

    # 4) Re-login -> new token family and fresh cookie
    r5 = client.post(LOGIN_URL, json={"identifier": IDENTIFIER, "password": PASSWORD})
    assert r5.status_code == 200
    rt_new = _get_cookie_value(client, REFRESH_COOKIE_NAME)
    assert rt_new and rt_new != rt2

    # 5) Logout: validate server-side revocation on separate client
    rt_live = _get_cookie_value(client, REFRESH_COOKIE_NAME)
    assert rt_live, "no RT before logout"

    client.post(LOGOUT_URL)

    rogue2 = httpx.Client(timeout=10.0, follow_redirects=False)
    rogue2.cookies.set(REFRESH_COOKIE_NAME, rt_live, domain="127.0.0.1", path="/api/v1/auth")
    r7 = rogue2.post(REFRESH_URL)
    assert r7.status_code == 401, f"refresh after logout must be 401, got {r7.status_code}"
