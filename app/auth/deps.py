from __future__ import annotations
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)

def current_user(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    token: Optional[str] = None

    # 1) Bearer
    if cred and cred.scheme.lower() == "bearer" and cred.credentials:
        token = cred.credentials

    # 2) Cookie
    if not token:
        token = (
            request.cookies.get("access_token")
            or request.cookies.get("Authorization")
            or request.cookies.get("token")
        )

    # 3) Query
    if not token:
        token = (
            request.query_params.get("access_token")
            or request.query_params.get("token")
        )

    # 4) Заголовки-валидайты без схемы
    if not token:
        raw = request.headers.get("authorization", "").strip()
        if raw and " " not in raw:
            token = raw
    if not token:
        token = request.headers.get("x-access-token") or request.headers.get("x-token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload["sub"]))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

# Функция, чтобы в /generate можно было сохранить user_id, но не требовать токен.
def optional_user(
  cred: HTTPAuthorizationCredentials | None = Depends(bearer),
  db: Session = Depends(get_db),
) -> User | None:
  if not cred or cred.scheme.lower() != "bearer":
    return None
  try:
    payload = decode_access_token(cred.credentials)
    user_id = UUID(str(payload["sub"]))
  except Exception:
    return None
  return db.get(User, user_id)


async def get_user_or_ip_identifier(request: Request) -> str:
    """
    Get user ID or IP address for rate limiting.
    
    Args:
        request: FastAPI request object
        
    Returns:
        String identifier for rate limiting
    """
    # Try to get user from authorization header
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    
    # Fallback to IP address
    host = getattr(request.client, "host", "unknown")
    return f"ip:{host}"

