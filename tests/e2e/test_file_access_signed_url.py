import pytest


@pytest.mark.e2e
def test_signed_file_link(app_client):
    # Если сервис возвращает подписанные ссылки, проверим доступ
    # Здесь проверяем, что без валидной сигнатуры доступ закрыт
    r = app_client.get("/file?path=/tmp/foo.png")
    assert r.status_code in (400,403,404,422)
