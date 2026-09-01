import os
from pathlib import Path
from typing import Any

import torch
from diffusers import DPMSolverMultistepScheduler
from diffusers.models.attention_processor import AttnProcessor, AttnProcessor2_0
from diffusers.models.autoencoders.autoencoder_kl import AutoencoderKL
from diffusers.pipelines.auto_pipeline import AutoPipelineForText2Image
from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import StableDiffusionPipeline
from huggingface_hub import snapshot_download
from loguru import logger

from app.config import settings
from app.core.logging import lg

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

_pipe: Any | None = None
_ip_ready = False


# --- online/offline switch & cache helpers ---


def _is_offline() -> bool:
    """Check if running in offline mode based on settings."""
    return settings.hf_hub_offline or settings.transformers_offline or settings.diffusers_offline or settings.no_network


def _project_root() -> Path:
    """Get project root directory."""
    # from app/inference/pipeline.py -> project root
    return Path(__file__).resolve().parents[2]


def _hub_candidates() -> list[Path]:
    """
    Get candidate directories for HuggingFace cache.

    Priority order:
    1. Explicit HUGGINGFACE_HUB_CACHE from settings
    2. HF_HOME/hub from settings
    3. Project models/.cache/huggingface/hub
    4. CWD models/.cache/huggingface/hub
    5. User home ~/.cache/huggingface/hub
    """
    c: list[Path] = []

    # Priority 1: Explicit hub cache path
    if settings.huggingface_hub_cache:
        c.append(settings.huggingface_hub_cache)

    # Priority 2: HF_HOME/hub
    if settings.hf_home:
        c.append(settings.hf_home / "hub")
    c.append(_project_root() / "models" / ".cache" / "huggingface" / "hub")
    c.append(Path.cwd() / "models" / ".cache" / "huggingface" / "hub")
    c.append(Path.home() / ".cache" / "huggingface" / "hub")
    # de-duplicate while keeping order
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in c:
        s = str(p)
        if s not in seen:
            seen.add(s)
            uniq.append(p)
    return uniq


def _find_snapshot(repo: str) -> Path | None:
    repo_dir = f"models--{repo.replace('/', '--')}"
    for hub in _hub_candidates():
        snaps_root = hub / repo_dir / "snapshots"
        if snaps_root.exists():
            snaps = sorted(snaps_root.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if snaps:
                lg("app").bind(event="hf_cache", hub=str(hub), repo=repo).info("Using HF hub cache")
                return snaps[0]
    return None


def _ensure_snapshot(repo: str, offline: bool) -> Path:
    snap = _find_snapshot(repo)
    if snap:
        return snap
    if offline:
        raise RuntimeError(f"Missing local snapshot '{repo}'. Warm the cache online once.")
    snapshot_download(repo, local_files_only=False)  # nosec B615
    # Double check after download
    snap = _find_snapshot(repo)
    if not snap:
        raise RuntimeError(f"Snapshot '{repo}' not found after download")
    return snap


def _align_ip_encoders(pipe: Any) -> None:
    dev = next(pipe.unet.parameters()).device
    dt = next(pipe.unet.parameters()).dtype

    enc = getattr(pipe, "image_encoder", None)
    if enc is not None:
        try:
            pipe.image_encoder = enc.to(device=dev, dtype=dt)
        except Exception:
            pipe.image_encoder = enc.to(device=dev)

    adapters = getattr(pipe, "ip_adapter", None)
    if not adapters:
        return
    if isinstance(adapters, dict):
        it = list(adapters.values())
    elif isinstance(adapters, (list, tuple)):
        it = list(adapters)
    else:
        it = [adapters]

    for a in it:
        enc2 = getattr(a, "image_encoder", None)
        if enc2 is not None:
            try:
                a.image_encoder = enc2.to(device=dev, dtype=dt)
            except Exception:
                a.image_encoder = enc2.to(device=dev)


def _move_ip_encoders_to_cpu(pipe: Any) -> None:
    # Global image_encoder -> CPU FP32
    enc = getattr(pipe, "image_encoder", None)
    if enc is not None:
        try:
            pipe.image_encoder = enc.to(device="cpu", dtype=torch.float32)
        except Exception:
            pipe.image_encoder = enc.to(device="cpu")
    # Nested encoders inside ip_adapter -> CPU FP32
    adapters = getattr(pipe, "ip_adapter", None)
    if not adapters:
        return
    if isinstance(adapters, dict):
        it = list(adapters.values())
    elif isinstance(adapters, (list, tuple)):
        it = list(adapters)
    else:
        it = [adapters]

    for a in it:
        enc2 = getattr(a, "image_encoder", None)
        if enc2 is not None:
            try:
                a.image_encoder = enc2.to(device="cpu", dtype=torch.float32)
            except Exception:
                a.image_encoder = enc2.to(device="cpu")


def _align_ipadapter_long_buffers_to_unet_device(pipe: Any) -> None:
    dev = next(pipe.unet.parameters()).device

    adapters = getattr(pipe, "ip_adapter", None)
    if not adapters:
        return

    if isinstance(adapters, dict):
        it = list(adapters.values())
    elif isinstance(adapters, (list, tuple)):
        it = list(adapters)
    else:
        it = [adapters]

    for a in it:
        # Iterate over all nested buffers
        for name, buf in a.named_buffers(recurse=True):
            if buf is None:
                continue
            # Skip image_encoder buffers (should remain on CPU)
            if name.startswith("image_encoder") or "image_encoder" in name:
                continue
            # Migrate only if device differs
            if buf.device != dev:
                try:
                    # Move buffer to UNet device; preserve dtype
                    a._buffers[name] = buf.to(dev)
                except Exception:
                    # If buffer is frozen/non-persistent, attempt replacing via register_buffer
                    try:
                        a.register_buffer(name, buf.to(dev), persistent=False)
                    except Exception as exc:
                        logger.debug(
                            "ip_adapter_buffer_register_failed", extra={"buffer_name": name, "error": str(exc)}
                        )


def get_pipeline() -> Any:
    global _pipe
    if _pipe is not None:
        return _pipe

    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    want_cuda = str(getattr(settings, "device", "cuda")).lower() != "cpu"
    device = "cuda" if (torch.cuda.is_available() and want_cuda) else "cpu"
    _dtype_map = {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}
    requested_dtype = _dtype_map.get(getattr(settings, "torch_dtype", "fp16").lower(), torch.float16)
    # CPU doesn't support float16, use float32 instead
    dtype = torch.float32 if device == "cpu" else requested_dtype

    mid = settings.model_id
    offline = _is_offline()

    # 1) LDM .safetensors
    if os.path.isfile(mid) and mid.lower().endswith((".safetensors", ".ckpt")):
        # Resolve SD1.5 config first (used also as VAE fallback)
        sd15_cfg = _ensure_snapshot("runwayml/stable-diffusion-v1-5", offline)

        def _pick_local_vae_dir(sd15: Path) -> Path | None:
            """Prefer explicit project VAE dir, else SD1.5 VAE, else None."""
            proj = Path("models/vae")
            if proj.exists():
                return proj
            sd15_vae = sd15 / "vae"
            return sd15_vae if sd15_vae.exists() else None

        vae = None
        vid_raw = getattr(settings, "vae_id", None)
        vid = str(vid_raw).strip() if vid_raw else ""

        if offline:
            # OFFLINE: ignore HF repo ids; use only local dirs
            if vid and Path(vid).exists():
                vae = AutoencoderKL.from_pretrained(str(Path(vid)), torch_dtype=dtype, local_files_only=True)
            else:
                local_vae_dir = _pick_local_vae_dir(sd15_cfg)
                if not local_vae_dir:
                    raise RuntimeError(
                        "Offline mode: no local VAE found (VAE_ID path missing, models/vae missing, SD1.5 VAE missing)"
                    )
                vae = AutoencoderKL.from_pretrained(str(local_vae_dir), torch_dtype=dtype, local_files_only=True)
        else:
            # ONLINE: local dir wins; otherwise treat VAE_ID as repo id and fetch/cache
            if vid and Path(vid).exists():
                vae = AutoencoderKL.from_pretrained(str(Path(vid)), torch_dtype=dtype, local_files_only=True)
            elif vid:
                vae_snap = _ensure_snapshot(vid, offline=False)
                vae = AutoencoderKL.from_pretrained(
                    str(Path(vae_snap)),  # normalize to str path
                    torch_dtype=dtype,
                    local_files_only=offline,
                )
            else:
                # default to SD1.5 VAE
                vae_dir = _pick_local_vae_dir(sd15_cfg)
                if vae_dir:
                    vae = AutoencoderKL.from_pretrained(str(vae_dir), torch_dtype=dtype, local_files_only=False)

        sd15_cfg = _ensure_snapshot("runwayml/stable-diffusion-v1-5", offline)
        cfg_dir = Path(sd15_cfg)
        mi = cfg_dir / "model_index.json"
        if not mi.exists():
            raise RuntimeError(f"SD1.5 config repo is invalid: missing {mi}")

        # Explicitly load tokenizer and text_encoder to avoid "vocab_file is None" errors
        # Load from the config repo (runwayml/stable-diffusion-v1-5) which should have them
        from transformers import CLIPTextModel, CLIPTokenizer

        tokenizer = None
        text_encoder = None

        # Try loading from config directory subdirectories
        tokenizer_dir = cfg_dir / "tokenizer"
        text_encoder_dir = cfg_dir / "text_encoder"

        # Load tokenizer
        if tokenizer_dir.exists() and (tokenizer_dir / "vocab.json").exists():
            try:
                tokenizer = CLIPTokenizer.from_pretrained(str(tokenizer_dir), local_files_only=offline)  # nosec B615
            except Exception as e:
                lg("app").debug(f"Failed to load tokenizer from {tokenizer_dir}: {e}")

        # If tokenizer not loaded from subdir, try loading from repo
        if tokenizer is None:
            try:
                tokenizer = CLIPTokenizer.from_pretrained(
                    "openai/clip-vit-large-patch14" if offline else "runwayml/stable-diffusion-v1-5",
                    subfolder="tokenizer" if not offline else None,
                    local_files_only=offline,
                )  # nosec B615
            except Exception as e:
                lg("app").warning(f"Failed to load tokenizer from repo: {e}")

        # Load text_encoder
        if text_encoder_dir.exists() and (text_encoder_dir / "config.json").exists():
            try:
                text_encoder = CLIPTextModel.from_pretrained(
                    str(text_encoder_dir), torch_dtype=dtype, local_files_only=offline
                )  # nosec B615
            except Exception as e:
                lg("app").debug(f"Failed to load text_encoder from {text_encoder_dir}: {e}")

        # If text_encoder not loaded from subdir, try loading from repo
        if text_encoder is None:
            try:
                text_encoder = CLIPTextModel.from_pretrained(
                    "openai/clip-vit-large-patch14" if offline else "runwayml/stable-diffusion-v1-5",
                    subfolder="text_encoder" if not offline else None,
                    torch_dtype=dtype,
                    local_files_only=offline,
                )  # nosec B615
            except Exception as e:
                lg("app").warning(f"Failed to load text_encoder from repo: {e}")

        # Build pipe kwargs - always include tokenizer and text_encoder if loaded
        # Use repo_id for config instead of local path to avoid "config.json not found" errors
        # from_single_file will load config from the repo if config path doesn't have all required files
        pipe_kwargs = {
            "config": "runwayml/stable-diffusion-v1-5" if not offline else str(cfg_dir),
            "torch_dtype": dtype,
            "vae": vae,
            "use_safetensors": True,
            "safety_checker": None,
            "feature_extractor": None,
            "local_files_only": offline,
        }

        if tokenizer is not None:
            pipe_kwargs["tokenizer"] = tokenizer
        if text_encoder is not None:
            pipe_kwargs["text_encoder"] = text_encoder

        pipe = StableDiffusionPipeline.from_single_file(mid, **pipe_kwargs)

    else:
        # 2) HF repository or local directory with model_index.json
        if offline and not os.path.exists(mid):
            raise RuntimeError("OFFLINE mode enabled and model_id is not a local path")
        pipe = AutoPipelineForText2Image.from_pretrained(
            mid,
            torch_dtype=dtype,
            use_safetensors=True,
            local_files_only=offline,
        )

    # --- Scheduler: replace with DPMSolver++ (Karras, 2nd order) ---
    try:
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config,
            algorithm_type="sde-dpmsolver++",
            use_karras_sigmas=True,
            solver_order=2,
        )
    except Exception as exc:
        logger.debug(f"scheduler_swap_failed: {exc}")

    # --- Memory optimizations ---
    pipe.unet.set_attn_processor(AttnProcessor2_0())
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    pipe.enable_vae_tiling()
    # xformers is optional - only enable if available
    try:
        pipe.enable_xformers_memory_efficient_attention()
    except (ModuleNotFoundError, ValueError) as e:
        lg("app").debug(f"xformers not available, skipping: {e}")

    pipe.set_progress_bar_config(disable=True)

    if device == "cuda":
        pipe.unet.to(memory_format=torch.channels_last)

    # Log: base model loaded and configured
    lg("app").bind(
        event="model.loaded",
        model_id=settings.model_id,
        device=device,
        torch_version=getattr(torch, "__version__", "unknown"),
        diffusers_version=getattr(__import__("diffusers"), "__version__", "unknown"),
    ).info("model.loaded")

    # --- begin: force device sync (exec device, text/image encoders) ---
    try:
        dev = torch.device(device)

        # Base dtype of pipeline: fp16 on CUDA, fp32 otherwise
        pipe.to(device=dev, dtype=dtype)

        # UNet/VAE strictly in pipeline dtype
        if getattr(pipe, "unet", None) is not None:
            pipe.unet.to(device=dev, dtype=dtype)
        if getattr(pipe, "vae", None) is not None:
            pipe.vae.to(device=dev, dtype=dtype)

        # text_encoder stays FP32 (on same device), image_encoder is always CPU/FP32
        text_encoder = getattr(pipe, "text_encoder", None)
        if text_encoder is not None:
            text_encoder.to(device=dev, dtype=torch.float32)
        image_encoder = getattr(pipe, "image_encoder", None)
        if image_encoder is not None:
            image_encoder.to(device="cpu", dtype=torch.float32)

    except Exception:
        logger.exception("device_sync_failed")
    # --- end: force device sync ---

    # --- Unified patch: synchronize dtype for sample/timestep and time_embedding input ---
    try:
        unet = pipe.unet
        unet_dtype = next(unet.parameters()).dtype

        _old_unet_forward = unet.forward

        def _unet_forward(sample: Any, timestep: Any, *args: Any, **kwargs: Any) -> Any:
            if isinstance(sample, torch.Tensor) and sample.dtype != unet_dtype:
                sample = sample.to(dtype=unet_dtype)
            if isinstance(timestep, torch.Tensor) and timestep.dtype != unet_dtype:
                timestep = timestep.to(dtype=unet_dtype)

            enc = kwargs.get("encoder_hidden_states", None)
            if isinstance(enc, torch.Tensor) and enc.dtype != unet_dtype:
                kwargs["encoder_hidden_states"] = enc.to(dtype=unet_dtype)
            elif enc is None and len(args) >= 1 and isinstance(args[0], torch.Tensor) and args[0].dtype != unet_dtype:
                args = (args[0].to(dtype=unet_dtype),) + args[1:]

            return _old_unet_forward(sample, timestep, *args, **kwargs)

        unet.forward = _unet_forward
    except Exception:
        logger.exception("unet_time_embedding_patch_failed")

    # --- Patch: time_embedding.forward -> cast input to TE weights dtype ---
    try:
        _unet2 = getattr(pipe, "unet", None)
        te = getattr(_unet2, "time_embedding", None)
        if te is not None and hasattr(te, "linear_1"):
            _old_te_forward = te.forward
            te_w_dtype = te.linear_1.weight.dtype

            def _te_forward(x: Any, *a: Any, **kw: Any) -> Any:
                if isinstance(x, torch.Tensor) and x.dtype != te_w_dtype:
                    x = x.to(dtype=te_w_dtype)
                return _old_te_forward(x, *a, **kw)

            te.forward = _te_forward
    except Exception:
        logger.exception("time_embedding_patch_failed")

    # --- Patch: VAE.decode -> cast z to VAE dtype before post_quant_conv ---
    try:
        vae = getattr(pipe, "vae", None)
        if vae is not None:
            vae_dtype = next(vae.parameters()).dtype
            _old_decode = vae.decode

            def _decode(z: Any, *a: Any, **kw: Any) -> Any:
                if isinstance(z, torch.Tensor) and z.dtype != vae_dtype:
                    z = z.to(dtype=vae_dtype)
                return _old_decode(z, *a, **kw)

            vae.decode = _decode
    except Exception:
        logger.exception("vae_decode_patch_failed")

    _pipe = pipe
    return _pipe


def get_pipeline_with_ip() -> Any:
    """
    Loads IP-Adapter and returns pipeline.
    Disables slicing on self.unet during load.
    """
    global _ip_ready, _pipe
    pipe = get_pipeline()
    if _ip_ready:
        return pipe

    try:
        if hasattr(pipe, "disable_attention_slicing"):
            pipe.disable_attention_slicing()
        try:
            pipe.unet.set_attn_processor(AttnProcessor2_0())
        except Exception:
            pipe.unet.set_attn_processor(AttnProcessor())
    except Exception as exc:
        logger.debug(f"ip_adapter_attention_prep_failed: {exc}")

    ip_dir = getattr(settings, "ip_adapter_dir", None)
    if not ip_dir:
        lg("app").bind(event="ip_adapter.disabled", reason="no_ip_adapter_dir").warning("ip_adapter.disabled")
        return pipe

    plus = os.path.join(ip_dir, "ip-adapter-plus_sd15.safetensors")
    base = os.path.join(ip_dir, "ip-adapter_sd15.safetensors")
    if _is_offline() and not (os.path.exists(plus) or os.path.exists(base)):
        lg("app").bind(event="ip_adapter.disabled", reason="weights_missing", dir=ip_dir).warning("ip_adapter.disabled")
        return pipe

    try:
        pipe.load_ip_adapter(
            ip_dir,
            subfolder="",
            weight_name="ip-adapter-plus_sd15.safetensors",
            image_encoder_folder="image_encoder",
        )
    except Exception:
        try:
            pipe.load_ip_adapter(
                ip_dir,
                subfolder="",
                weight_name="ip-adapter_sd15.safetensors",
                image_encoder_folder="image_encoder",
            )
        except Exception as e:
            lg("app").bind(event="ip_adapter.disabled", reason=str(e)).warning("ip_adapter.disabled")
            return pipe

    _align_ip_encoders(pipe)
    _move_ip_encoders_to_cpu(pipe)
    _align_ipadapter_long_buffers_to_unet_device(pipe)

    # Synchronize dtype across all UNet layers (including newly added IP-Adapter layers)
    try:
        _unet_dtype = next(pipe.unet.parameters()).dtype
        pipe.unet.to(dtype=_unet_dtype)
    except Exception as e:
        logger.warning(f"UNet dtype sync failed: {e}")

    try:
        dev = next(pipe.unet.parameters()).device

        if hasattr(pipe, "text_encoder") and pipe.text_encoder is not None:
            pipe.text_encoder.to(dev)

        if hasattr(pipe, "image_encoder") and pipe.image_encoder is not None:
            pipe.image_encoder.to(device="cpu", dtype=torch.float32)
    except Exception:
        logger.exception("post_ip_adapter_device_sync_failed")

    lg("app").bind(
        event="ip_adapter.loaded",
        model_id=settings.model_id,
        device=str(dev),
    ).info("ip_adapter.loaded")

    _ip_ready = True
    return pipe
