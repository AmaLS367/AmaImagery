"""
Central registry that routes generation requests to the appropriate provider.

Enables provider selection and switching without changing application code.
"""

from typing import Dict, Optional
from app.domain.providers.base import IImageProvider


class ProviderRegistry:
    """
    Centralized provider registry that isolates application code from provider selection logic.
    
    Raises KeyError if a requested provider is not registered.
    """
    
    def __init__(self, providers: Optional[Dict[str, IImageProvider]] = None, default_name: Optional[str] = None):
        self._providers: Dict[str, IImageProvider] = providers or {}
        self._default_name = default_name
    
    def register(self, name: str, provider: IImageProvider) -> None:
        self._providers[name] = provider
    
    def get(self, name: str) -> IImageProvider:
        """
        Raises KeyError if provider is not registered.
        """
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered")
        return self._providers[name]
    
    def get_default(self) -> IImageProvider:
        """
        Returns provider registered under default_name, or first registered provider if default_name is None.
        
        Raises ValueError if no providers are registered.
        """
        if not self._providers:
            raise ValueError("No providers registered")
        
        if self._default_name and self._default_name in self._providers:
            return self._providers[self._default_name]
        
        return next(iter(self._providers.values()))
    
    def list_providers(self) -> list[str]:
        return list(self._providers.keys())
    
    async def health_report(self) -> Dict[str, bool]:
        """
        Checks all providers concurrently via asyncio.gather.
        Returns False for any provider that raises during health_check().
        """
        import asyncio
        
        async def check_provider(name: str, provider: IImageProvider) -> tuple[str, bool]:
            try:
                is_healthy = await provider.health_check()
                return (name, is_healthy)
            except Exception:
                return (name, False)
        
        tasks = [check_provider(name, provider) for name, provider in self._providers.items()]
        results = await asyncio.gather(*tasks)
        return dict(results)


_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """
    Returns singleton registry instance with providers registered from configuration.
    
    Lazy-initializes DiffusersProvider on first access to avoid heavy imports at module load time.
    Checks feature flags before registering providers.
    """
    global _registry
    if _registry is None:
        from app.config import settings
        from app.core.feature_flags import get_feature_flag_service
        
        feature_flags = get_feature_flag_service()
        
        if not feature_flags.is_enabled("image_generation"):
            raise ValueError("Image generation feature is disabled")
        
        providers: dict[str, IImageProvider] = {}
        
        if "diffusers" in settings.providers_enabled:
            from app.infra.providers import DiffusersProvider
            providers["diffusers"] = DiffusersProvider()
        
        _registry = ProviderRegistry(
            providers=providers,
            default_name=settings.providers_default_name
        )
    return _registry

