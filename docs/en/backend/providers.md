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
    async def submit(request: GenerationRequest) -> ProviderSubmission
    async def wait_for_result(submission: ProviderSubmission, timeout_sec: float) -> ProviderResult
    async def cancel(submission: ProviderSubmission) -> None
    async def health_check() -> bool
    def supports_features(features: set[str]) -> bool
```

**Purpose:** Defines a lifecycle-aware contract for image generation, allowing the worker to submit, wait, and fail consistently across local and remote providers.

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

### ProviderSubmission

Submission DTO persisted after `submit()`:

- `provider_name: str`
- `provider_job_id: Optional[str]`
- `provider_state: Dict[str, Any]`
- `metadata: Dict[str, Any]`

### ProviderResult

Result DTO returned after `wait_for_result()`:

- `image_path: str` - Path to the generated image
- `provider_job_id: Optional[str]`
- `provider_state: Dict[str, Any]`
- `metadata: Dict[str, Any]`
- `artifact_persisted: bool`

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
PROVIDERS_ENABLED=diffusers,comfyui
PROVIDERS_DEFAULT_NAME=diffusers
COMFYUI_BASE_URL=http://host.docker.internal:8188
COMFYUI_WEBSOCKET_URL=ws://host.docker.internal:8188/ws
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

submission = await provider.submit(request)
result = await provider.wait_for_result(submission, timeout_sec=300)
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

### ComfyUIProvider

Remote provider adapter for ComfyUI workflow execution.

**Location:** `app/infra/providers/comfyui_provider.py`

**Features:**
- Workflow submit via `/prompt`
- Completion tracking via websocket with polling fallback
- Remote artifact retrieval via `/view`
- Canonical local artifact persistence after download

## Verification Profiles

For live verification and rollout, use:

- `docker/.env.verify.diffusers.example`
- `docker/.env.verify.comfyui.example`

The rollout target after successful verification is `PROVIDERS_DEFAULT_NAME=comfyui`, while keeping `diffusers` enabled as fallback.

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

