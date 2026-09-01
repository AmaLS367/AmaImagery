from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.config import settings

_gen_semaphore: asyncio.Semaphore | None = None
_gen_limit_cached: int | None = None


def get_gen_semaphore() -> asyncio.Semaphore:
    global _gen_semaphore, _gen_limit_cached
    limit = settings.max_concurrent_generations
    if limit < 1:
        limit = 1

    if _gen_semaphore is None or _gen_limit_cached != limit:
        _gen_semaphore = asyncio.Semaphore(limit)
        _gen_limit_cached = limit

    return _gen_semaphore


async def try_acquire(timeout_sec: float = 0.0) -> bool:
    sem = get_gen_semaphore()
    try:
        await asyncio.wait_for(sem.acquire(), timeout=timeout_sec)
        return True
    except TimeoutError:
        return False


@asynccontextmanager
async def gen_slot(timeout_sec: float | None = None) -> AsyncIterator[bool]:
    sem = get_gen_semaphore()
    acquired = False
    try:
        if timeout_sec is None:
            await sem.acquire()
            acquired = True
        else:
            acquired = await try_acquire(timeout_sec)
        if not acquired:
            yield False
            return
        yield True
    finally:
        if acquired:
            sem.release()
