from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.v1.auth.deps import current_superuser
from app.domain.generation_lifecycle import (
    build_generation_public_payload,
    isoformat_or_none,
)
from app.domain.models import User
from app.files.artifacts import get_artifact_service
from app.infra.uow import get_uow

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


@router.get("/", include_in_schema=False)
async def admin_root() -> RedirectResponse:
    return RedirectResponse(url="/admin/generations", status_code=307)


@router.get("/generations", response_class=HTMLResponse, include_in_schema=False)
async def admin_generations(
    request: Request,
    admin_user: User = Depends(current_superuser),
    status: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HTMLResponse:
    filters: dict[str, Any] = {}
    if status:
        filters["status"] = status
    if provider:
        filters["provider_name"] = provider

    uow = get_uow()
    async with uow:
        total = await uow.generations.count(**filters)
        rows = await uow.generations.list(limit=limit, offset=offset, **filters)

    artifacts = get_artifact_service()
    items = []
    for row in rows:
        payload = build_generation_public_payload(row, artifacts=artifacts)
        prompt = (getattr(row, "prompt", None) or {}).get("prompt", "")
        items.append(
            {
                "task_id": payload.task_id,
                "status": payload.status,
                "provider_name": payload.provider_name,
                "provider_job_id": payload.provider_job_id,
                "provider_state": payload.provider_state,
                "image_url": payload.image_url,
                "image_filename": payload.image_filename,
                "error": payload.error,
                "created_at": isoformat_or_none(getattr(row, "created_at", None)),
                "started_at": isoformat_or_none(getattr(row, "started_at", None)),
                "completed_at": isoformat_or_none(getattr(row, "completed_at", None)),
                "prompt_preview": prompt[:140],
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/generations.html",
        context={
            "admin_user": admin_user,
            "items": items,
            "total": total,
            "status_filter": status or "",
            "provider_filter": provider or "",
            "limit": limit,
            "offset": offset,
        },
    )


@router.get("/generations/{generation_id}", response_class=HTMLResponse, include_in_schema=False)
async def admin_generation_detail(
    generation_id: str,
    request: Request,
    admin_user: User = Depends(current_superuser),
) -> HTMLResponse:
    uow = get_uow()
    async with uow:
        generation = await uow.generations.get(generation_id)
        owner = None
        if generation is not None and getattr(generation, "user_id", None):
            owner = await uow.users.get(generation.user_id)

    payload = None
    prompt_blob: dict[str, Any] = {}
    params_blob: dict[str, Any] = {}
    if generation is not None:
        payload = build_generation_public_payload(generation, artifacts=get_artifact_service())
        prompt_blob = dict(getattr(generation, "prompt", None) or {})
        params_blob = dict(getattr(generation, "params", None) or {})

    return templates.TemplateResponse(
        request=request,
        name="admin/generation_detail.html",
        context={
            "admin_user": admin_user,
            "generation": generation,
            "payload": payload,
            "owner": owner,
            "prompt_blob": prompt_blob,
            "params_blob": params_blob,
            "created_at": isoformat_or_none(getattr(generation, "created_at", None)) if generation else None,
            "started_at": isoformat_or_none(getattr(generation, "started_at", None)) if generation else None,
            "completed_at": isoformat_or_none(getattr(generation, "completed_at", None)) if generation else None,
        },
    )


@router.get("/users", response_class=HTMLResponse, include_in_schema=False)
async def admin_users(
    request: Request,
    admin_user: User = Depends(current_superuser),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HTMLResponse:
    uow = get_uow()
    async with uow:
        total = await uow.users.count()
        rows = await uow.users.list(limit=limit, offset=offset)

    items = [
        {
            "id": str(row.id),
            "email": row.email,
            "username": row.username,
            "is_superuser": bool(row.is_superuser),
            "created_at": isoformat_or_none(getattr(row, "created_at", None)),
        }
        for row in rows
    ]

    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context={
            "admin_user": admin_user,
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )
