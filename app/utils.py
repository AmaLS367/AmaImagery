from hashlib import sha256
from time import time_ns
from pathlib import Path
from uuid import uuid4
import re

from app.config import settings

_SAFE_STEM_RE = re.compile(r"[^A-Za-z0-9._-]+")

def _safe_stem(value: str, max_len: int = 80) -> str:
    s = _SAFE_STEM_RE.sub("_", value).strip("._-")
    return s[:max_len] or "file"

def prompt_hash(prompt: str, negative: str | None) -> str:
    payload = f"{prompt}||{negative or ''}"
    return sha256(payload.encode("utf-8")).hexdigest()[:32]

def out_path(stem: str, ext: str = "png") -> str:
    safe = _safe_stem(stem)
    suffix = f"{time_ns()}_{uuid4().hex[:8]}"
    name = f"{safe}_{suffix}.{ext}"
    base = Path(settings.outputs_dir)
    base.mkdir(parents=True, exist_ok=True)
    return str(base / name)
