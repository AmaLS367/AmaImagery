from __future__ import annotations

from fastapi import APIRouter, Response, HTTPException
from app.config import settings

router = APIRouter()

@router.options("/health")
async def health_options() -> Response:
    return Response(status_code=200)

@router.get("/health")
async def health_check() -> dict:
    return {"ok": True, "status": "healthy"}

@router.get("/healthz")
async def healthz() -> dict:
    limits_enabled = getattr(settings, "limits_enabled", None)
    if limits_enabled is None:
        raise HTTPException(status_code=503, detail="misconfigured")
    return {"ok": True, "status": "ready"}
