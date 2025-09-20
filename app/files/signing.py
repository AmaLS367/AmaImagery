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

async def consume_once(redis: Optional["redis.asyncio.Redis"], sig: str, ttl: int) -> bool:
    """
    True → можно отдать файл и пометили токен как использованный.
    False → ссылка уже была использована.
    В dev (redis=None) или при сбоях Redis → не валим ручку, возвращаем True.
    """
    # одноразовость выключена настройкой → всегда разрешаем
    if not getattr(settings, "file_single_use", False):
        return True

    # Redis отсутствует (dev) → пропускаем одноразовость
    if redis is None:
        return True

    key = f"filedl:{sig}"
    try:
        # setnx: первый доступ → True, повтор → False
        ok = await redis.setnx(key, "1")
        if not ok:
            return False
        # ограничим TTL адекватным диапазоном
        await redis.expire(key, max(1, min(ttl, 3600)))
        return True
    except Exception:
        # при любой ошибке Redis не роняем выдачу файла в dev
        return True
