"""
Health check endpoints.

Provides health check and readiness endpoints for monitoring.
"""

from fastapi import APIRouter, Response

router = APIRouter(tags=["health"])


@router.options("/health")
async def health_options():
    """Handle OPTIONS request for health endpoint."""
    return Response(status_code=200)


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        dict: Status indicating service health
    """
    return {"ok": True, "status": "healthy"}


@router.get("/healthz")
async def healthz():
    """
    Kubernetes-style health check endpoint.
    
    Returns:
        dict: Status indicating service readiness
    """
    return {"ok": True, "status": "ready"}
