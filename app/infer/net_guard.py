"""
Процессный сетевой «предохранитель»: при NO_NETWORK=1 запрещает любые TCP-соединения.
Работает для requests/urllib3/хаба HF, т.к. обрубает socket.connect().
"""
import os, socket

_APPLIED = False
_OrigSocket = socket.socket
_OrigCreateConn = socket.create_connection

class _BlockedSocket(socket.socket):
    def connect(self, *args, **kwargs):  # type: ignore
        raise OSError("Outbound network is disabled")
    def connect_ex(self, *args, **kwargs):  # type: ignore
        return 111  # ECONNREFUSED

def apply():
    global _APPLIED
    if _APPLIED or os.getenv("NO_NETWORK", "1") not in ("1","true","yes"):
        return
    socket.socket = _BlockedSocket  # type: ignore
    socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(OSError("Outbound network is disabled"))  # type: ignore
    # дубль: переменные оффлайна для HF/Transformers
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    _APPLIED = True
