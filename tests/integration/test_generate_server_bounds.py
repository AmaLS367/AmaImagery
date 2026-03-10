import pytest

from app.config import settings

@pytest.mark.parametrize("w,h", [(settings.max_gen_width+1,512),(512,settings.max_gen_height+1)])
def test_size_upper_bound(app_client, w,h):
    r = app_client.post("/api/v1/images/generate", json={"prompt":"x", "width": w, "height": h, "steps": 10, "guidance_scale": 7.5})
    assert r.status_code in (400, 422)

def test_steps_upper_bound(app_client):
    r = app_client.post("/api/v1/images/generate", json={"prompt":"x", "width": 512, "height": 512, "steps": settings.max_gen_steps+1, "guidance_scale": 7.5})
    assert r.status_code in (400, 422)

def test_guidance_upper_bound(app_client):
    r = app_client.post("/api/v1/images/generate", json={"prompt":"x", "width": 512, "height": 512, "steps": 10, "guidance_scale": settings.max_guidance+1})
    assert r.status_code in (400, 422)
