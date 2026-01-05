"""
Main entry point for the application.
Starts both the FastAPI server and the generation worker.
"""
import multiprocessing
import signal
import sys
import uvicorn
from app.config import settings
from app.core.logging import lg


def run_worker_process():
    """Run the generation worker in a separate process."""
    from app.entrypoints.generation_worker import main
    main()


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
    
    # Start worker in a separate process
    worker_process = multiprocessing.Process(target=run_worker_process, name="GenerationWorker")
    worker_process.daemon = True  # Worker will terminate when main process exits
    worker_process.start()
    
    logger = lg("app")
    logger.info(f"Generation worker started (PID: {worker_process.pid})")
    
    try:
        # Run the server (this blocks)
        run_server()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Terminate worker process
        if worker_process.is_alive():
            logger.info("Terminating worker process...")
            worker_process.terminate()
            worker_process.join(timeout=5)
            if worker_process.is_alive():
                logger.warning("Worker process did not terminate gracefully, forcing kill...")
                worker_process.kill()
                worker_process.join()
        logger.info("Shutdown complete")