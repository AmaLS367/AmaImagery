from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.auth.deps import optional_user
from app.core.logging import lg
from app.config import settings
from app.domain.schemas import GenReq, GenResp
from app.services.upscale_service import UpscaleService

router = APIRouter()

