import hmac, time
from hashlib import sha256
from typing import Optional
from app.config import settings

def _payload(name: str, exp: int) -> bytes:
    return f"{name}.{exp}".encode("utf-8")

def make_signature(name: str, exp: int) -> str:
    key = settings.secret_key.encode("utf-8")
    return hmac.new(key, _payload(name, exp), sha256).hexdigest()

def verify_signature(name: str, exp: int, sig: str) -> bool:
    if exp < int(time.time()):
        return False
    expected = make_signature(name, exp)
    try:
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False

async def consume_once(redis, sig: str, ttl: int) -> bool:
    if not settings.file_single_use:
        return True
    # setnx = True → первый доступ, False → повтор
    ok = await redis.setnx(f"filedl:{sig}", "1")
    if ok:
        await redis.expire(f"filedl:{sig}", ttl)
    return bool(ok)
