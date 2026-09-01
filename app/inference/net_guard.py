"""
Network guard module to block outbound network connections.

This module patches socket connections to prevent ML models from accessing
the internet while allowing local connections (localhost, 127.0.0.1).
Useful for security and ensuring models run in offline mode.
"""

import os
import socket
from typing import Any, cast

_APPLIED = False

_OrigConnect = socket.socket.connect
_OrigConnectEx = socket.socket.connect_ex
_OrigCreateConn = socket.create_connection


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "dev", "debug", "development"}


def _blocked_connect(self: socket.socket, address: Any) -> None:
    """Block outbound connections except to localhost."""
    host = address[0] if isinstance(address, (tuple, list)) and address else address
    if isinstance(host, str) and host in {"127.0.0.1", "localhost", "::1"}:
        if isinstance(address, list):
            address = tuple(address)
        return _OrigConnect(self, address)
    raise OSError("Outbound network is disabled by net_guard")


def _blocked_connect_ex(self: socket.socket, address: Any) -> int:
    """Block outbound connections (connect_ex variant)."""
    try:
        _blocked_connect(self, address)
        return 0
    except OSError:
        return 111  # Connection refused


def _blocked_create_connection(*a: Any, **k: Any) -> Any:
    """Block socket.create_connection()."""
    raise OSError("Outbound network is disabled by net_guard")


def apply() -> None:
    """Apply network blocking patches"""
    global _APPLIED
    if _APPLIED:
        return

    # Import settings here to avoid circular dependency
    from app.config import settings

    if not _env_bool("NO_NETWORK", settings.no_network):
        return

    # Patch socket methods
    socket_class = cast(Any, socket.socket)
    socket_module = cast(Any, socket)
    socket_class.connect = _blocked_connect
    socket_class.connect_ex = _blocked_connect_ex
    socket_module.create_connection = _blocked_create_connection

    # Set environment variables for ML libraries to use offline mode
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    _APPLIED = True


def restore() -> None:
    global _APPLIED
    if not _APPLIED:
        return
    socket_class = cast(Any, socket.socket)
    socket_module = cast(Any, socket)
    socket_class.connect = _OrigConnect
    socket_class.connect_ex = _OrigConnectEx
    socket_module.create_connection = _OrigCreateConn
    _APPLIED = False
