from __future__ import annotations
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from app.prompt_hygiene.contracts import Mode
from app.prompt_hygiene.settings import get_mode, set_mode

router = APIRouter()

class HygieneModeIn(BaseModel):
    mode: Mode

class HygieneModeOut(BaseModel):
    user_id: str
    mode: Mode

@router.get("/{user_id}/hygiene-mode", response_model=HygieneModeOut)
async def get_hygiene_mode(user_id: str = Path(..., min_length=1, max_length=128)) -> HygieneModeOut:
    return HygieneModeOut(user_id=user_id, mode=get_mode(user_id))

@router.patch("/{user_id}/hygiene-mode", response_model=HygieneModeOut)
async def patch_hygiene_mode(payload: HygieneModeIn, user_id: str = Path(..., min_length=1, max_length=128)) -> HygieneModeOut:
    try:
        set_mode(user_id, payload.mode)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="failed_to_set_mode") from exc
    return HygieneModeOut(user_id=user_id, mode=payload.mode)
