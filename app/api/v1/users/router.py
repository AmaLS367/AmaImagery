from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.v1.auth.deps import current_user
from app.core.logging import lg
from app.domain.generation_lifecycle import build_generation_public_payload, isoformat_or_none
from app.domain.models import User, UserSettings
from app.files.artifacts import get_artifact_service
from app.infra.uow import get_uow

router = APIRouter()


class SettingsOut(BaseModel):
    data: dict[str, Any]


class SettingsIn(BaseModel):
    data: dict[str, Any]


@router.get("/me/settings", response_model=SettingsOut)
async def get_settings(user: User = Depends(current_user)) -> SettingsOut:
    uow = get_uow()
    async with uow:
        us = await uow.users.get_settings(user.id)
    lg("app").bind(scope="users", action="get_settings").info("users.settings.get")
    return SettingsOut(data=(us.data if us else {}))


@router.patch("/me/settings", response_model=SettingsOut)
async def patch_settings(payload: SettingsIn, user: User = Depends(current_user)) -> SettingsOut:
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
    task_id: str
    status: str
    provider_name: str | None = None
    provider_job_id: str | None = None
    provider_state: dict[str, Any] | None = None
    image_path: str
    image_filename: str | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None
    prompt: dict[str, Any]
    params: dict[str, Any]
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
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
) -> GenList:
    uow = get_uow()
    async with uow:
        total = await uow.generations.count_by_user(user.id)
        rows = await uow.generations.list_by_user(user.id, limit=limit, offset=offset)
    artifacts = get_artifact_service()

    items = []
    for r in rows:
        payload = build_generation_public_payload(r, artifacts=artifacts)
        items.append(
            GenItem(
                id=str(r.id),
                task_id=payload.task_id,
                status=payload.status,
                provider_name=payload.provider_name,
                provider_job_id=payload.provider_job_id,
                provider_state=payload.provider_state,
                image_path=payload.image_path or "",
                image_filename=payload.image_filename,
                metadata=payload.metadata,
                error=payload.error,
                prompt=r.prompt or {},
                params=r.params or {},
                created_at=isoformat_or_none(r.created_at) or "",
                started_at=isoformat_or_none(r.started_at),
                completed_at=isoformat_or_none(r.completed_at),
                exp=payload.exp,
                sig=payload.sig,
                image_url=payload.image_url,
            )
        )
    lg("app").bind(scope="users", action="list_generations").info("users.generations.list")
    return GenList(total=total, items=items)
