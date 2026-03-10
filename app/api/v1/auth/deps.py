from __future__ import annotations
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_db
from app.domain.models import User
from app.core.security import decode_access_token
from app.infra.repositories import SqlAlchemyUserRepository

bearer = HTTPBearer(auto_error=False)

async def current_user(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token: Optional[str] = None

    # Bearer
    if cred and cred.scheme.lower() == "bearer" and cred.credentials:
        token = cred.credentials

    # Cookie
    if not token:
        token = (
            request.cookies.get("access_token")
            or request.cookies.get("Authorization")
            or request.cookies.get("token")
        )

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload["sub"]))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = SqlAlchemyUserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

async def optional_user(
  cred: HTTPAuthorizationCredentials | None = Depends(bearer),
  db: AsyncSession = Depends(get_db),
) -> User | None:
  if not cred or cred.scheme.lower() != "bearer":
    return None
  try:
    payload = decode_access_token(cred.credentials)
    user_id = UUID(str(payload["sub"]))
  except Exception:
    return None
  repo = SqlAlchemyUserRepository(db)
  return await repo.get(user_id)


async def get_user_or_ip_identifier(request: Request) -> str:
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

