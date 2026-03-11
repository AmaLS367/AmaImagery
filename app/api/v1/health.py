from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.config import settings
from app.domain.providers import get_provider_boot_snapshot, get_provider_registry

router = APIRouter()


@router.options("/health")
async def health_options() -> Response:
    return Response(status_code=200)


@router.get("/health")
async def health_check(request: Request) -> dict:
    providers = get_provider_boot_snapshot().as_dict()
    infra = getattr(request.app.state, "infrastructure_status", {})
    return {
        "ok": True,
        "status": "alive",
        "providers": providers,
        "infrastructure": infra,
    }


@router.get("/healthz", response_model=None)
async def healthz(request: Request) -> dict[str, Any] | JSONResponse:
    registry = get_provider_registry()
    readiness = await registry.readiness_snapshot()
    infra = getattr(request.app.state, "infrastructure_status", {})
    queue_info = infra.get("task_queue", {}) if isinstance(infra, dict) else {}
    queue_backend = queue_info.get("backend")
    queue_ready = bool(queue_info.get("ready", False)) and (queue_backend == "redis" or settings.no_redis)
    generation_ready = bool(readiness["default_provider_usable"]) and queue_ready
    payload = {
        "ok": generation_ready,
        "status": "ready" if generation_ready else "not_ready",
        "providers": readiness,
        "infrastructure": infra,
        "generation_ready": generation_ready,
        "default_provider_usable": readiness["default_provider_usable"],
        "task_queue_ready": queue_ready,
    }
    if generation_ready:
        return payload
    return JSONResponse(status_code=503, content=payload)
