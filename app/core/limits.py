import asyncio
from app.config import settings

_gen_semaphore = asyncio.Semaphore(settings.max_concurrent_generations)

def get_gen_semaphore() -> asyncio.Semaphore:
    return _gen_semaphore
