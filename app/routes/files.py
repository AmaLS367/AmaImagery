"""
File serving endpoints.

Handles secure file downloads with signature verification.
"""

import time
from pathlib import Path

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import settings
from app.files.signing import consume_once, verify_signature
from app.files.validators import check_ext, check_mime, safe_join
from app.services.rate_limiting import create_file_rate_limiter

router = APIRouter(tags=["files"])


@router.get("/file")
async def download_file(
    path: str = Query(..., min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$"),
    exp: int = Query(..., ge=0),
    sig: str = Query(..., min_length=64, max_length=64),
    rate_limiter=Depends(create_file_rate_limiter()),
) -> FileResponse:
    """
    Download a file with signature verification.
    
    Args:
        path: File path/name
        exp: Expiration timestamp
        sig: Signature for verification
        rate_limiter: Rate limiter dependency
        
    Returns:
        FileResponse with the requested file
        
    Raises:
        HTTPException: For invalid signatures, expired links, or file not found
    """
    # Validate signature
    if not verify_signature(path, exp, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Check expiration
    ttl_left = max(0, exp - int(time.time()))
    if ttl_left == 0:
        raise HTTPException(status_code=403, detail="Link expired")
    
    # Check if link has been used
    redis_client = redis.from_url(
        settings.redis_url, 
        encoding="utf-8", 
        decode_responses=True
    )
    
    try:
        if not await consume_once(redis_client, sig, ttl_left):
            raise HTTPException(status_code=403, detail="Link already used")
    finally:
        await redis_client.aclose()
    
    # Validate file path and extension
    file_path = safe_join(path)
    check_ext(file_path)
    
    # Check MIME type
    ext = file_path.suffix.lstrip(".").lower()
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg", 
        "jpeg": "image/jpeg",
        "webp": "image/webp"
    }
    mime_type = mime_map.get(ext)
    check_mime(mime_type)
    
    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Prepare response headers
    headers = {
        "Content-Disposition": f'attachment; filename="{file_path.name}"',
        "X-Content-Type-Options": "nosniff",
    }
    
    # Log file download
    from app.logging_setup import sec
    sec("file_download", name=file_path.name)
    
    return FileResponse(
        str(file_path),
        media_type=mime_type,
        filename=file_path.name,
        headers=headers
    )
