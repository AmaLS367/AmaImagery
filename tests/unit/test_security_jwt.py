import pytest


def test_jwt_roundtrip():
    try:
        from app.core.security import create_access_token, decode_access_token
    except Exception:
        pytest.skip("security helpers недоступны")
    payload = {"sub": "user@example.com"}
    t, _ = create_access_token(sub="user@example.com")
    data = decode_access_token(t)
    assert data.get("sub") == "user@example.com"
    assert "exp" in data
