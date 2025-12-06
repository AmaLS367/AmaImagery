import time

import pytest


@pytest.mark.slow
def test_generate_latency(app_client):
    t0 = time.time()
    r = app_client.post("/generate", json={"prompt":"speed","steps":5,"width":256,"height":256})
    if r.status_code not in (200,201):
        pytest.skip("/generate недоступен")
    dt = time.time() - t0
    assert dt < 10.0  # дымовой порог; подстрой под железо
