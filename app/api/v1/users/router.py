from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.v1.auth.deps import current_user
from app.domain.models import User, UserSettings
from app.infra.uow import get_uow
from app.core.logging import lg
from app.files.artifacts import get_artifact_service

router = APIRouter()

class SettingsOut(BaseModel):
    data: dict[str, Any]
class SettingsIn(BaseModel):
    data: dict[str, Any]

@router.get("/me/settings", response_model=SettingsOut)
async def get_settings(user: User = Depends(current_user)):
    uow = get_uow()
    async with uow:
        us = await uow.users.get_settings(user.id)
    lg("app").bind(scope="users", action="get_settings").info("users.settings.get")
    return SettingsOut(data=(us.data if us else {}))

@router.patch("/me/settings", response_model=SettingsOut)
async def patch_settings(payload: SettingsIn, user: User = Depends(current_user)):
    uow = get_uow()
    async with uow:
        us = await uow.users.get_settings(user.id) or UserSettings(user_id=user.id, data={})
        new_data = dict(us.data or {})
        new_data.update(payload.data or {})
        us.data = new_data
        await uow.users.save_settings(us)
    
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
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    uow = get_uow()
    async with uow:
        total = await uow.generations.count_by_user(user.id)
        rows = await uow.generations.list_by_user(user.id, limit=limit, offset=offset)
    artifacts = get_artifact_service()

    items = []
    for r in rows:
        signed = artifacts.build_signed_download(r.image_path)
        items.append(GenItem(
            id=str(r.id),
            image_path=r.image_path or "",
            prompt=r.prompt or {},
            params={
                **(r.params or {}),
                "status": r.status,
                "provider_name": r.provider_name,
                "provider_state": r.provider_state or {},
                "result": r.result or {},
                "error": r.error,
            },
            created_at=r.created_at.isoformat(),
            exp=signed["exp"],
            sig=signed["sig"],
            image_url=signed["image_url"],
        ))
    lg("app").bind(scope="users", action="list_generations").info("users.generations.list")
    return GenList(total=total, items=items)
