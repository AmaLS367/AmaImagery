from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.schemas import GenReq, GenResp
from app.safety import is_blocked
from app.utils import prompt_hash, out_path
from app.inference.pipeline import get_pipeline, get_pipeline_with_ip

from app.utils_01.spell import build_spell, correct_prompt
from app.logging_setup import setup_logging, AccessLogMiddleware, install_exception_handlers, lg, new_gen_id, save_prompt_raw
from app.config import settings

from contextlib import nullcontext
from PIL import Image, ImageOps
from pydantic import BaseModel
from pathlib import Path

import torch
import os
import base64
import io
import time 

setup_logging()
app = FastAPI(title="NSFW Image Generator", version="0.2.0")
app.add_middleware(AccessLogMiddleware)
install_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000","http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    "/ui",
    StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "frontend"), html=True),
    name="ui",
)

AUTOCORRECT_MODE = os.getenv("AUTOCORRECT", "on")  # on | warn | off
SPELL = build_spell(extra_words=[
    "bokeh","karras","euler","dpmsolver","lora","vae",
    "anime","photorealistic","cinematic","volumetric",
])
WHITELIST = {"sd15","sdxl","lcm","lora","vae"}  # не исправлять эти токены

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")

class UpReq(BaseModel):
    path: str
    steps: int = 4
    noise_level: int = 20
    seed: int | None = None

# @app.post("/upscale")
# def upscale(req: UpReq):
#     up = get_upscaler()
#     img = Image.open(req.path).convert("RGB")
#     gen = torch.Generator(device=str(up.device))
#     if req.seed is not None:
#         gen = gen.manual_seed(req.seed)
#     with torch.inference_mode():
#         out = up(
#             prompt="", image=img,
#             num_inference_steps=req.steps,
#             guidance_scale=0.0,
#             noise_level=req.noise_level,
#             generator=gen,
#         )
#         out_img = out.images[0]
#     new_path = req.path.replace(".png", "_x2.png")
#     out_img.save(new_path)
#     return {"ok": True, "path": new_path}

@app.get("/health")
def health():
    return {"ok": True}

# =================== Helpers ===================
def _prepare_ref_image(ref_image_b64: str, target: int = 512) -> Image.Image:
    img = Image.open(io.BytesIO(base64.b64decode(ref_image_b64.split(",")[-1]))).convert("RGB")
    # вписываем с сохранением композиции + поля (letterbox), чтобы поза/ракурс не резались
    img.thumbnail((target, target), Image.Resampling.LANCZOS)
    pad_w, pad_h = target - img.width, target - img.height
    if pad_w or pad_h:
        img = ImageOps.expand(
            img,
            border=(pad_w // 2, pad_h // 2, pad_w - pad_w // 2, pad_h - pad_h // 2),
            fill=(0, 0, 0),
        )
    return img
# =============================================

@app.post("/generate", response_model=GenResp)
def generate(req: GenReq):
    gen_logger = lg("generation")
    prompt_logger = lg("prompt")
    inference_logger = lg("generation")  # для низкоуровневых фаз
    gen_id = new_gen_id()  # сквозной ID генерации
    
    stem = prompt_hash(req.prompt, req.negative_prompt)
    
    gen_logger.bind(
        phase="requested",
        model_id=settings.model_id,
        size=[req.width, req.height],
        steps=req.steps,
        guidance_scale=req.guidance_scale,
        ip_scale=req.ip_scale,
        seed=req.seed,
    ).info("generation.requested")
    
    if is_blocked(req.prompt) or is_blocked(req.negative_prompt):
        from app.utils import prompt_hash as _ph
        stem = _ph(req.prompt, req.negative_prompt)
        lg("error").bind(
            scope="safety",
            prompt_hash=stem,
            reason="blocked_by_rules",
        ).error("safety.blocked")
        raise HTTPException(status_code=400, detail="Blocked by safety policy.")
    
    use_ip = bool(req.ref_image_b64)
    pipe = get_pipeline_with_ip() if use_ip else get_pipeline()
    exec_device = next(pipe.unet.parameters()).device
    gen = torch.Generator(device=str(exec_device)).manual_seed(int(req.seed)) if req.seed is not None else None
        
    prompt = req.prompt
    corrections = []
    if AUTOCORRECT_MODE != "off":
        fixed, corr = correct_prompt(prompt, SPELL, whitelist=WHITELIST)
        corrections = corr
        if AUTOCORRECT_MODE == "on":
            prompt = fixed

    # автокаст только для cuda
    ctx = torch.autocast("cuda", dtype=torch.float16) if exec_device.type == "cuda" else nullcontext()
    
    extra = {}
    if use_ip:
        ref_img = _prepare_ref_image(req.ref_image_b64, 512)  # нормализуем под 512
        extra["ip_adapter_image"] = ref_img

        # ip_scale: жёстко в [0..1]; дефолт 0.6
        s = 0.6 if req.ip_scale is None else float(req.ip_scale)
        s = 0.0 if s < 0.0 else (1.0 if s > 1.0 else s)
        extra["ip_adapter_scale"] = s
        
    neg = req.negative_prompt or (
    "close-up, cropped, zoomed in, out of frame, bad composition, "
    "lowres, blurry, jpeg artifacts, extra fingers, extra limbs, bad hands, worst quality, low quality"
)
    # логируем тексты промптов + исправления
    prompt_logger.bind(
        prompt_hash=stem,           # stem должен быть вычислен заранее (см. пункт C1)
        original=req.prompt,
        negative=neg,
        corrected=prompt,           # это строка после correct_prompt(...) и применения режима AUTOCORRECT
        corrections=corrections,    # список пар (исходное, исправленное) из correct_prompt(...)
    ).info("prompt.logged")
    save_prompt_raw(stem, req.prompt, neg)


    # не душим IP резкейлом CFG: убираем guidance_rescale
    # тайминг инференса + завершение/ошибка
    t0 = time.perf_counter()
    try:
        with torch.inference_mode(), ctx:
            result = pipe(
                prompt=prompt,
                negative_prompt=neg,
                num_inference_steps=req.steps,
                width=req.width,
                height=req.height,
                guidance_scale=req.guidance_scale,
                generator=gen,              
                **extra,                    
            )
            img = result.images[0]

        infer_ms = int((time.perf_counter() - t0) * 1000)

        # сохранение
        path = out_path(stem)
        img.save(path)

        # логируем успешную генерацию
        gen_logger.bind(
            phase="completed",
            prompt_hash=stem,
            total_ms=infer_ms,
            output_path=path,
            device=settings.device,
        ).success("generation.completed")

        return GenResp(ok=True, path=path, prompt_hash=stem)

    except Exception as exc:
        # логируем ошибку генерации
        lg("error").bind(
            scope="generation",
            prompt_hash=stem,
            error_type=type(exc).__name__,
        ).exception("generation.failed")
        raise


    stem = prompt_hash(req.prompt, req.negative_prompt)
    path = out_path(stem)
    img.save(path)
    return GenResp(ok=True, path=path, prompt_hash=stem)

# удобный эндпоинт для отдачи файлов
@app.get("/file")
def file(path: str):
    return FileResponse(path)
