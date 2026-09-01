import os, torch
from huggingface_hub import snapshot_download
from diffusers import StableDiffusionPipeline, AutoencoderKL  # type: ignore

snapshot_download("openai/clip-vit-large-patch14", local_files_only=False)
vae_id = os.getenv("VAE_ID", "stabilityai/sd-vae-ft-mse")
snapshot_download(vae_id, local_files_only=False)

model_id = os.getenv("MODEL_ID", "models/dreamshaper_6NoVae.safetensors")
dtype = torch.float16 if os.getenv("TORCH_DTYPE", "fp16") == "fp16" else torch.bfloat16
device = "cuda" if torch.cuda.is_available() else "cpu"

if model_id.endswith(".safetensors"):
    pipe = StableDiffusionPipeline.from_single_file(model_id, torch_dtype=dtype, use_safetensors=True)
else:
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)

if vae_id:
    vae = AutoencoderKL.from_pretrained(vae_id, torch_dtype=dtype)
    pipe.vae = vae

pipe = pipe.to(device)
with torch.inference_mode():
    img = pipe("warmup", num_inference_steps=6, guidance_scale=3.5, width=512, height=512).images[0]

out_dir = os.getenv("OUTPUTS_DIR", "outputs")
os.makedirs(out_dir, exist_ok=True)
img.save(os.path.join(out_dir, "warm_cache.png"))
print("OK: warm_cache.png")
