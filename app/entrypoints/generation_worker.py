"""
Entrypoint for generation worker process.
"""

import asyncio
import signal
import sys
import os

from app.core.logging import lg
from app.infra.redis import init_redis, close_redis, get_redis
from app.infra.queue import get_task_queue
from app.workers import run_worker


async def init_worker_infrastructure():
    """Initialize Redis connection and verify task queue in worker process."""
    worker_log = lg("worker")
    try:
        worker_log.info("worker.init_starting", extra={"pid": os.getpid()})
        
        # Initialize Redis
        await init_redis()
        redis_client = get_redis()
        if not redis_client:
            raise RuntimeError("Redis client is None after initialization")
        
        # Verify Redis connection
        ping_result = await redis_client.ping()
        if not ping_result:
            raise RuntimeError("Redis ping failed")
        
        worker_log.info("worker.redis_initialized", extra={"redis_url": "connected"})
        
        # Verify task queue can be created
        try:
            task_queue = get_task_queue()
            worker_log.info("worker.task_queue_ready")
        except Exception as e:
            worker_log.exception("worker.task_queue_init_failed", extra={"error": str(e)})
            raise
        
        worker_log.info("worker.infrastructure_ready")
        
    except Exception as e:
        worker_log.exception("worker.init_failed", extra={"error": str(e), "error_type": type(e).__name__})
        raise


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    worker_log = lg("worker")
    worker_log.info("worker.process_started", extra={"pid": os.getpid()})
    
    def signal_handler(sig, frame):
        worker_log.info("worker.shutdown_signal", extra={"signal": sig})
        try:
            loop.stop()
        except RuntimeError as exc:
            worker_log.warning("worker.loop_stop_failed", extra={"error": str(exc)})
    
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception as e:
        worker_log.warning("worker.signal_handler_failed", extra={"error": str(e)})
    
    try:
        # Initialize Redis and task queue before starting worker loop
        worker_log.info("worker.initializing_infrastructure")
        loop.run_until_complete(init_worker_infrastructure())
        
        # Start worker loop
        worker_log.info("worker.starting_main_loop")
        loop.run_until_complete(run_worker())
        
    except KeyboardInterrupt:
        worker_log.info("worker.shutdown_keyboard")
    except Exception as e:
        worker_log.exception("worker.fatal_error", extra={"error": str(e), "error_type": type(e).__name__})
        # Don't exit immediately, try to cleanup
        try:
            loop.run_until_complete(close_redis())
        except Exception as cleanup_exc:
            worker_log.warning("worker.emergency_cleanup_failed", extra={"error": str(cleanup_exc)})
        sys.exit(1)
    finally:
        # Cleanup Redis connection
        worker_log.info("worker.cleaning_up")
        try:
            loop.run_until_complete(close_redis())
        except Exception as e:
            worker_log.warning("worker.cleanup_failed", extra={"error": str(e)})
        finally:
            loop.close()
            worker_log.info("worker.process_exited")


if __name__ == "__main__":
    main()

