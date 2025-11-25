from pathlib import Path
from typing import Iterable
from starlette.responses import JSONResponse
from app.config import settings

BASE = Path(settings.outputs_dir).resolve()
ALLOWED_EXTS = {e.lower() for e in settings.file_allowed_exts}
ALLOWED_MIMES = set(settings.file_allowed_mimes)

def safe_join(name: str) -> Path:
    if not name or len(name) > 128:
        raise ValueError("invalid_name")
    if "/" in name or "\\" in name:
        raise ValueError("invalid_name")
    p = (BASE / name).resolve()
    if not str(p).startswith(str(BASE)):
        raise ValueError("traversal")
    return p

def check_ext(path: Path) -> None:
    ext = path.suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError("forbidden_extension")

def check_mime(mime: str | None) -> None:
    if not mime or mime.lower() not in ALLOWED_MIMES:
        raise ValueError("forbidden_mime")

def error(status: int, code: str, msg: str) -> JSONResponse:
    return JSONResponse({"error": code, "message": msg}, status_code=status)
