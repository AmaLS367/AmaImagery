"""
Central registry for image generation providers.

Manages the lifecycle and retrieval of registered providers strategies.
"""

import asyncio
from dataclasses import asdict, dataclass
from typing import Dict, Optional, List, Any, Tuple

from app.core.logging import lg
from app.domain.providers.interfaces import IImageProvider
from app.domain.providers.validation import (
    validate_comfyui_provider_settings,
    validate_diffusers_provider_settings,
)


@dataclass(frozen=True)
class ProviderBootSnapshot:
    enabled_providers: list[str]
    booted_providers: list[str]
    failed_providers: list[str]
    boot_error_summaries: dict[str, str]
    default_provider: str | None
    default_provider_booted: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProviderRegistry:
    """
    Strategy pattern registry.
    
    Allows the application to route requests to different implementations 
    (Diffusers, OpenAI, etc.) dynamically.
    """
    
    def __init__(
        self,
        providers: Optional[Dict[str, IImageProvider]] = None,
        default_name: Optional[str] = None,
        boot_errors: Optional[Dict[str, str]] = None,
        enabled_names: Optional[List[str]] = None,
    ):
        self._providers: Dict[str, IImageProvider] = providers or {}
        self._default_name = default_name
        self._boot_errors: Dict[str, str] = boot_errors or {}
        self._enabled_names: tuple[str, ...] = tuple(enabled_names or [])
    
    def register(self, name: str, provider: IImageProvider) -> None:
        self._providers[name] = provider
    
    def get(self, name: str) -> IImageProvider:
        """
        Retrieve a provider by name.
        """
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered")
        return self._providers[name]
    
    def get_default(self) -> IImageProvider:
        """
        Returns the preferred provider strategy.
        """
        if not self._providers:
            raise ValueError("No providers registered")
        
        if self._default_name and self._default_name in self._providers:
            return self._providers[self._default_name]
        
        # Fallback to the first available if default is not set
        return next(iter(self._providers.values()))
    
    def list_providers(self) -> List[str]:
        return list[str](self._providers.keys())

    def boot_errors(self) -> Dict[str, str]:
        return dict(self._boot_errors)

    def boot_snapshot(self) -> ProviderBootSnapshot:
        enabled = list(self._enabled_provider_names())
        booted = self.list_providers()
        failed = [name for name in enabled if name not in self._providers]
        return ProviderBootSnapshot(
            enabled_providers=enabled,
            booted_providers=booted,
            failed_providers=failed,
            boot_error_summaries={name: _summarize_error(error) for name, error in self._boot_errors.items()},
            default_provider=self._default_name,
            default_provider_booted=bool(self._default_name and self._default_name in self._providers),
        )

    async def health_report(self) -> Dict[str, bool]:
        """
        Aggregates health status from all registered providers concurrently.
        """
        async def check_provider(name: str, provider: IImageProvider) -> tuple[str, bool]:
            try:
                is_healthy = await provider.health_check()
                return (name, is_healthy)
            except Exception:
                return (name, False)
        
        if not self._providers:
            return {}

        tasks = [check_provider(name, provider) for name, provider in self._providers.items()]
        results = await asyncio.gather(*tasks)
        return dict[str, bool](results)

    async def readiness_snapshot(self) -> dict[str, Any]:
        boot = self.boot_snapshot()
        health = await self.health_report()
        default_provider = boot.default_provider
        default_provider_usable = bool(default_provider and health.get(default_provider, False))
        return {
            **boot.as_dict(),
            "provider_health": health,
            "default_provider_usable": default_provider_usable,
        }

    def _enabled_provider_names(self) -> tuple[str, ...]:
        names = list(dict.fromkeys(self._enabled_names))
        for name in self._boot_errors.keys():
            if name not in names:
                names.append(name)
        if self._default_name and self._default_name not in names:
            names.append(self._default_name)
        return tuple(names)


def get_provider_registry() -> ProviderRegistry:
    """
    Factory function that creates and configures the provider registry.
    
    Registers providers based on settings.providers_enabled and sets the default provider.
    """
    from app.config import settings

    signature = _settings_signature()
    global _provider_registry_cache
    global _provider_registry_signature

    if _provider_registry_cache is None or _provider_registry_signature != signature:
        _provider_registry_cache = _build_provider_registry()
        _provider_registry_signature = signature

    return _provider_registry_cache


def _build_provider_registry() -> ProviderRegistry:
    from app.config import settings

    providers: Dict[str, IImageProvider] = {}
    boot_errors: Dict[str, str] = {}
    logger = lg("providers")

    if "diffusers" in settings.providers_enabled:
        try:
            validate_diffusers_provider_settings()
            from app.infra.providers.diffusers_provider import DiffusersProvider

            providers["diffusers"] = DiffusersProvider()
        except Exception as exc:
            boot_errors["diffusers"] = str(exc)
            logger.warning("provider.bootstrap_failed", extra={"provider": "diffusers", "error": str(exc)})

    if "comfyui" in settings.providers_enabled:
        try:
            validate_comfyui_provider_settings()
            from app.infra.providers.comfyui_provider import ComfyUIProvider

            providers["comfyui"] = ComfyUIProvider()
        except Exception as exc:
            boot_errors["comfyui"] = str(exc)
            logger.warning("provider.bootstrap_failed", extra={"provider": "comfyui", "error": str(exc)})

    return ProviderRegistry(
        providers=providers,
        default_name=settings.providers_default_name,
        boot_errors=boot_errors,
        enabled_names=list(settings.providers_enabled or []),
    )


def _settings_signature() -> Tuple[Any, ...]:
    from app.config import settings

    return (
        tuple(settings.providers_enabled or []),
        settings.providers_default_name,
        settings.model_id,
        settings.vae_id,
        settings.comfyui_base_url,
        settings.comfyui_websocket_url,
        str(settings.comfyui_workflow_path or ""),
        str(settings.comfyui_workflow_map_path or ""),
        settings.comfyui_poll_interval_sec,
        settings.comfyui_timeout_sec,
    )


def _summarize_error(error: str) -> str:
    compact = " ".join(str(error).split())
    if len(compact) <= 160:
        return compact
    return f"{compact[:157]}..."


_provider_registry_cache: ProviderRegistry | None = None
_provider_registry_signature: Tuple[Any, ...] | None = None
