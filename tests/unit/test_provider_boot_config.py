import app.config as cfg
from app.domain.providers.registry import get_provider_registry


def test_settings_allow_missing_local_model_when_diffusers_not_required():
    settings = cfg.Settings(
        MODEL_ID="missing-model.safetensors",
        PROVIDERS_ENABLED=["comfyui"],
        PROVIDERS_DEFAULT_NAME="comfyui",
        NO_NETWORK=True,
    )

    assert settings.model_id == "missing-model.safetensors"
    assert settings.providers_enabled == ["comfyui"]


def test_provider_registry_boots_comfyui_without_diffusers(monkeypatch):
    monkeypatch.setattr(cfg.settings, "providers_enabled", ["comfyui"])
    monkeypatch.setattr(cfg.settings, "providers_default_name", "comfyui")
    monkeypatch.setattr(cfg.settings, "comfyui_base_url", "http://localhost:8188")

    registry = get_provider_registry()

    assert registry.list_providers() == ["comfyui"]
    assert registry.boot_errors() == {}


def test_provider_registry_reports_diffusers_boot_error(monkeypatch):
    monkeypatch.setattr(cfg.settings, "providers_enabled", ["diffusers"])
    monkeypatch.setattr(cfg.settings, "providers_default_name", "diffusers")
    monkeypatch.setattr(cfg.settings, "model_id", "missing-model.safetensors")

    registry = get_provider_registry()

    assert registry.list_providers() == []
    assert "diffusers" in registry.boot_errors()
