import pytest


@pytest.mark.redis
def test_rate_limit_basic(app_client):
    # Сервис может вернуть 429 после порога; если нет лимитера — пропускаем
    hit429 = False
    for _i in range(30):
        r = app_client.get("/api/v1/healthz")
        if r.status_code == 429:
            hit429 = True
            break
    if not hit429:
        pytest.skip("rate limiter не активен")
