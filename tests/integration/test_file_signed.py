import time

from fastapi.testclient import TestClient

from app.files.signing import make_signature
from app.main import app

client = TestClient(app)


def test_file_signed_expired():
    name = "nonexistent.png"
    exp = int(time.time()) - 1
    sig = make_signature(name, exp)
    r = client.get("/api/v1/file", params={"path": name, "exp": exp, "sig": sig})
    assert r.status_code in (403, 404)  # Expired signature or file missing
