from fastapi import APIRouter, Response, HTTPException
from app.config import settings 

router = APIRouter(tags=["health❤️‍🩹"])

@router.options("/health")
async def health_options():
    return Response(status_code=200)

@router.get("/health")
async def health_check():
    return {"ok": True, "status": "healthy"}

@router.get("/healthz")
async def healthz():
    if getattr(settings, "limits_enabled", None) is None:
        raise HTTPException(status_code=503, detail="Misconfigured")
    return {"ok": True, "status": "ready"}
