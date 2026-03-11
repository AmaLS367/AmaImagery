import re

from app.core.logging import logger, setup_logging


def test_log_redacts_tokens(capsys):
    setup_logging()
    logger.info("Authorization: Bearer abc.def.ghi; Set-Cookie: session=abcdef")
    out = capsys.readouterr().err
    assert "Authorization: Bearer ****" in out
    assert re.search(r"Set-Cookie:\s*session=\*{3,}", out)
