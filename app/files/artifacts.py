from __future__ import annotations

import shutil
import time
from pathlib import Path
from urllib.parse import quote

from app.config import settings
from app.files.signing import make_signature
from app.files.validators import safe_join


class ArtifactService:
    def __init__(self, outputs_dir: Path | None = None) -> None:
        self.outputs_dir = Path(outputs_dir or settings.outputs_dir)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def canonical_name(self, generation_id: str, source_path: str | Path | None = None, default_ext: str = "png") -> str:
        ext = default_ext
        if source_path:
            suffix = Path(source_path).suffix.lstrip(".").lower()
            if suffix:
                ext = suffix
        return f"{generation_id}.{ext}"

    def local_path(self, filename: str) -> Path:
        return safe_join(filename)

    def persist_local(self, generation_id: str, source_path: str | Path, default_ext: str = "png") -> str:
        src = Path(source_path)
        filename = self.canonical_name(generation_id, src, default_ext=default_ext)
        dst = self.outputs_dir / filename
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        return str(dst)

    async def persist_bytes(self, generation_id: str, payload: bytes, ext: str = "png") -> str:
        filename = self.canonical_name(generation_id, default_ext=ext)
        dst = self.outputs_dir / filename
        dst.write_bytes(payload)
        return str(dst)

    def build_signed_download(self, image_path: str | None) -> dict[str, int | str | None]:
        if not image_path:
            return {"image_filename": None, "image_url": None, "exp": None, "sig": None}
        filename = Path(image_path).name
        now = int(time.time())
        exp = now + int(settings.file_download_ttl_sec)
        sig = make_signature(filename, exp)
        image_url = f"/api/v1/file?path={quote(filename)}&exp={exp}&sig={sig}"
        return {
            "image_filename": filename,
            "image_url": image_url,
            "exp": exp,
            "sig": sig,
        }


_artifact_service: ArtifactService | None = None


def get_artifact_service() -> ArtifactService:
    global _artifact_service
    if _artifact_service is None:
        _artifact_service = ArtifactService()
    return _artifact_service
