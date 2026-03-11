import importlib

import pytest
from pydantic import ValidationError


def test_secret_key_required(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "")
    with pytest.raises((ValidationError, RuntimeError)):
        import app.config as cfg
        import app.main as main

        importlib.reload(cfg)
        importlib.reload(main)
