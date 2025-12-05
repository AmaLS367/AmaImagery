from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
import time

from app.infra.db import get_db
from app.api.v1.auth.deps import current_user
from app.domain.models import User, UserSettings
from app.infra.repositories import SqlAlchemyGenerationRepository
from app.core.logging import lg
from app.config import settings
from app.files.signing import make_signature

router = APIRouter()

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
    if us.user_id is None:
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
    exp: int | None = None
    sig: str | None = None
    image_url: str | None = None

class GenList(BaseModel):
    total: int
    items: list[GenItem]

@router.get("/me/generations", response_model=GenList)
async def my_generations(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    repo = SqlAlchemyGenerationRepository(db)
    total = await repo.count_by_user(user.id)
    rows = await repo.list_by_user(user.id, limit=limit, offset=offset)
    now = int(time.time())
    ttl = int(settings.file_download_ttl_sec)

    items = []
    for r in rows:
        name = Path(r.image_path).name 
        exp = now + ttl
        sig = make_signature(name, exp)
        image_url = f"/file?path={name}&exp={exp}&sig={sig}"
        items.append(GenItem(
            id=str(r.id),
            image_path=r.image_path,
            prompt=r.prompt or {},
            params=r.params or {},
            created_at=r.created_at.isoformat(),
            exp=exp,
            sig=sig,
            image_url=image_url,
        ))
    lg("app").bind(scope="users", action="list_generations").info("users.generations.list")
    return GenList(total=total, items=items)
