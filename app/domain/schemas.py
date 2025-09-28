from pydantic import BaseModel, Field
from app.config import settings
from typing import List, Tuple, Optional, Literal, Dict, Any

Style = Literal['realistic', 'anime']

class GenReq(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(min_length=3, max_length=1000, description="Main generation prompt")
    negative_prompt: Optional[str] = Field(None, max_length=1000, description="Negative prompt")
    steps: int = Field(default=4, ge=1, le=settings.max_steps, description="Number of inference steps")
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    width: int = Field(default=settings.max_size, ge=256, le=settings.max_size, description="Image width")
    height: int = Field(default=settings.max_size, ge=256, le=settings.max_size, description="Image height")
    guidance_scale: float = Field(6.5, ge=0.0, le=15.0, description="Guidance scale for generation")
    ref_image_b64: Optional[str] = Field(None, description="Base64 encoded reference image for IP-Adapter")
    ip_scale: float = Field(0.6, ge=0.0, le=1.5, description="IP-Adapter scale")
    style: Style = Field(default='anime', description="Visual style for generation")

class GenResp(BaseModel):
    """Response model for image generation."""
    ok: bool = Field(description="Whether generation was successful")
    path: str = Field(description="Path to generated image")
    prompt_hash: str = Field(description="Hash of the prompt for identification")
    corrections: List[Tuple[str, str]] = Field(default=[], description="List of prompt corrections made")
    exp: Optional[int] = Field(None, description="Expiration timestamp for signed URL")
    sig: Optional[str] = Field(None, description="Signature for file download")

class HealthResponse(BaseModel):
    """Health check response model."""
    ok: bool = Field(description="Service health status")
    status: str = Field(description="Detailed status message")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
