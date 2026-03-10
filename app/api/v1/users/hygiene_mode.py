from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.auth.deps import current_user
from app.domain.models import User
from app.prompt_hygiene.contracts import Mode
from app.prompt_hygiene.settings import get_mode, set_mode

router = APIRouter()


class HygieneModeIn(BaseModel):
    mode: Mode


class HygieneModeOut(BaseModel):
    user_id: str
    mode: Mode


@router.get("/me/hygiene-mode", response_model=HygieneModeOut)
async def get_hygiene_mode(user: User = Depends(current_user)) -> HygieneModeOut:
    user_id = str(user.id)
    return HygieneModeOut(user_id=user_id, mode=get_mode(user_id))


@router.patch("/me/hygiene-mode", response_model=HygieneModeOut)
async def patch_hygiene_mode(payload: HygieneModeIn, user: User = Depends(current_user)) -> HygieneModeOut:
    user_id = str(user.id)
    try:
        set_mode(user_id, payload.mode)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="failed_to_set_mode") from exc
    return HygieneModeOut(user_id=user_id, mode=payload.mode)
