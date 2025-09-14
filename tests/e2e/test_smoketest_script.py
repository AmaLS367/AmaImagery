import os, subprocess, sys, pytest
@pytest.mark.e2e
def test_smoke_script_exists():
    # Просто проверим наличие твоего smoke-скрипта
    ok = os.path.exists("scripts/linux/smoketest.sh") or os.path.exists("scripts/windows/smoketest.ps1")
    assert ok
