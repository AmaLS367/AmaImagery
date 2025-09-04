from hashlib import sha256
from time import time
from pathlib import Path
from app.config import settings

def prompt_hash(prompt: str, negative: str | None) -> str:
    return sha256((prompt + "||" + (negative or "")).encode()).hexdigest()[:16]

def out_path(stem: str) -> str:
    name = f"{stem}_{int(time())}.png"
    p = Path(settings.out_dir) / name
    return str(p)
