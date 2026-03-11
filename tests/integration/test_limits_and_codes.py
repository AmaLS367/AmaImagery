from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_wrong_method_returns_404_or_405() -> None:
    response = client.get("/api/v1/auth/register")
    assert response.status_code in (404, 405)


def test_generate_request_rejects_oversized_body() -> None:
    oversized_prompt = "x" * (26_214_400 + 1)
    response = client.post(
        "/api/v1/images/generate",
        json={
            "prompt": oversized_prompt,
            "width": 256,
            "height": 256,
            "steps": 5,
            "guidance_scale": 7.5,
        },
    )
    assert response.status_code == 413
