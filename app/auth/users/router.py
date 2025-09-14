from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth.deps import current_user
from app.models import User, UserSettings, Generation
from app.logging_setup import lg

router = APIRouter(prefix="/users", tags=["users🤵"])

class SettingsOut(BaseModel):
    data: dict[str, Any]

class SettingsIn(BaseModel):
    data: dict[str, Any]

@router.get("/me/settings", response_model=SettingsOut)
def get_settings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    us = db.get(UserSettings, user.id)
    lg("app").bind(scope="users", action="get_settings").info("users.settings.get")
    return SettingsOut(data=(us.data if us else {}))

@router.patch("/me/settings", response_model=SettingsOut)
def patch_settings(payload: SettingsIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    us = db.get(UserSettings, user.id) or UserSettings(user_id=user.id, data={})
    if us.user_id is None:  # только если создаём
        db.add(us)
    new_data = dict(us.data or {})
    new_data.update(payload.data or {})
    us.data = new_data
    db.commit()
    lg("app").bind(scope="users", action="patch_settings").info("users.settings.patch")
    return SettingsOut(data=us.data)

class GenItem(BaseModel):
    id: str
    image_path: str
    prompt: dict
    params: dict
    created_at: str

class GenList(BaseModel):
    total: int
    items: list[GenItem]

@router.get("/me/generations", response_model=GenList)
def my_generations(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Generation).filter(Generation.user_id == user.id).order_by(Generation.created_at.desc())
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    items = [GenItem(
        id=str(r.id),
        image_path=r.image_path,
        prompt=r.prompt or {},
        params=r.params or {},
        created_at=r.created_at.isoformat(),
    ) for r in rows]
    lg("app").bind(scope="users", action="list_generations").info("users.generations.list")
    return GenList(total=total, items=items)
