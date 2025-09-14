"""
Image generation endpoints.

Handles AI image generation requests and responses.
"""

import asyncio
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import optional_user
from app.db import get_db
from app.limits import get_gen_semaphore
from app.config import settings
from app.schemas import GenReq, GenResp
from app.services.generation_service import GenerationService
try:
    from app.services.rate_limiting import create_rate_limiter 
    _RATE_DEP = Depends(create_rate_limiter())
except Exception:
    from fastapi import Depends as _Depends 
    async def _noop(): 
        return None
    _RATE_DEP = _Depends(_noop)

router = APIRouter(tags=["generation"])


@router.post("/generate", response_model=GenResp)
async def generate_image(
    request: GenReq,
    db: Session = Depends(get_db),
    user: Optional[Any] = Depends(optional_user),
    semaphore: asyncio.Semaphore = Depends(get_gen_semaphore),
    rate_limiter=_RATE_DEP,
) -> GenResp:
    """
    Generate an AI image based on the provided prompt.
    
    Args:
        request: Generation parameters including prompt and settings
        db: Database session for storing generation metadata
        user: Optional authenticated user
        semaphore: Rate limiting semaphore
        rate_limiter: Rate limiter dependency
        
    Returns:
        GenerationResponse with generated image details
        
    Raises:
        HTTPException: For validation errors or generation failures
    """
    generation_service = GenerationService(db)
    
    try:
        # Acquire semaphore with timeout
        gen_limit = float(settings.generation_timeout_sec)
        queue_timeout = max(20.0, min(gen_limit - 5.0, gen_limit / 2.0))

        acquired = False
        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=queue_timeout)
            acquired = True
            result = await generation_service.generate_image(request=request, user=user)
            return result
        except RuntimeError as e:
            # Нормализуем таймаут в 504
            if "timed out" in str(e).lower():
                raise HTTPException(status_code=504, detail="Generation timed out")
            raise
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=429, 
            detail="Service temporarily unavailable. Please try again later."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )
    finally:
        if acquired:
            try:
                semaphore.release()
            except Exception:
                pass
