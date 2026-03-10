from __future__ import annotations

from pathlib import Path

from app.config import settings


class ProviderBootstrapError(RuntimeError):
    """Raised when a provider cannot be safely bootstrapped from current settings."""


def validate_diffusers_provider_settings() -> None:
    model_id = str(settings.model_id or "").strip()
    vae_id = str(settings.vae_id or "").strip() or None

    if _looks_like_local_model_path(model_id) and not Path(model_id).exists():
        raise ProviderBootstrapError(f"Diffusers MODEL_ID points to missing local file: {model_id}")

    if vae_id and _looks_like_local_model_path(vae_id) and not Path(vae_id).exists():
        raise ProviderBootstrapError(f"Diffusers VAE_ID points to missing local file: {vae_id}")


def validate_comfyui_provider_settings() -> None:
    if not str(settings.comfyui_base_url or "").strip():
        raise ProviderBootstrapError("ComfyUI provider requires COMFYUI_BASE_URL")


def _looks_like_local_model_path(value: str) -> bool:
    lower = value.lower()
    if lower.endswith((".safetensors", ".ckpt", ".pt", ".bin")):
        return True
    return any(sep in value for sep in ("/", "\\"))
