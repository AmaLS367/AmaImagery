import io, logging, pytest
from app.core.logging import setup_logging, logger

def test_auth_header_masking(capsys):
    setup_logging()
    logger.bind(event_type="app").info("Authorization: Bearer abcdef.123456")
    out = capsys.readouterr().out
    assert "Bearer ***" in out
    assert "abcdef.123456" not in out
