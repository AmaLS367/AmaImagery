import pytest


def test_prompt_hash_stable():
    try:
        from app.utils import prompt_hash
    except Exception:
        pytest.skip("utils.prompt_hash not found")
    p = "test prompt"
    h1 = prompt_hash("test prompt", negative="")
    h2 = prompt_hash("test prompt", negative="")
    assert h1 == h2
    assert h1 != prompt_hash("test prompt ", negative="")
