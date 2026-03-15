from typing import Any, Literal

from pydantic import BaseModel, Field

Style = Literal["realistic", "anime"]


class GenReq(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000, description="Main generation prompt")
    negative_prompt: str | None = Field(None, max_length=1000, description="Negative prompt")

    steps: int = Field(default=28, ge=1, le=200, description="Number of inference steps")
    seed: int | None = Field(None, description="Random seed for reproducible generation")
    width: int = Field(default=768, ge=256, le=4096, description="Image width")
    height: int = Field(default=1152, ge=256, le=4096, description="Image height")
    guidance_scale: float = Field(7.5, ge=0.0, le=50.0, description="Guidance scale for generation")

    ref_image_b64: str | None = Field(None, description="Base64 encoded reference image for IP-Adapter")
    ip_scale: float = Field(0.6, ge=0.0, le=2.0, description="IP-Adapter scale")
    style: Style = Field(default="realistic", description="Visual style for generation")


class GenResp(BaseModel):
    ok: bool = Field(description="Whether generation was successful")
    path: str = Field(description="Path to generated image")
    prompt_hash: str = Field(description="Hash of the prompt for identification")
    corrections: list[tuple[str, str]] = Field(default_factory=list, description="List of prompt corrections made")
    exp: int | None = Field(None, description="Expiration timestamp for signed URL")
    sig: str | None = Field(None, description="Signature for file download")


class TaskResp(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Task status (queued, running, completed, failed, canceled)")


class TaskStatusResp(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Task status (queued, running, completed, failed, canceled)")
    provider_name: str | None = Field(None, description="Selected provider name")
    provider_state: dict[str, Any] | None = Field(None, description="Provider-specific execution state")
    image_path: str | None = Field(None, description="Path to generated image (completed only)")
    image_filename: str | None = Field(None, description="Filename of generated image (completed only)")
    image_url: str | None = Field(None, description="Signed URL for image download (completed only)")
    exp: int | None = Field(None, description="Expiration timestamp for signed URL (completed only)")
    sig: str | None = Field(None, description="Signature for file download (completed only)")
    metadata: dict[str, Any] | None = Field(None, description="Generation metadata (completed only)")
    error: str | None = Field(None, description="Error message (failed only)")
    created_at: int | None = Field(None, description="Task creation timestamp")
    started_at: int | None = Field(None, description="Task start timestamp")
    completed_at: int | None = Field(None, description="Task completion timestamp")


class HealthResponse(BaseModel):
    ok: bool = Field(description="Service health status")
    status: str = Field(description="Detailed status message")


class ErrorResponse(BaseModel):
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
