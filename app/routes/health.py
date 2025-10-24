from fastapi import APIRouter, Response

router = APIRouter(tags=["health❤️‍🩹"])

@router.options("/health")
async def health_options():
    return Response(status_code=200)

@router.get("/health")
async def health_check():
    return {"ok": True, "status": "healthy"}

@router.get("/healthz")
async def healthz():
    return {"ok": True, "status": "ready"}
