from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.infra.uow import get_uow
from app.api.v1.auth.deps import current_user
from app.core.safety import (
    is_blocked,
    is_blocked_forced,
    get_rules,
    reload_rules,
)

router = APIRouter()

class NSFWToggle(BaseModel):
    allow: bool

class NSFWCheckRequest(BaseModel):
    text: Optional[str] = None
    forced: bool = False

class NSFWCheckResponse(BaseModel):
    blocked: bool
    forced: bool

@router.patch("/users/me/nsfw")
async def set_nsfw(toggle: NSFWToggle, user=Depends(current_user)):
    uow = get_uow()
    async with uow:
        settings_row = await uow.users.get_settings(user.id) or UserSettings(user_id=user.id, data={})
        payload = dict(settings_row.data or {})
        payload["nsfw_allow"] = bool(toggle.allow)
        settings_row.data = payload
        await uow.users.save_settings(settings_row)
    return {"ok": True, "nsfw_allow": bool(toggle.allow)}

@router.post("/check", response_model=NSFWCheckResponse)
def check_text(req: NSFWCheckRequest):
    if req.forced:
        return NSFWCheckResponse(blocked=is_blocked_forced(req.text), forced=True)
    return NSFWCheckResponse(blocked=is_blocked(req.text), forced=False)

@router.get("/rules")
def list_rules():
    path = str(getattr(settings, "nsfw_blocklist_path", ""))
    return {"path": path, "rules": get_rules(), "count": len(get_rules())}

@router.post("/reload")
def reload_rules_cache():
    reload_rules()
    return {"ok": True}
