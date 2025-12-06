import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
        timeout_keep_alive=settings.keepalive_timeout_seconds,
    )