import importlib
import os
import sys


def _reload_safety(nsrm: str):
    os.environ["NSFW_ALLOW"] = nsrm
    importlib.invalidate_caches()

    # Reload config to pick up new environment variables
    if "app.config" in sys.modules:
        importlib.reload(sys.modules["app.config"])
    else:
        importlib.import_module("app.config")

    # Reload core.safety (main safety module)
    if "app.core.safety" in sys.modules:
        importlib.reload(sys.modules["app.core.safety"])
    else:
        importlib.import_module("app.core.safety")

    # Clear safety cache after reload
    safety_module = sys.modules["app.core.safety"]
    if hasattr(safety_module, "reload_rules"):
        safety_module.reload_rules()

    return safety_module


def test_blocklist_respects_allow_flag():
    safety = _reload_safety("false")
    assert safety.is_blocked("bestiality") is True
    assert safety.is_blocked("a cute cat") is False

    safety = _reload_safety("true")
    assert safety.is_blocked("bestiality") is False
    assert safety.is_blocked_forced("bestiality") is True


def test_blocklist_forced_always_checks():
    safety = _reload_safety("true")
    assert safety.is_blocked_forced("gore content") is True
    assert safety.is_blocked_forced("landscape") is False
