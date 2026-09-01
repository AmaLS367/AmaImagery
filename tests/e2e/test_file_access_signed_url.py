import pytest


@pytest.mark.e2e
def test_signed_file_link(app_client):
    # Verify file access requires a valid signature
    r = app_client.get("/api/v1/file?path=foo.png")
    assert r.status_code in (400, 403, 404, 422)
