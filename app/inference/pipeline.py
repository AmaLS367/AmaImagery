# app/inference/pipeline.py
import os
import torch
from diffusers import ( # type: ignore 
    StableDiffusionPipeline,
    AutoPipelineForText2Image,
    AutoencoderKL,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
)  

from app.config import settings
from diffusers.models.attention_processor import AttnProcessor2_0, AttnProcessor # type: ignore 
from loguru import logger
from app.logging_setup import lg

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

_pipe = None
_ip_ready = False

def get_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe

    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    dtype = torch.float16 if settings.device == "cuda" else torch.float32

    mid = settings.model_id

    # 1) DreamShaper .safetensors (локальный файл)
    if os.path.isfile(mid) and mid.lower().endswith((".safetensors", ".ckpt")):
        vae = None
        if getattr(settings, "vae_id", None):
            vae = AutoencoderKL.from_pretrained(settings.vae_id, torch_dtype=dtype)

        pipe = StableDiffusionPipeline.from_single_file(
            mid,
            dtype=dtype,
            vae=vae,                   # у версии "no vae" может быть None — это норм
            use_safetensors=True,
            safety_checker=None,       # не подтягиваем safety_checker
            feature_extractor=None,
        )
    else:
        # 2) HF-репозиторий или локальная папка с model_index.json
        pipe = AutoPipelineForText2Image.from_pretrained(
            mid, dtype=dtype, use_safetensors=True
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
    if hasattr(pipe, "disable_attention_slicing"):
        pipe.disable_attention_slicing()


    vae = getattr(pipe, "vae", None)

    pipe.set_progress_bar_config(disable=True)

    if settings.device == "cuda":
        pipe = pipe.to("cuda")
        pipe.unet.to(memory_format=torch.channels_last)
        
    # лог: базовая модель загружена и сконфигурирована
    lg("app").bind(
        event="model.loaded",
        model_id=settings.model_id,
        device=str(settings.device),
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

    # временно убрать SlicedAttnProcessor
    try:
        if hasattr(pipe, "disable_attention_slicing"):
            pipe.disable_attention_slicing()
        try:
            pipe.unet.set_attn_processor(AttnProcessor2_0())  # torch>=2.*
        except Exception:
            pipe.unet.set_attn_processor(AttnProcessor())
    except Exception:
        pass

    # загрузка IP-Adapter (SD1.5 веса)
    try:
        pipe.load_ip_adapter(
            "h94/IP-Adapter",
            subfolder="models",
            weight_name="ip-adapter-plus_sd15.safetensors",
        )
    except Exception:
        pipe.load_ip_adapter(
            "h94/IP-Adapter",
            subfolder="models",
            weight_name="ip-adapter_sd15.safetensors",
        )


    # энкодер изображения держим на CPU
    if getattr(pipe, "image_encoder", None) is not None:
        target_device = next(pipe.unet.parameters()).device
        pipe.image_encoder = pipe.image_encoder.to(target_device)
        
    # лог: IP-Adapter подключен
    lg("app").bind(
        event="ip_adapter.loaded",
        model_id=settings.model_id,
        device=str(settings.device),
    ).info("ip_adapter.loaded")


    _ip_ready = True
    return pipe

