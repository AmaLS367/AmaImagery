from pydantic import BaseModel, Field
from app.config import settings
from typing import List, Tuple, Optional, Literal, Dict, Any

Style = Literal['realistic', 'anime']

class GenReq(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000, description="Main generation prompt")
    negative_prompt: Optional[str] = Field(None, max_length=1000, description="Negative prompt")
    steps: int = Field(default=28, ge=1, le=settings.max_steps, description="Number of inference steps")
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    width: int = Field(default=768, ge=256, le=settings.max_size, description="Image width")
    height: int = Field(default=1152, ge=256, le=settings.max_size, description="Image height")
    guidance_scale: float = Field(7.5, ge=0.0, le=15.0, description="Guidance scale for generation")
    ref_image_b64: Optional[str] = Field(None, description="Base64 encoded reference image for IP-Adapter")
    ip_scale: float = Field(0.6, ge=0.0, le=1.5, description="IP-Adapter scale")
    style: Style = Field(default='anime', description="Visual style for generation")

class GenResp(BaseModel):
    ok: bool = Field(description="Whether generation was successful")
    path: str = Field(description="Path to generated image")
    prompt_hash: str = Field(description="Hash of the prompt for identification")
    corrections: List[Tuple[str, str]] = Field(default=[], description="List of prompt corrections made")
    exp: Optional[int] = Field(None, description="Expiration timestamp for signed URL")
    sig: Optional[str] = Field(None, description="Signature for file download")

class TaskResp(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Task status (queued, running, completed, failed)")

class TaskStatusResp(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Task status (queued, running, completed, failed)")
    image_path: Optional[str] = Field(None, description="Path to generated image (completed only)")
    image_filename: Optional[str] = Field(None, description="Filename of generated image (completed only)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Generation metadata (completed only)")
    error: Optional[str] = Field(None, description="Error message (failed only)")
    created_at: Optional[int] = Field(None, description="Task creation timestamp")
    started_at: Optional[int] = Field(None, description="Task start timestamp")
    completed_at: Optional[int] = Field(None, description="Task completion timestamp")
    
class HealthResponse(BaseModel):
    ok: bool = Field(description="Service health status")
    status: str = Field(description="Detailed status message")

class ErrorResponse(BaseModel):
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")