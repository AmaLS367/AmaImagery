from unittest.mock import Mock, patch

from app.config import settings


class _RegistryStub:
    def boot_snapshot(self):
        return Mock(
            as_dict=Mock(
                return_value={
                    "enabled_providers": ["comfyui"],
                    "booted_providers": [],
                    "failed_providers": ["comfyui"],
                    "boot_error_summaries": {"comfyui": "connection refused"},
                    "default_provider": "comfyui",
                    "default_provider_booted": False,
                }
            )
        )

    async def readiness_snapshot(self):
        return {
            "enabled_providers": ["comfyui"],
            "booted_providers": [],
            "failed_providers": ["comfyui"],
            "boot_error_summaries": {"comfyui": "connection refused"},
            "default_provider": "comfyui",
            "default_provider_booted": False,
            "provider_health": {},
            "default_provider_usable": False,
        }


def test_health_exposes_provider_boot_state(app_client):
    app_client.app.state.infrastructure_status = {
        "redis": {"status": "disabled", "error": None},
        "task_queue": {"backend": "memory", "ready": True, "error": None},
    }

    boot_snapshot = Mock(
        as_dict=Mock(
            return_value={
                "enabled_providers": ["comfyui"],
                "booted_providers": [],
                "failed_providers": ["comfyui"],
                "boot_error_summaries": {"comfyui": "connection refused"},
                "default_provider": "comfyui",
                "default_provider_booted": False,
            }
        )
    )

    with patch("app.api.v1.health.get_provider_boot_snapshot", return_value=boot_snapshot):
        response = app_client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "alive"
    assert payload["providers"]["enabled_providers"] == ["comfyui"]
    assert payload["providers"]["failed_providers"] == ["comfyui"]
    assert payload["providers"]["boot_error_summaries"]["comfyui"] == "connection refused"


def test_readiness_fails_when_default_provider_is_not_usable(app_client, monkeypatch):
    app_client.app.state.infrastructure_status = {
        "redis": {"status": "connected", "error": None},
        "task_queue": {"backend": "redis", "ready": True, "error": None},
    }
    monkeypatch.setattr(settings, "no_redis", False)

    with patch("app.api.v1.health.get_provider_registry", return_value=_RegistryStub()):
        response = app_client.get("/api/v1/healthz")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["default_provider_usable"] is False
    assert payload["generation_ready"] is False
