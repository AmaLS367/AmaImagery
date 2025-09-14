import os, time, pytest, importlib
from app.files.signing import make_signature, verify_signature

def test_signed_link_ok():
    name = "x.png"
    exp = int(time.time()) + 5
    sig = make_signature(name, exp)
    assert verify_signature(name, exp, sig)

def test_signed_link_expired():
    name = "x.png"
    exp = int(time.time()) - 1
    sig = make_signature(name, exp)
    assert not verify_signature(name, exp, sig)

def test_settings_failfast_secret_key_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://app:pass@postgres:5432/appdb")
    monkeypatch.setenv("REDIS_URL", "redis://:pass@redis:6379/0")
    monkeypatch.setenv("RUN_IN_DOCKER", "1")
    import app.config as cfg
    with pytest.raises(RuntimeError):
        importlib.reload(cfg)  # внутри модуля создаётся settings = Settings() и падает без SECRET_KEY
