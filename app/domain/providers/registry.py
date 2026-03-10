"""
Central registry for image generation providers.

Manages the lifecycle and retrieval of registered providers strategies.
"""

import asyncio
from typing import Dict, Optional, List

from app.core.logging import lg
from app.domain.providers.interfaces import IImageProvider
from app.domain.providers.validation import (
    validate_comfyui_provider_settings,
    validate_diffusers_provider_settings,
)


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
    ):
        self._providers: Dict[str, IImageProvider] = providers or {}
        self._default_name = default_name
        self._boot_errors: Dict[str, str] = boot_errors or {}
    
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


def get_provider_registry() -> ProviderRegistry:
    """
    Factory function that creates and configures the provider registry.
    
    Registers providers based on settings.providers_enabled and sets the default provider.
    """
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
    )
