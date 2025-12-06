from __future__ import annotations
from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.users.router import router as auth_users_router
from app.api.v1.files.router import router as files_router
from app.api.v1.images.generate import router as generate_router
from app.api.v1.images.status import router as status_router
from app.api.v1.moderation.nsfw import router as nsfw_router
from app.api.v1.users.hygiene_mode import router as hygiene_mode_router
from app.api.v1.health import router as health_router

api_v1 = APIRouter()

api_v1.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1.include_router(auth_users_router, prefix="/auth/users", tags=["auth"])
api_v1.include_router(files_router, tags=["files"])
api_v1.include_router(generate_router, tags=["images"])
api_v1.include_router(status_router, tags=["images"])
api_v1.include_router(nsfw_router, prefix="/nsfw", tags=["moderation"])
api_v1.include_router(hygiene_mode_router, prefix="/users", tags=["users"])
api_v1.include_router(health_router, tags=["health"])
