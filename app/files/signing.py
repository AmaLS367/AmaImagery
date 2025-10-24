import hmac, time
from hashlib import sha256
from app.config import settings
from app.infra.redis import get_redis

def _payload(name: str, exp: int) -> bytes:
    return f"{name}.{exp}".encode("utf-8")

def make_signature(name: str, exp: int) -> str:
    key = settings.secret_key.encode("utf-8")
    return hmac.new(key, _payload(name, exp), sha256).hexdigest()

def verify_signature(name: str, exp: int, sig: str) -> bool:
    expected = make_signature(name, exp)
    try:
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False

async def consume_once(sig: str, exp: int, skew: int = 0) -> bool:
    """
    True → можно отдать файл и пометили токен как использованный.
    False → ссылка уже была использована.
    При отсутствии Redis или ошибках → возвращаем True, чтобы не ломать выдачу.
    TTL рассчитывается по exp.
    """
    if not getattr(settings, "file_single_use", False):
        return True

    redis = get_redis()
    if redis is None:
        return True

    now = int(time.time())
    ttl = max(1, min(max(0, exp - now), 3600))
    key = f"filedl:{sig}"
    try:
        ok = await redis.setnx(key, "1")
        if not ok:
            return False
        await redis.expire(key, ttl)
        return True
    except Exception:
        return True
