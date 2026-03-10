def test_signed_url_rejects_tamper(app_client):
    tampered_sig = "deadbeef" * 8
    r = app_client.get(f"/api/v1/file?path=nope.png&sig={tampered_sig}&exp=9999999999")
    assert r.status_code in (400, 403, 404)
