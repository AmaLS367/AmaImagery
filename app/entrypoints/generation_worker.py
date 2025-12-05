"""
Entrypoint for generation worker process.
"""

import asyncio
import signal
import sys

from app.core.logging import lg
from app.workers import run_worker


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    worker_log = lg("worker")
    
    def signal_handler(sig, frame):
        worker_log.info("worker.shutdown_signal", extra={"signal": sig})
        loop.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        loop.run_until_complete(run_worker())
    except KeyboardInterrupt:
        worker_log.info("worker.shutdown_keyboard")
    except Exception as e:
        worker_log.exception("worker.fatal_error", extra={"error": str(e)})
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()

