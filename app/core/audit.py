import logging
from datetime import datetime, timezone
from typing import Any, Dict

_security = logging.getLogger("security")

def sec(event: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    payload.update(fields)
    _security.info(payload)
