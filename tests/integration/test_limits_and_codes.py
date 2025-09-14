from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_405_wrong_method():
    r = client.get("/auth/register")  # у тебя POST
    assert r.status_code in (404, 405)

def test_413_large_body(monkeypatch):
    big = b"x" * (26214400 + 1)
    r = client.post(
        "/upload",
        files={"file": ("big.bin", big, "application/octet-stream")},
    )
    assert r.status_code in (400, 413, 422)
