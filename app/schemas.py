from pydantic import BaseModel, Field
from app.config import settings
from typing import List, Tuple, Optional

class GenReq(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)
    negative_prompt: str | None = None
    steps: int = Field(default=4, ge=1, le=settings.max_steps)
    seed: int | None = None
    width: int = Field(default=settings.max_size, ge=256, le=settings.max_size)
    height: int = Field(default=settings.max_size, ge=256, le=settings.max_size)
    guidance_scale: float = Field(6.5, ge=0.0, le=15.0)
    ref_image_b64: Optional[str] = None         #
    ip_scale: float = Field(0.6, ge=0.0, le=1.5)

class GenResp(BaseModel):
    ok: bool
    path: str
    prompt_hash: str
    corrections: List[Tuple[str, str]] = []  # [(исходное, замена)]
