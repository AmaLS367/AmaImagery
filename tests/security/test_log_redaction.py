import re
import sys
from io import StringIO

from app.core.logging import logger


def test_log_redacts_tokens(monkeypatch):
    buf = StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    logger.info("Authorization: Bearer abc.def.ghi; Set-Cookie: session=abcdef")
    out = buf.getvalue()
    assert "Authorization: Bearer ****" in out
    assert re.search(r"Set-Cookie:\s*session=\*{3,}", out)
