# Provider Abstraction Layer

## Overview

The provider abstraction layer decouples the application from specific image generation implementations, enabling switching between different providers (diffusers, external APIs, etc.) without changing application code.

## Architecture

```
┌─────────────────┐
│  API / Services │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ProviderRegistry│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ IImageProvider   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌───▼───┐
│Diffusers│ │External│
│Provider │ │Provider │
└────────┘ └────────┘
```

## Core Components

### IImageProvider

Protocol interface that all image generation providers must implement:

```python
class IImageProvider(Protocol):
    async def generate(request: GenerationRequest) -> GenerationResult
    async def health_check() -> bool
    def supports_features(features: set[str]) -> bool
```

**Purpose:** Defines a unified contract for image generation, allowing the application to work with any provider through a consistent interface.

### GenerationRequest

Domain DTO containing all parameters needed for image generation:

- `prompt: str` - Main generation prompt
- `negative_prompt: Optional[str]` - Negative prompt
- `seed: Optional[int]` - Random seed for reproducibility
- `width: int` - Image width
- `height: int` - Image height
- `steps: Optional[int]` - Number of inference steps
- `guidance_scale: Optional[float]` - Guidance scale
- `ref_image_b64: Optional[str]` - Base64 reference image for IP-Adapter
- `ip_scale: Optional[float]` - IP-Adapter scale
- `style: Style` - Visual style ('realistic' or 'anime')

**Purpose:** Provider-agnostic request format that isolates application code from provider-specific parameter structures.

### GenerationResult

Domain DTO containing the output of image generation:

- `image_path: str` - Path to the generated image
- `metadata: Dict[str, Any]` - Technical and business metadata

**Purpose:** Normalizes output from different providers, allowing application code to work with results uniformly.

### ProviderRegistry

Central registry that manages provider instances and routes requests:

```python
class ProviderRegistry:
    def register(name: str, provider: IImageProvider) -> None
    def get(name: str) -> IImageProvider
    def get_default() -> IImageProvider
    def list_providers() -> list[str]
    async def health_report() -> Dict[str, bool]
```

**Purpose:** Isolates application code from provider selection logic, enabling runtime provider switching and health monitoring.

## Configuration

### Environment Variables

- `PROVIDERS_DEFAULT_NAME` - Name of the default provider (default: `"diffusers"`)
- `PROVIDERS_ENABLED` - Comma-separated list of enabled providers (default: `"diffusers"`)

### Example Configuration

```bash
PROVIDERS_DEFAULT_NAME=diffusers
PROVIDERS_ENABLED=diffusers
```

### Selecting Default Provider

The default provider is selected via `PROVIDERS_DEFAULT_NAME` environment variable. The registry uses this value when calling `get_default()`:

1. If `default_name` is set and provider exists → returns that provider
2. Otherwise → returns first registered provider
3. If no providers registered → raises `ValueError`

## Usage

### Getting Provider from Registry

```python
from app.domain.providers import get_provider_registry

registry = get_provider_registry()
provider = registry.get_default()

result = await provider.generate(request)
```

### Checking Provider Health

```python
registry = get_provider_registry()
health_status = await registry.health_report()
# Returns: {"diffusers": True, "external_api": False}
```

### Checking Feature Support

```python
provider = registry.get_default()
supports_ip = provider.supports_features({"ip_adapter"})
```

## Current Providers

### DiffusersProvider

Implementation using the diffusers library for local Stable Diffusion inference.

**Location:** `app/infra/providers/diffusers_provider.py`

**Features:**
- Text-to-image generation
- IP-Adapter support for image conditioning
- Device and dtype management
- Timeout enforcement
- Memory management

**Configuration:** Uses existing model configuration (`MODEL_ID`, `DEVICE`, `TORCH_DTYPE`, etc.)

## Adding New Providers

To add a new provider:

1. Implement `IImageProvider` interface
2. Register in `get_provider_registry()` function
3. Add provider name to `PROVIDERS_ENABLED` if needed
4. Update `PROVIDERS_DEFAULT_NAME` to use new provider

Example:

```python
# In app/infra/providers/external_api_provider.py
class ExternalAPIProvider:
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        # Implementation
        pass
    
    async def health_check(self) -> bool:
        # Implementation
        pass
    
    def supports_features(self, features: set[str]) -> bool:
        # Implementation
        pass

# In app/domain/providers/registry.py
def get_provider_registry() -> ProviderRegistry:
    # ...
    if "external_api" in settings.providers_enabled:
        from app.infra.providers.external_api_provider import ExternalAPIProvider
        providers["external_api"] = ExternalAPIProvider()
```

## Benefits

- **Decoupling:** Application code doesn't depend on specific ML libraries
- **Flexibility:** Easy to switch or add providers
- **Testability:** Providers can be mocked for testing
- **Maintainability:** Provider-specific logic is isolated

