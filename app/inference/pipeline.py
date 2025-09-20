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
from inspect import signature

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

_pipe = None
_ip_ready = False

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
    import torch
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
    """
    Переводит ВСЕ зарегистрированные буферы (особенно индексы dtype long) внутри IP-Adapter
    на device UNet. image_encoder не трогаем (он уже на CPU).
    """
    import torch
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
        
        pipe = pipe.to(device)
        if dtype is not None:
            pipe.unet.to(dtype=dtype)
            if getattr(pipe, "vae", None) is not None:
                pipe.vae.to(dtype=dtype)
            # текстовый энкодер — fp32, но на том же девайсе
            if getattr(pipe, "text_encoder", None) is not None:
                pipe.text_encoder.to(device=device, dtype=torch.float32)
        return pipe

    
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
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # чтобы encode_prompt не уносил input_ids на CPU
        setattr(pipe, "_execution_device", dev)
        
        if hasattr(pipe, "text_encoder"): pipe.text_encoder.to(dev)
        if hasattr(pipe, "image_encoder"): pipe.image_encoder.to(device="cpu", dtype=torch.float32)
        pipe.to(dev)

        if hasattr(pipe, "unet") and pipe.unet is not None:
            pipe.unet.to(dev)
        if hasattr(pipe, "vae") and pipe.vae is not None:
            pipe.vae.to(dev)
        if hasattr(pipe, "text_encoder") and pipe.text_encoder is not None:
            pipe.text_encoder.to(dev)

        # vision-энкодер (CLIP) держим на том же девайсе, но в fp32 — это безопаснее
        if hasattr(pipe, "image_encoder") and pipe.image_encoder is not None:
            pipe.image_encoder.to(device=dev, dtype=torch.float32)

        pipe.to(dev)
    except Exception:
        logger.exception("device_sync_failed")
    # --- end: force device sync ---


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
        lg("app").bind(event="ip_adapter.disabled", reason="no_ip_adapter_dir").warning("ip_adapter.disabled")
        return pipe

    plus = os.path.join(ip_dir, "ip-adapter-plus_sd15.safetensors")
    base = os.path.join(ip_dir, "ip-adapter_sd15.safetensors")
    if settings.no_network and not (os.path.exists(plus) or os.path.exists(base)):
        lg("app").bind(event="ip_adapter.disabled", reason="weights_missing", dir=ip_dir).warning("ip_adapter.disabled")
        return pipe  # без весов не подключаем

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

    try:
        dev = next(pipe.unet.parameters()).device
        setattr(pipe, "_execution_device", dev)

        if hasattr(pipe, "text_encoder") and pipe.text_encoder is not None:
            pipe.text_encoder.to(dev)

        if hasattr(pipe, "image_encoder") and pipe.image_encoder is not None:
            pipe.image_encoder.to(device="cpu", dtype=torch.float32)
    except Exception:
        logger.exception("post_ip_adapter_device_sync_failed")

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


