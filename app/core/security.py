from __future__ import annotations
from datetime import datetime, timedelta, timezone
from jwt import InvalidTokenError, ExpiredSignatureError
from app.config import settings
from uuid import UUID
from app.infra.redis import get_redis

import re, jwt, uuid, time, secrets

import bcrypt
_EMAIL_RX = re.compile(r"\s+")
RESET_TYP = "pwd_reset"

def normalize_email(s: str) -> str:
    return _EMAIL_RX.sub("", s).strip().lower()

def hash_password(raw: str) -> str:
    hashed = bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds))
    return hashed.decode("utf-8")

def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False

def create_access_token(sub: str | int | UUID, extra: dict | None = None, expires_minutes: int | None = None) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    exp_minutes = expires_minutes or settings.access_ttl_min
    exp = now + timedelta(minutes=exp_minutes)
    payload = {
        "sub": str(sub),
        "typ": "access",
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_alg)
    return token, exp_minutes * 60

def decode_access_token(token: str) -> dict:
  try:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_alg], options={"verify_aud": False})
    if "sub" not in payload or "exp" not in payload:
      raise InvalidTokenError("malformed")

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if int(payload["exp"]) <= now_ts:
        raise ExpiredSignatureError()
    return payload

  except ExpiredSignatureError as e:
    raise e
  except Exception as e:
    raise InvalidTokenError(str(e))

def create_reset_token(*, sub: str, ttl_min: int | None = None) -> tuple[str, int]:
    ttl = int(ttl_min or settings.reset_token_ttl_min)
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ttl)
    payload = {
        "sub": str(sub),
        "typ": RESET_TYP,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_alg)
    return token, ttl

def decode_reset_token(token: str) -> dict:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_alg])
    if payload.get("typ") != RESET_TYP:
        raise jwt.InvalidTokenError("invalid reset token type")
    return payload


# ==================== Extended Security Functions ====================
def _now_ts() -> int:
    return int(time.time())


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


# Constants for token management
ACCESS_TTL_MIN = settings.access_ttl_min
FAMILY_PREFIX = "rtfam:"
REVOKE_PREFIX = settings.revoke_prefix
LOGOUT_PREFIX = "logout:"
REFRESH_TTL_SEC = settings.refresh_ttl_days * 86400

_in_memory_families: dict[str, dict[str, int | str]] = {}
_in_memory_revoked: dict[str, int] = {}
_in_memory_logged_out: dict[str, int] = {}

def _family_record(new_jti: str, exp_ts: int) -> dict[str, int | str]:
    """Build family record for Redis with unified structure."""
    return {
        "current_jti": new_jti,
        "exp": exp_ts,
        "created": _now_ts(),
    }

def _family_key(user_id: str, session_id: str) -> str:
    """Generate family key for token management."""
    return f"{FAMILY_PREFIX}{user_id}:{session_id}"


def new_session_id() -> str:
    """Generate a new session ID."""
    return secrets.token_urlsafe(16)


def _issue_access_token(user_id: str) -> str:
    """Issue a new access token."""
    iat = _now_dt()
    exp = iat + timedelta(minutes=ACCESS_TTL_MIN)
    payload = {
        "sub": user_id,
        "typ": "access",
        "iat": int(iat.timestamp()),
        "nbf": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": uuid.uuid4().hex,
        "iss": "amaimagery-api",
        "aud": "amaimagery-client",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_alg)


def _issue_refresh_token(user_id: str, session_id: str) -> tuple[str, str, int]:
    """Issue a new refresh token."""
    iat = _now_dt()
    exp = iat + timedelta(days=settings.refresh_ttl_days)
    rjti = uuid.uuid4().hex
    payload = {
        "sub": user_id,
        "typ": "refresh",
        "iat": int(iat.timestamp()),
        "nbf": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": rjti,
        "session_id": session_id,
        "iss": "amaimagery-api",
        "aud": "amaimagery-client",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_alg)
    return token, rjti, int(exp.timestamp())


async def issue_tokens_rotating(user_id: str, session_id: str) -> dict[str, str]:
    """Issue rotating tokens for a user session."""
    r = get_redis()

    await revoke_family_all(user_id)

    access = _issue_access_token(user_id)
    refresh, rjti, exp_ts = _issue_refresh_token(user_id, session_id)

    family_key = _family_key(user_id, session_id)
    if r is None:
        _in_memory_families[family_key] = _family_record(rjti, exp_ts)
    else:
        await r.hset(family_key, mapping=_family_record(rjti, exp_ts))
        await r.expire(family_key, REFRESH_TTL_SEC)
    
    return {"access": access, "refresh": refresh}


async def check_family_current(user_id: str, session_id: str, jti: str) -> bool:
    """Check if the JTI is current for the family."""
    r = get_redis()
    family_key = _family_key(user_id, session_id)
    if r is None:
        _cleanup_in_memory_security_state()
        current_jti = (_in_memory_families.get(family_key) or {}).get("current_jti")
        return current_jti == jti
    current_jti = await r.hget(family_key, "current_jti")
    return current_jti == jti


async def rotate_refresh(user_id: str, session_id: str, old_jti: str) -> dict[str, str]:
    """Rotate refresh token for a session."""
    r = get_redis()
    family_key = _family_key(user_id, session_id)

    if r is None:
        _cleanup_in_memory_security_state()
        current_jti = (_in_memory_families.get(family_key) or {}).get("current_jti")
        if current_jti != old_jti:
            raise ValueError("Invalid old JTI")
        _in_memory_revoked[old_jti] = _now_ts() + 86400
    else:
        current_jti = await r.hget(family_key, "current_jti")
        if current_jti != old_jti:
            raise ValueError("Invalid old JTI")
        await r.setex(f"{REVOKE_PREFIX}{old_jti}", 86400, "1")

    access = _issue_access_token(user_id)
    refresh, new_jti, exp_ts = _issue_refresh_token(user_id, session_id)
    if r is None:
        _in_memory_families[family_key] = _family_record(new_jti, exp_ts)
    else:
        await r.hset(family_key, mapping=_family_record(new_jti, exp_ts))
        await r.expire(family_key, REFRESH_TTL_SEC)
    
    return {"access": access, "refresh": refresh}


async def revoke_family(user_id: str, session_id: str) -> None:
    """Revoke a specific family of tokens."""
    r = get_redis()
    family_key = _family_key(user_id, session_id)
    if r is None:
        _in_memory_families.pop(family_key, None)
        return
    await r.delete(family_key)


async def revoke_family_all(user_id: str) -> None:
    """Revoke all families for a user."""
    r = get_redis()
    pattern = f"{FAMILY_PREFIX}{user_id}:*"
    if r is None:
        _cleanup_in_memory_security_state()
        keys = [key for key in _in_memory_families.keys() if key.startswith(pattern.rstrip("*"))]
        for key in keys:
            _in_memory_families.pop(key, None)
        return
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)


async def revoke_jti(jti: str, exp_ts: int) -> None:
    """Revoke a specific JTI."""
    r = get_redis()
    ttl = max(0, exp_ts - _now_ts())
    if ttl > 0:
       if r is None:
           _in_memory_revoked[jti] = exp_ts
           return
       await r.setex(f"{REVOKE_PREFIX}{jti}", ttl, "1")


async def is_revoked(jti: str) -> bool:
    r = get_redis()
    if r is None:
        _cleanup_in_memory_security_state()
        exp_ts = _in_memory_revoked.get(jti)
        return bool(exp_ts and exp_ts > _now_ts())
    return bool(await r.exists(f"{REVOKE_PREFIX}{jti}"))


async def mark_user_logged_out(user_id: str) -> None:
    """Mark user as logged out."""
    r = get_redis()
    if r is None:
        _in_memory_logged_out[user_id] = _now_ts() + 86400
        return
    await r.setex(f"{LOGOUT_PREFIX}{user_id}", 86400, "1")


async def is_user_logged_out(user_id: str) -> bool:
    r = get_redis()
    if r is None:
        _cleanup_in_memory_security_state()
        exp_ts = _in_memory_logged_out.get(user_id)
        return bool(exp_ts and exp_ts > _now_ts())
    return bool(await r.exists(f"{LOGOUT_PREFIX}{user_id}"))

async def clear_user_logged_out(user_id: str) -> None:
    """Clear user logged out status."""
    r = get_redis()
    if r is None:
        _in_memory_logged_out.pop(user_id, None)
        return
    await r.delete(f"{LOGOUT_PREFIX}{user_id}")


def _cleanup_in_memory_security_state() -> None:
    now_ts = _now_ts()
    for store in (_in_memory_revoked, _in_memory_logged_out):
        expired = [key for key, exp_ts in store.items() if exp_ts <= now_ts]
        for key in expired:
            store.pop(key, None)

    expired_families = [
        key
        for key, record in _in_memory_families.items()
        if int(record.get("exp", 0)) <= now_ts
    ]
    for key in expired_families:
        _in_memory_families.pop(key, None)
