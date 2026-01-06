"""
Main entry point for the application.
Starts both the FastAPI server and the generation worker.
"""
import asyncio
import multiprocessing
import signal
import sys
import uvicorn
from app.config import settings
from app.core.logging import lg
from app.infra.redis import get_redis, init_redis


def run_worker_process():
    """Run the generation worker in a separate process."""
    from app.entrypoints.generation_worker import main
    main()


async def check_redis_available() -> bool:
    """Check if Redis is available for worker."""
    if settings.no_redis:
        return False
    
    try:
        await init_redis()
        redis_client = get_redis()
        if redis_client:
            await redis_client.ping()
            return True
    except Exception:
        pass
    return False


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        reload=settings.debug,
        forwarded_allow_ips="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
        timeout_keep_alive=settings.keepalive_timeout_seconds,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger = lg("app")
    logger.info("Shutdown signal received, terminating processes...")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger = lg("app")
    logger.info("Starting application server. Worker will be started via FastAPI lifespan hooks.")
    
    try:
        # Run the server (this blocks)
        # Worker is started automatically via lifespan hooks in app/main.py
        run_server()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        logger.info("Shutdown complete")