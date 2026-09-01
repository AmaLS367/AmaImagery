"""
Main entry point for the application server.
"""

import signal
import sys
from typing import Any

import uvicorn

from app.config import settings
from app.core.logging import lg


def run_server() -> None:
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


def signal_handler(sig: int, frame: Any) -> None:
    """Handle shutdown signals gracefully."""
    logger = lg("app")
    logger.info("Shutdown signal received, terminating processes...")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger = lg("app")
    logger.info("Starting application server. Run the generation worker separately if queue processing is needed.")

    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        logger.info("Shutdown complete")
