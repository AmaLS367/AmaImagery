from typing import Any

from app.core.logging import sec as _sec


def sec(event: str, **fields: Any) -> None:
    _sec(event, **fields)
