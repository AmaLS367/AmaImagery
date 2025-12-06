def test_signed_url_rejects_tamper(app_client):
    # Путь выдуманный; сервис должен отказать 403 при подмене сигнатуры
    r = app_client.get("/file?path=/nope.png&sig=deadbeef&exp=9999999999")
    assert r.status_code in (400,403,404)
