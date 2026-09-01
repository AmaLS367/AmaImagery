# Models

AmaImagery is a code-only repository. It does not distribute model weights, datasets, or Hugging Face caches. The tracked `models/` directory contains only lightweight configuration required by optional local runtimes.

## Configure a Provider

- **ComfyUI:** run ComfyUI separately, obtain its checkpoints under their upstream terms, and set `COMFYUI_BASE_URL`.
- **Diffusers:** set `MODEL_ID` to a Hugging Face model identifier or to a local path outside Git. The default in `.env.example` is `runwayml/stable-diffusion-v1-5`.

For a first online Diffusers download, set `NO_NETWORK=false` and provide `HF_TOKEN` if the upstream model requires access approval. After the model is cached or placed at a local path, set `NO_NETWORK=true` for offline operation.

`VAE_ID`, `IP_ADAPTER_DIR`, and `IP_IMAGE_ENCODER_PATH` are optional and must point to assets obtained separately by the operator.

## Compliance

Model licenses do not become application licenses. Before downloading, using, redistributing, or serving a model, review its upstream license and the repository [NOTICE](../../../NOTICE.txt).

## Related Documents

- [Backend Providers](../backend/providers.md)
- [Docker](../docker/README.md)
- [Reference](../reference/README.md)
