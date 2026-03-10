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


def _extract_access_token(
    request: Request,
    cred: HTTPAuthorizationCredentials | None,
) -> str | None:
    if cred and cred.scheme.lower() == "bearer" and cred.credentials:
        return cred.credentials

    return (
        request.cookies.get("access_token")
        or request.cookies.get("Authorization")
        or request.cookies.get("token")
    )

async def current_user(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = _extract_access_token(request, cred)

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
  request: Request,
  cred: HTTPAuthorizationCredentials | None = Depends(bearer),
  db: AsyncSession = Depends(get_db),
) -> User | None:
  token = _extract_access_token(request, cred)
  if not token:
    return None
  try:
    payload = decode_access_token(token)
    user_id = UUID(str(payload["sub"]))
  except Exception:
    return None
  repo = SqlAlchemyUserRepository(db)
  return await repo.get(user_id)


async def current_superuser(user: User = Depends(current_user)) -> User:
    if not getattr(user, "is_superuser", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")
    return user


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

