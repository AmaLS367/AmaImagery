from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import StableDiffusionPipeline # type: ignore
from diffusers.pipelines.auto_pipeline import AutoPipelineForText2Image # type: ignore
from diffusers.models.autoencoders.autoencoder_kl import AutoencoderKL # type: ignore
from diffusers.schedulers.scheduling_euler_ancestral_discrete import EulerAncestralDiscreteScheduler # type: ignore
from diffusers.schedulers.scheduling_dpmsolver_multistep import DPMSolverMultistepScheduler  # type: ignore
from diffusers.models.attention_processor import AttnProcessor2_0, AttnProcessor # type: ignore 

from app.config import settings
from loguru import logger
from app.logging_setup import lg

import os
import torch

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

_pipe = None
_ip_ready = False

def get_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe

    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    want_cuda = str(getattr(settings, "device", "cuda")).lower() != "cpu"
    device = "cuda" if (torch.cuda.is_available() and want_cuda) else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    mid = settings.model_id

    # 1) DreamShaper .safetensors (локальный файл)
    if os.path.isfile(mid) and mid.lower().endswith((".safetensors", ".ckpt")):
        vae = None
        if getattr(settings, "vae_id", None):
            vae = AutoencoderKL.from_pretrained(settings.vae_id, torch_dtype=dtype, local_files_only=True)

        pipe = StableDiffusionPipeline.from_single_file(
            mid,
            torch_dtype=dtype,
            vae=vae,                   # у версии "no vae" может быть None — это норм
            use_safetensors=True,
            safety_checker=None,       # не подтягиваем safety_checker
            feature_extractor=None,
        )
    else:
        # 2) HF-репозиторий или локальная папка с model_index.json
        if settings.no_network and not os.path.exists(mid):
            raise RuntimeError("NO_NETWORK=1 и model_id не локальный путь")
        pipe = AutoPipelineForText2Image.from_pretrained(
            mid, torch_dtype=dtype, use_safetensors=True, local_files_only=True
        )

    # --- шедулер: заменяем на Euler Ancestral (CFG > 3 работает корректно) ---
    try:
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras=True)
    except Exception:
        pass

    # --- экономия памяти ---
    try:
        pipe.unet.set_attn_processor(AttnProcessor2_0())
    except Exception:
        pass
    try:
        pipe.enable_attention_slicing()
    except Exception:
        pass
    try:
        pipe.enable_vae_slicing()
    except Exception:
        pass
    try:
        pipe.enable_vae_tiling()
    except Exception:
        pass
    try:
        pipe.enable_xformers_memory_efficient_attention()
    except Exception:
        pass


    vae = getattr(pipe, "vae", None)

    pipe.set_progress_bar_config(disable=True)

    pipe = pipe.to(device)
    if device == "cuda":
        pipe.unet.to(memory_format=torch.channels_last)

    try:
        pipe.enable_attention_slicing()
    except Exception:
        pass
    try:
        pipe.enable_vae_slicing()
    except Exception:
        pass
    try:
        pipe.enable_xformers_memory_efficient_attention()
    except Exception:
        pass
    try:
        from accelerate import cpu_offload
        if device == "cuda":
            pipe.enable_model_cpu_offload()
    except Exception:
        pass
        
    # лог: базовая модель загружена и сконфигурирована
    lg("app").bind(
        event="model.loaded",
        model_id=settings.model_id,
        device=device,
        torch_version=getattr(torch, "__version__", "unknown"),
        diffusers_version=getattr(__import__("diffusers"), "__version__", "unknown"),
    ).info("model.loaded")

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

    # временно убрать SlicedAttnProcessor на время загрузки
    try:
        if hasattr(pipe, "disable_attention_slicing"):
            pipe.disable_attention_slicing()
        try:
            pipe.unet.set_attn_processor(AttnProcessor2_0()) 
        except Exception:
            pipe.unet.set_attn_processor(AttnProcessor())
    except Exception:
        pass


    # загрузка IP-Adapter (SD1.5 веса)
    ip_dir = getattr(settings, "ip_adapter_dir", None)
    if not ip_dir:
        raise RuntimeError("IP-Adapter не задан: IP_ADAPTER_DIR должен указывать на папку с .safetensors")

    import os
    plus = os.path.join(ip_dir, "ip-adapter-plus_sd15.safetensors")
    base = os.path.join(ip_dir, "ip-adapter_sd15.safetensors")
    if settings.no_network and not (os.path.exists(plus) or os.path.exists(base)):
        raise RuntimeError("NO_NETWORK=1, но веса IP-Adapter не найдены в IP_ADAPTER_DIR")

    try:
        pipe.load_ip_adapter(
            ip_dir,
            subfolder="",
            weight_name="ip-adapter-plus_sd15.safetensors",
        )
    except Exception:
        pipe.load_ip_adapter(
            ip_dir,
            subfolder="",
            weight_name="ip-adapter_sd15.safetensors",
        )

    # энкодер изображения держим на CPU
    image_encoder = getattr(pipe, "image_encoder", None)
    if image_encoder is not None:
        if str(next(pipe.unet.parameters()).device).startswith("cuda"):
            pipe.image_encoder = image_encoder.to("cpu")
        else:
            pipe.image_encoder = image_encoder
        
    # лог: IP-Adapter подключен
    lg("app").bind(
        event="ip_adapter.loaded",
        model_id=settings.model_id,
        device=str(settings.device),
    ).info("ip_adapter.loaded")


    # вернуть экономию памяти после загрузки IP-Adapter
    try:
        pipe.enable_attention_slicing()
    except Exception:
        pass
    try:
        pipe.enable_vae_slicing()
    except Exception:
        pass
    try:
        pipe.enable_vae_tiling()
    except Exception:
        pass
    try:
        pipe.enable_xformers_memory_efficient_attention()
    except Exception:
        pass

    _ip_ready = True
    return pipe


