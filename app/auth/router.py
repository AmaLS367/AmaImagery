from __future__ import annotations
from typing import Literal, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.infra.db import get_db
from app.domain.models import User, UserSettings
from app.core.logging import lg, sec
from app.auth.deps import current_user
from app.services.rate_limiting import create_rate_limiter

from app.core.security import (
    normalize_email, hash_password, verify_password,
    create_reset_token, decode_reset_token, create_access_token
)
from app.core.security import (
    new_session_id, issue_tokens_rotating, check_family_current,
    rotate_refresh, revoke_family, revoke_family_all, revoke_jti, is_revoked,
    mark_user_logged_out, is_user_logged_out, clear_user_logged_out,
)

from app.infra.mailer import send_mail
from app.config import settings

import jwt

router = APIRouter(prefix="/auth", tags=["auth🥷"])

# ========= Registration =========

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    username: str = Field(min_length=2, max_length=32)

class RegisterOut(BaseModel):
    id: str
    email: EmailStr
    username: str
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  

class MeOut(BaseModel):
  id: str
  email: str
  username: str
  settings: dict[str, Any] = {}

# ======== Helper ========
def _set_refresh_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.refresh_cookie_secure,   # в проде True
        samesite="lax",
        max_age=settings.refresh_ttl_days * 86400,
        path="/auth",
    )
# ========================

@router.post(
    "/register",
    response_model=RegisterOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(create_rate_limiter(limit=3, window_sec=3600))]
)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    username = payload.username.strip()

    exists = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if exists:
        raise HTTPException(status_code=409, detail="User with this email or username already exists")

    user = User(email=email, username=username, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()  # получаем user.id
    db.add(UserSettings(user_id=user.id, data={}))
    db.commit()

    # минимальный лог без PII
    lg("app").bind(scope="auth", action="register").info("auth.registered")

    token, ttl = create_access_token(sub=user.id, extra={"username": username})
    return RegisterOut(
        id=str(user.id),
        email=email,
        username=username,
        access_token=token,
        expires_in=ttl,
    )

@router.get("/me", response_model=MeOut)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    lg("app").bind(scope="auth", action="me").info("auth.me")
    us = db.get(UserSettings, user.id)  # PK = user_id
    return MeOut(
        id=str(user.id),
        email=user.email,
        username=user.username,
        settings=(us.data if us else {}),
    )

# ========= Логин =========

class LoginIn(BaseModel):
    identifier: str = Field(min_length=2)  # email или username
    password: str = Field(min_length=8, max_length=256)

class LoginOut(BaseModel):
    id: str
    email: EmailStr
    username: str
    settings: dict[str, Any] = {}
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # seconds

@router.post("/me", response_model=LoginOut, dependencies=[Depends(create_rate_limiter(limit=5, window_sec=60))])
async def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    ident = payload.identifier.strip()
    email_norm = normalize_email(ident)
    user = (
        db.query(User)
        .filter((User.email == email_norm) | (User.username == ident))
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        sec("login_failure")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    us = db.get(UserSettings, user.id)
    
    sid = new_session_id()
    pair = await issue_tokens_rotating(str(user.id), sid)
    await clear_user_logged_out(str(user.id))

    body = LoginOut(
        id=str(user.id),
        email=user.email,
        username=user.username,
        settings=(us.data if us else {}),
        access_token=pair["access"],
        expires_in=settings.access_ttl_min * 60,
    ).model_dump()

    resp = JSONResponse(content=body)
    
    # Clear old refresh cookie first - use same path as setting
    resp.set_cookie(
        settings.refresh_cookie_name,
        "",
        expires=0,
        path="/auth",
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax"
    )
    
    # Set new refresh cookie
    _set_refresh_cookie(resp, pair["refresh"])
    lg("app").bind(scope="auth", action="login").info("auth.login")
    sec("login_success", user_id=str(user.id))
    return resp

# ========= Logout =========
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request) -> Response:
    rt = request.cookies.get(settings.refresh_cookie_name)
    if rt:
        try:
            payload = jwt.decode(rt, settings.secret_key, algorithms=[settings.jwt_alg], options={"verify_aud": False})
            uid = str(payload.get("sub") or "")
            jti = str(payload.get("jti") or "")
            exp = int(payload.get("exp") or 0)
            if jti and exp:
                await revoke_jti(jti, exp_ts=exp)
            if uid:
                await revoke_family_all(uid)
                await mark_user_logged_out(uid)
        except jwt.PyJWTError:
            pass

    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie(settings.refresh_cookie_name, path="/auth")
    return resp
                  

# ========= Forgot password =========
class ForgotIn(BaseModel):
    identifier: str = Field(min_length=2)  # email или username

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    dependencies=[Depends(create_rate_limiter(limit=3, window_sec=3600))]
)
def forgot_password(payload: ForgotIn, db: Session = Depends(get_db)) -> None:
    ident = payload.identifier.strip()
    user = db.query(User).filter(
        (User.email == normalize_email(ident)) | (User.username == ident)
    ).first()

    # одинаковый ответ в любом случае (без утечки существования)
    if not user:
        lg("app").bind(scope="auth", action="forgot").info("auth.forgot.unknown")
        return

    token, ttl = create_reset_token(sub=str(user.id))
    link = f"{settings.frontend_origin.rstrip('/')}/reset?token={token}"

    subject = "Reset your password"
    text = f"Use this link to reset your password (valid {ttl} min): {link}"
    html = f"""<p>Use this link to reset your password (valid {ttl} min):</p>
               <p><a href="{link}" target="_blank" rel="noopener">{link}</a></p>"""

    send_mail(subject, user.email, text, html)
    lg("app").bind(scope="auth", action="forgot", user=str(user.id)).info("auth.forgot.sent")

# ========= Reset password by token =========
class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=256)

@router.post("/reset-password", status_code=status.HTTP_200_OK, response_class=Response)
def reset_password(payload: ResetIn, db: Session = Depends(get_db)) -> None:
    try:
        data = decode_reset_token(payload.token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.get(User, data.get("sub"))
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    lg("app").bind(scope="auth", action="reset", user=str(user.id)).info("auth.reset.ok")

# ========= Change password for logged-in user =========
class ChangePwdIn(BaseModel):
    old_password: str = Field(min_length=8, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)

from app.auth.deps import current_user  # импорт после определения схем

@router.post("/change-password", status_code=status.HTTP_200_OK, response_class=Response)
def change_password(payload: ChangePwdIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Wrong old password")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    lg("app").bind(scope="auth", action="change_pwd", user=str(user.id)).info("auth.change_pwd.ok")


# ========= refresh token =========
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

@router.post("/refresh", response_model=TokenOut, dependencies=[Depends(create_rate_limiter(limit=30, window_sec=60))])
async def refresh(response: Response, request: Request):
    rt = request.cookies.get(settings.refresh_cookie_name)
    if not rt:
        raise HTTPException(status_code=401, detail="no refresh")

    try:
        payload = jwt.decode(
            rt,
            settings.secret_key,
            algorithms=[settings.jwt_alg],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="bad token")

    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="bad typ")

    uid = str(payload.get("sub") or "")
    sid = str(payload.get("session_id") or "")
    jti = str(payload.get("jti") or "")
    
    if await is_user_logged_out(uid):
        await revoke_family_all(uid)
        raise HTTPException(status_code=401, detail="logged out")
    if not uid or not sid or not jti:
        raise HTTPException(status_code=401, detail="bad claims")

    if await is_revoked(jti):
        sec("refresh_reuse_detected", user_id=uid, jti=jti)
        await revoke_family(uid, sid)
        resp = JSONResponse(status_code=401, content={"detail": "reused"})
        resp.delete_cookie(settings.refresh_cookie_name, path="/auth")
        return resp


    if not await check_family_current(uid, sid, jti):
        sec("refresh_mismatch", user_id=uid, jti=jti)
        await revoke_family(uid, sid)
        resp = JSONResponse(status_code=401, content={"detail": "rotated"})
        resp.delete_cookie(settings.refresh_cookie_name, path="/auth")
        return resp


    pair = await rotate_refresh(uid, sid, old_jti=jti)

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=pair["refresh"],
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        max_age=settings.refresh_ttl_days * 86400,
        path="/auth",
    )
    return TokenOut(
        access_token=pair["access"],
        expires_in=settings.access_ttl_min * 60,
    )



