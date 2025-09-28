import os, socket

_APPLIED = False

_OrigConnect = socket.socket.connect
_OrigConnectEx = socket.socket.connect_ex
_OrigCreateConn = socket.create_connection

def _blocked_connect(self, address):
    host = address[0] if isinstance(address, (tuple, list)) and address else address
    if isinstance(host, str) and host in {"127.0.0.1", "localhost", "::1"}:
        return _OrigConnect(self, address)
    raise OSError("Outbound network is disabled")

def _blocked_connect_ex(self, address):
    try:
        _blocked_connect(self, address)
        return 0
    except OSError:
        return 111 

def _blocked_create_connection(*a, **k):
    raise OSError("Outbound network is disabled")

def apply():
    global _APPLIED
    if _APPLIED or os.getenv("NO_NETWORK", "0").lower() not in ("1","true","yes"):
        return
    socket.socket.connect = _blocked_connect        
    socket.socket.connect_ex = _blocked_connect_ex  
    socket.create_connection = _blocked_create_connection  
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    _APPLIED = True

def restore():
    global _APPLIED
    if not _APPLIED:
        return
    socket.socket.connect = _OrigConnect    
    socket.socket.connect_ex = _OrigConnectEx 
    socket.create_connection = _OrigCreateConn
    _APPLIED = False

