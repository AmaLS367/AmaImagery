from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import StableDiffusionPipeline
from diffusers.pipelines.auto_pipeline import AutoPipelineForText2Image 
from diffusers.models.autoencoders.autoencoder_kl import AutoencoderKL 
from diffusers.models.attention_processor import AttnProcessor2_0, AttnProcessor 
from diffusers import DPMSolverMultistepScheduler # type: ignore
from huggingface_hub import snapshot_download

from app.config import settings
from loguru import logger
from app.core.logging import lg

import os
import torch
from pathlib import Path

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

_pipe = None
_ip_ready = False

# --- dtype alignment helpers ---
def get_unet_dtype(pipe) -> torch.dtype:
    try:
        return next(pipe.unet.parameters()).dtype
    except Exception:
        return torch.float16 if getattr(pipe, "device", None) and getattr(pipe.device, "type", "") == "cuda" else torch.float32

def align_to_unet_dtype(tensor: torch.Tensor, pipe) -> torch.Tensor:
    try:
        return tensor.to(dtype=get_unet_dtype(pipe), device=pipe.device)
    except Exception:
        return tensor


# --- online/offline switch & cache helpers ---
def _flag(name: str) -> bool:
    return os.getenv(name, "0").strip().lower() in ("1", "true", "yes", "on")

def _is_offline() -> bool:
    return _flag("HF_HUB_OFFLINE") or _flag("TRANSFORMERS_OFFLINE") or _flag("DIFFUSERS_OFFLINE") or _flag("NO_NETWORK")

def _project_root() -> Path:
    # from app/inference/pipeline.py -> project root
    return Path(__file__).resolve().parents[2]

def _hub_candidates() -> list[Path]:
    # Priority: explicit env -> HF_HOME/hub -> project cache -> CWD cache -> user home
    c: list[Path] = []
    env_hub = os.getenv("HUGGINGFACE_HUB_CACHE")
    if env_hub:
        c.append(Path(env_hub))
    hf_home = os.getenv("HF_HOME")
    if hf_home:
        c.append(Path(hf_home) / "hub")
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
    snapshot_download(repo, local_files_only=False)
    snap = _find_snapshot(repo)
    if not snap:
        raise RuntimeError(f"Snapshot '{repo}' not found after download")
    return snap

def _align_ip_encoders(pipe):
    dev = next(pipe.unet.parameters()).device
    dt  = next(pipe.unet.parameters()).dtype

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
                setattr(a, "image_encoder", enc2.to(device=dev, dtype=dt))
            except Exception:
                setattr(a, "image_encoder", enc2.to(device=dev))


def _move_ip_encoders_to_cpu(pipe):
    # Глобальный image_encoder → CPU FP32
    enc = getattr(pipe, "image_encoder", None)
    if enc is not None:
        try:
            pipe.image_encoder = enc.to(device="cpu", dtype=torch.float32)
        except Exception:
            pipe.image_encoder = enc.to(device="cpu")
    # Вложенные encoders внутри ip_adapter → CPU FP32
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
                setattr(a, "image_encoder", enc2.to(device="cpu", dtype=torch.float32))
            except Exception:
                setattr(a, "image_encoder", enc2.to(device="cpu"))

def _align_ipadapter_long_buffers_to_unet_device(pipe):
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
        # пройтись по всем вложенным буферам
        for name, buf in a.named_buffers(recurse=True):
            if buf is None:
                continue
            # image_encoder буферы пропускаем (он должен остаться на CPU)
            if name.startswith("image_encoder") or "image_encoder" in name:
                continue
            # переносим только если устройство отличается
            if buf.device != dev:
                try:
                    # двигаем буфер на device UNet; dtype сохраняем
                    a._buffers[name] = buf.to(dev)
                except Exception:
                    # если буфер заморожен/неперсистентен — пробуем заменить через register_buffer
                    try:
                        a.register_buffer(name, buf.to(dev), persistent=False)
                    except Exception:
                        pass


def get_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe

    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    want_cuda = str(getattr(settings, "device", "cuda")).lower() != "cpu"
    device = "cuda" if (torch.cuda.is_available() and want_cuda) else "cpu"
    _dtype_map = {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}
    dtype = _dtype_map.get(getattr(settings, "torch_dtype", "fp16").lower(), torch.float16)

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
                vae = AutoencoderKL.from_pretrained(
                    str(Path(vid)), 
                    torch_dtype=dtype, 
                    local_files_only=True
                )
            else:
                local_vae_dir = _pick_local_vae_dir(sd15_cfg)
                if not local_vae_dir:
                    raise RuntimeError("Offline mode: no local VAE found (VAE_ID path missing, models/vae missing, SD1.5 VAE missing)")
                vae = AutoencoderKL.from_pretrained(
                    str(local_vae_dir), 
                    torch_dtype=dtype, 
                    local_files_only=True
                )
        else:
            # ONLINE: local dir wins; otherwise treat VAE_ID as repo id and fetch/cache
            if vid and Path(vid).exists():
                vae = AutoencoderKL.from_pretrained(
                    str(Path(vid)), 
                    torch_dtype=dtype, 
                    local_files_only=True
                )
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
                    vae = AutoencoderKL.from_pretrained(
                        str(vae_dir), 
                        torch_dtype=dtype, 
                        local_files_only=False
                    )

        sd15_cfg = _ensure_snapshot("runwayml/stable-diffusion-v1-5", offline)
        cfg_dir = Path(sd15_cfg)  
        mi = cfg_dir / "model_index.json"
        if not mi.exists():
            raise RuntimeError(f"SD1.5 config repo is invalid: missing {mi}")

        pipe = StableDiffusionPipeline.from_single_file(
            mid,
            config=str(cfg_dir),  
            torch_dtype=dtype,
            vae=vae,
            use_safetensors=True,
            safety_checker=None,
            feature_extractor=None,
            local_files_only=offline,
        )

    else:
        # 2) HF-репозиторий или локальная папка с model_index.json
        if offline and not os.path.exists(mid):
            raise RuntimeError("OFFLINE и model_id не локальный путь")
        pipe = AutoPipelineForText2Image.from_pretrained(
            mid,
            torch_dtype=dtype,
            use_safetensors=True,
            local_files_only=offline,  
        )

    # --- шедулер: заменяем на DPMSolver++ (Karras, 2nd order) ---
    try:
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config,
            algorithm_type="sde-dpmsolver++",
            use_karras_sigmas=True,
            solver_order=2,
        )
    except Exception:
        pass

    # --- экономия памяти ---
    pipe.unet.set_attn_processor(AttnProcessor2_0())
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    pipe.enable_vae_tiling()
    pipe.enable_xformers_memory_efficient_attention()

    pipe.set_progress_bar_config(disable=True)

    if device == "cuda":
        pipe.unet.to(memory_format=torch.channels_last)
        
    # лог: базовая модель загружена и сконфигурирована
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

        # базовый dtype всего пайпа: fp16 на CUDA, иначе fp32
        pipe.to(device=dev, dtype=dtype)

        # UNet/VAE строго в dtype пайпа
        if getattr(pipe, "unet", None) is not None:
            pipe.unet.to(device=dev, dtype=dtype)
        if getattr(pipe, "vae", None) is not None:
            pipe.vae.to(device=dev, dtype=dtype)

        # text_encoder оставляем FP32 (на том же девайсе), image_encoder — всегда CPU/FP32
        if getattr(pipe, "text_encoder", None) is not None:
            pipe.text_encoder.to(device=dev, dtype=torch.float32)
        if getattr(pipe, "image_encoder", None) is not None:
            pipe.image_encoder.to(device="cpu", dtype=torch.float32)
        
    except Exception:
        logger.exception("device_sync_failed")
    # --- end: force device sync ---
    
    # --- единый патч: синхронизируем dtype для sample/timestep и входа time_embedding ---
    try:
        unet = pipe.unet
        unet_dtype = next(unet.parameters()).dtype

        _old_unet_forward = unet.forward
        def _unet_forward(sample, timestep, *args, **kwargs):
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
        
    # --- П4: time_embedding.forward -> привести вход к dtype весов TE ---
    try:
        _unet2 = getattr(pipe, "unet", None)
        te = getattr(_unet2, "time_embedding", None)
        if te is not None and hasattr(te, "linear_1"):
            _old_te_forward = te.forward
            te_w_dtype = te.linear_1.weight.dtype
            def _te_forward(x, *a, **kw):
                if isinstance(x, torch.Tensor) and x.dtype != te_w_dtype:
                    x = x.to(dtype=te_w_dtype)
                return _old_te_forward(x, *a, **kw)
            te.forward = _te_forward
    except Exception:
        logger.exception("time_embedding_patch_failed")

    # --- П5: VAE.decode -> привести z к dtype VAE перед post_quant_conv ---
    try:
        vae = getattr(pipe, "vae", None)
        if vae is not None:
            vae_dtype = next(vae.parameters()).dtype
            _old_decode = vae.decode
            def _decode(z, *a, **kw):
                if isinstance(z, torch.Tensor) and z.dtype != vae_dtype:
                    z = z.to(dtype=vae_dtype)
                return _old_decode(z, *a, **kw)
            vae.decode = _decode
    except Exception:
        logger.exception("vae_decode_patch_failed")


    _pipe = pipe
    return _pipe

def get_pipeline_with_ip():
    """
    Загружает IP-Adapter и возвращает пайп.
    На время загрузки выключаем slicing у self.unet.
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
    except Exception:
        pass

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
    
    # Синхронизация dtype всех слоёв UNet (включая добавленные IP-Adapter)
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


