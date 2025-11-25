# run_dev.py
import os
import socket
import logging
import uvicorn
from fastapi.responses import JSONResponse
from starlette.middleware.errors import ServerErrorMiddleware
from app.config import settings

os.environ["ENV"] = "dev"

def _apply_dev_env():
    os.environ.setdefault("ENV", "dev")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("PROMPTS_RAW", "1")
    os.environ.setdefault("NO_REDIS", "1")
    os.environ.setdefault("TORCH_SHOW_CPP_STACKTRACES", "1")
    os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "1")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:128")
    os.environ.setdefault("SECRET_KEY", "dev_" + "x"*48)
    os.environ.setdefault("DATABASE_URL", settings.database_url)
    
    os.environ.setdefault("REDIS_URL", "redis://:devpass@localhost:6379/0")

def _patch_outbound_network():
    if not hasattr(socket, "_orig_connect"):
        socket._orig_connect = socket.socket.connect  # type: ignore[attr-defined]
        def _dev_socket_connect(self, address):
            host = ""
            try:
                host = address[0] if isinstance(address, tuple) else ""
            except Exception:
                pass
            if host in ("127.0.0.1", "::1", "localhost"):
                return socket._orig_connect(self, address)  # type: ignore[attr-defined]
            raise OSError("Outbound network is disabled (dev runner)")
        socket.socket.connect = _dev_socket_connect  # type: ignore[assignment]

def _patch_sqlalchemy_types():
    """
    Делает SQLite совместимым с PG-типами без изменения моделей:
    JSONB -> JSON, ARRAY -> JSON, UUID/INET/CIDR/MACADDR -> TEXT/CHAR.
    """
    try:
        from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
        # JSONB
        if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
            def visit_JSONB(self, type_, **kw):  # noqa: N802
                return "JSON"
            SQLiteTypeCompiler.visit_JSONB = visit_JSONB  # type: ignore[attr-defined]
        # ARRAY
        if not hasattr(SQLiteTypeCompiler, "visit_ARRAY"):
            def visit_ARRAY(self, type_, **kw):  # noqa: N802
                return "JSON"
            SQLiteTypeCompiler.visit_ARRAY = visit_ARRAY  # type: ignore[attr-defined]
        # UUID
        if not hasattr(SQLiteTypeCompiler, "visit_UUID"):
            def visit_UUID(self, type_, **kw):  # noqa: N802
                return "CHAR(36)"
            SQLiteTypeCompiler.visit_UUID = visit_UUID  # type: ignore[attr-defined]
        # INET/CIDR/MACADDR -> TEXT
        for pg_net in ("INET", "CIDR", "MACADDR"):
            if not hasattr(SQLiteTypeCompiler, f"visit_{pg_net}"):
                def _mk(pgname):
                    def _visit(self, type_, **kw):  # noqa: N802
                        return "TEXT"
                    _visit.__name__ = f"visit_{pgname}"
                    return _visit
                setattr(SQLiteTypeCompiler, f"visit_{pg_net}", _mk(pg_net))  # type: ignore[attr-defined]
    except Exception:
        # не мешаем старту даже если SQLA внезапно поменялась
        pass

def _apply_dev_patches():
    _apply_dev_env()
    _patch_outbound_network()
    _patch_sqlalchemy_types()

def get_app():
    _apply_dev_patches()

    # импорт после патчей
    from app import main as m  # не трогаем прод-файлы

    # 1) вырубаем инициализацию Redis внутри lifespan
    async def _noop_initialize_redis():
        logging.getLogger("uvicorn.error").warning(
            "Redis init skipped by run_dev patch", extra={"event_type": "app"}
        )
        return None
    if hasattr(m, "_initialize_redis"):
        m._initialize_redis = _noop_initialize_redis  # type: ignore[assignment]

    # 2) форсируем debug-режим FastAPI и подробные трейсбеки
    try:
        m.app.debug = True
    except Exception:
        pass

    # 3) включаем middleware, который печатает traceback и отдаёт его в ответ (debug=True)
    #   добавляем поверх, не меняя prod-код
    m.app.add_middleware(ServerErrorMiddleware, debug=True)

    # 4) универсальный ловец всех необработанных исключений, чтобы точно видеть причину
    @m.app.exception_handler(Exception)
    async def _unhandled(request, exc):  # type: ignore[override]
        logging.getLogger("uvicorn.error").exception(
            "UNHANDLED",
            extra={"event_type": "app", "path": str(request.url), "method": request.method},
        )
        # возвращаем текст ошибки в dev, чтобы быстрее починить
        return JSONResponse(
            status_code=500,
            content={"error": "http_error", "status": 500, "message": str(exc)},
        )

    # 5) выключаем лимитёры в dev режиме через настройки
    if hasattr(m, "settings"):
        try:
            setattr(m.settings, "limits_enabled", False)
        except Exception:
            pass

    return m.app


if __name__ == "__main__":
    uvicorn.run(
        "run_dev:get_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
        timeout_keep_alive=int(os.getenv("KEEPALIVE_TIMEOUT_SECONDS", "5")),
    )
