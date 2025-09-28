"""
Image generation endpoints.

Handles AI image generation requests and responses.
"""

import asyncio
from typing import Optional, Any
import os, traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import optional_user
from app.infra.db import get_db
from app.core.logging import lg
from app.core.limits import get_gen_semaphore
from app.config import settings
from app.domain.schemas import GenReq, GenResp
from app.services.generation_service import GenerationService
from app.services.rate_limiting import create_rate_limiter

router = APIRouter(tags=["generation"])

# Подключаем лимитер только если включён флаг
_generation_deps = [Depends(create_rate_limiter(settings.gen_per_user_per_min, 60))] if getattr(settings, "limits_enabled", False) else []

@router.post("/generate", response_model=GenResp, dependencies=_generation_deps)
async def generate_image(
    request: GenReq,
    db: Session = Depends(get_db),
    user: Optional[Any] = Depends(optional_user),
    semaphore: asyncio.Semaphore = Depends(get_gen_semaphore),
) -> GenResp:

    generation_service = GenerationService(db)

    acquired = False
    try:
        # очередь/таймаут на вход в генерацию
        gen_limit = float(settings.generation_timeout_sec)
        queue_timeout = max(20.0, min(gen_limit - 5.0, gen_limit / 2.0))

        await asyncio.wait_for(semaphore.acquire(), timeout=queue_timeout)
        acquired = True

        result = await generation_service.generate_image(request=request, user=user)
        return result

    except asyncio.TimeoutError:
        # очередь переполнена/ожидание слота
        if os.getenv("ENV", "").lower() == "dev":
            traceback.print_exc()
        raise HTTPException(status_code=429, detail="Service temporarily unavailable. Please try again later.")

    except RuntimeError as e:
        # нормализуем таймаут пайплайна
        msg = str(e)
        if "timed out" in msg.lower():
            if os.getenv("ENV", "").lower() == "dev":
                traceback.print_exc()
            raise HTTPException(status_code=504, detail="Generation timed out")
        # остальное — как 500/DEV traceback ниже
        if os.getenv("ENV", "").lower() == "dev":
            traceback.print_exc()
            lg("app").exception("generate.runtime_error")
            raise

        raise HTTPException(status_code=500, detail=f"Generation failed: {msg}")

    except ValueError as e:
        # валидации/oom и т.п.
        if os.getenv("ENV", "").lower() == "dev":
            traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # общее — DEV: проброс, PROD: компактный JSON
        if os.getenv("ENV", "").lower() == "dev":
            traceback.print_exc()
            lg("app").exception("generate.failed")
            raise
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    finally:
        if acquired:
            try:
                semaphore.release()
            except Exception:
                pass
