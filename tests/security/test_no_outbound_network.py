import socket

from app.inference.net_guard import apply as net_guard_apply


def test_no_outbound_network_enabled(monkeypatch):
    monkeypatch.setenv("NO_NETWORK", "1")
    net_guard_apply()
    s = socket.socket()
    try:
        try:
            s.connect(("1.1.1.1", 80))
            raise AssertionError("connect must be blocked")
        except OSError:
            pass  # Expected to be blocked
    finally:
        s.close()
