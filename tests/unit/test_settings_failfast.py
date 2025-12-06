import importlib

import pytest


def test_secret_key_required(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "")
    with pytest.raises(Exception):
        import app.main as main
        importlib.reload(main)
