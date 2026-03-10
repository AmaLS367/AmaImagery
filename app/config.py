from typing import Annotated, Literal, Optional, List, Dict, Any
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Core / Environment ---
    env: Annotated[Literal["dev", "development", "local", "stage", "staging", "prod", "production"], Field(alias="ENV")] = "dev"
    run_in_docker: Annotated[bool, Field(alias="RUN_IN_DOCKER")] = False
    debug: Annotated[bool, Field(alias="DEBUG")] = False
    
    # --- Network ---
    no_network: Annotated[bool, Field(alias="NO_NETWORK")] = True 

    # --- Providers ---
    providers_default_name: Annotated[str, Field(alias="PROVIDERS_DEFAULT_NAME")] = "diffusers"
    providers_enabled: Annotated[List[str], Field(alias="PROVIDERS_ENABLED")] = ["diffusers"]
    comfyui_base_url: Annotated[Optional[str], Field(alias="COMFYUI_BASE_URL")] = None
    comfyui_websocket_url: Annotated[Optional[str], Field(alias="COMFYUI_WEBSOCKET_URL")] = None
    comfyui_workflow_path: Annotated[Optional[Path], Field(alias="COMFYUI_WORKFLOW_PATH")] = None
    comfyui_workflow_map_path: Annotated[Optional[Path], Field(alias="COMFYUI_WORKFLOW_MAP_PATH")] = None
    comfyui_poll_interval_sec: Annotated[float, Field(alias="COMFYUI_POLL_INTERVAL_SEC")] = 1.5
    comfyui_timeout_sec: Annotated[int, Field(alias="COMFYUI_TIMEOUT_SEC")] = 300
    
    # --- Feature Flags ---
    feature_flags: Annotated[Dict[str, bool], Field(alias="FEATURE_FLAGS")] = {
        "image_generation": True,
        "image_editing": True,
        "image_upscaling": True,
        "ip_adapter": True,
        "batch_generation": True,
    }
    
    # --- Inference/model ---
    model_id: Annotated[str, Field(alias="MODEL_ID")] = "models/dreamshaper_6NoVae.safetensors"
    device: Annotated[str, Field(alias="DEVICE")] = "cuda"
    max_steps: Annotated[int, Field(alias="MAX_STEPS")] = 128
    max_size: Annotated[int, Field(alias="MAX_SIZE")] = 2048
    generation_timeout_sec: Annotated[int, Field(alias="GENERATION_TIMEOUT_SEC")] = 300
    vae_id: Annotated[Optional[str], Field(alias="VAE_ID")] = None
    torch_dtype: Annotated[str, Field(alias="TORCH_DTYPE")] = "fp16"  # fp16|bf16|fp32
    scheduler: Annotated[Optional[str], Field(alias="SCHEDULER")] = None
    seed_strict: Annotated[bool, Field(alias="SEED_STRICT")] = False

    # --- Database ---
    database_url: Annotated[str, Field(alias="DATABASE_URL")] = "postgresql+asyncpg://postgres:postgres@localhost:5432/amaimagery"
    
    # --- Security ---
    secret_key: Annotated[str, Field(alias="SECRET_KEY")] = ""
    jwt_alg: Annotated[str, Field(alias="JWT_ALG")] = "HS256"
    
    # --- Logging ---
    log_dir: Annotated[str, Field(alias="LOG_DIR")] = "logs"
    log_level: Annotated[str, Field(alias="LOG_LEVEL")] = "INFO"                  # DEBUG/INFO/WARNING/ERROR
    log_rotation: Annotated[str, Field(alias="LOG_ROTATION")] = "00:00"           # daily rotation
    log_retention: Annotated[str, Field(alias="LOG_RETENTION")] = "30 days"
    log_compression: Annotated[str, Field(alias="LOG_COMPRESSION")] = "zip"
    prompts_raw: Annotated[int, Field(alias="PROMPTS_RAW")] = 0  
    log_mask_auth: Annotated[bool, Field(alias="LOG_MASK_AUTH")] = True

    # SMTP
    smtp_host: Annotated[str, Field(alias='SMTP_HOST')] = 'localhost'
    smtp_port: Annotated[int, Field(alias='SMTP_PORT')] = 1025
    smtp_user: Annotated[Optional[str], Field(alias='SMTP_USER')] = None
    smtp_pass: Annotated[Optional[str], Field(alias='SMTP_PASS')] = None
    smtp_from: Annotated[str, Field(alias='SMTP_FROM')] = 'no-reply@example.com'
    smtp_security: Annotated[str, Field(alias='SMTP_SECURITY')] = 'starttls'  # ssl | starttls | none
    smtp_timeout_sec: Annotated[int, Field(alias='SMTP_TIMEOUT_SEC')] = 15
    
    # --- General toggles ---
    autocorrect: Annotated[bool, Field(alias="AUTOCORRECT")] = False
    base_url: Annotated[Optional[str], Field(alias="BASE_URL")] = None

    # Links in emails
    frontend_origin: Annotated[str, Field(alias='FRONTEND_ORIGIN')] = 'http://localhost:5173'

    # TTL for password reset tokens (minutes)
    reset_token_ttl_min: Annotated[int, Field(alias='RESET_TOKEN_TTL_MIN')] = 30
    
    # allowed hosts
    allowed_hosts: Annotated[List[str], Field(alias='ALLOWED_HOSTS')] = ["localhost", "127.0.0.1"]

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def _parse_hosts(cls, v: Any) -> List[str] | Any:
        if v is None or v == "":
            return ["localhost", "127.0.0.1"]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    data = json.loads(s)
                    return [str(x).strip() for x in data if str(x).strip()]
                except Exception:
                    pass
            parts = s.replace(";", ",").split(",")
            return [p.strip() for p in parts if p.strip()]
        return v

    # --- Redis (for rate-limits, queues, etc) ---
    redis_url: Annotated[str, Field(alias='REDIS_URL')] = "redis://localhost:6379/0"
    no_redis: Annotated[bool, Field(alias='NO_REDIS')] = False  # Disable Redis (for dev/testing)
    enable_hsts: Annotated[bool, Field(alias='ENABLE_HSTS')] = False

    # Limits
    gen_per_user_per_min: Annotated[int, Field(alias="GEN_PER_USER_PER_MIN")] = 60
    gen_per_ip_per_min: Annotated[int, Field(alias="GEN_PER_IP_PER_MIN")] = 120
    limits_enabled: Annotated[bool, Field(alias="LIMITS_ENABLED")] = True

    # Concurrency
    queue_wait_timeout_sec: Annotated[float, Field(alias="QUEUE_WAIT_TIMEOUT_SEC")] = 2.0

    # --- Files ---
    file_signing_enabled: Annotated[bool, Field(alias="FILE_SIGNING_ENABLED")] = True
    file_url_ttl_sec: Annotated[int, Field(alias="FILE_URL_TTL_SEC")] = 86400
    file_download_ttl_sec: Annotated[int, Field(alias="FILE_DOWNLOAD_TTL_SEC")] = 900  # ≤ 15 min
    file_single_use: Annotated[bool, Field(alias="FILE_SINGLE_USE")] = False
    file_allowed_exts: Annotated[List[str], Field(alias="FILE_ALLOWED_EXTS")] = ["png", "jpg", "jpeg", "webp"]
    file_allowed_mimes: Annotated[List[str], Field(alias="FILE_ALLOWED_MIMES")] = ["image/png", "image/jpeg", "image/webp"]
    
    @field_validator("file_allowed_exts", "file_allowed_mimes", "providers_enabled", mode="before")
    @classmethod
    def _parse_list_env(cls, v: Any) -> List[str] | None:
        if v is None:
            return None
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
        s = str(v).strip()
        if s == "":
            return None
        if s.startswith("["):
            try:
                data = json.loads(s)
                return [str(x).strip() for x in data if str(x).strip()]
            except Exception:
                pass
        return [p.strip() for p in re.split(r"[;,]", s) if p.strip()]
    
    @field_validator("feature_flags", mode="before")
    @classmethod
    def _parse_feature_flags(cls, v: Any) -> Dict[str, bool] | None:
        if v is None:
            return None
        if isinstance(v, dict):
            return {str(k): bool(v) for k, v in v.items()}
        s = str(v).strip()
        if s == "":
            return None
        if s.startswith("{") or s.startswith("["):
            try:
                data = json.loads(s)
                if isinstance(data, dict):
                    return {str(k): bool(v) for k, v in data.items()}
                if isinstance(data, list):
                    return {str(item): True for item in data}
            except Exception:
                pass
        flags = {}
        for part in re.split(r"[;,]", s):
            part = part.strip()
            if not part:
                continue
            if "=" in part:
                k, v = part.split("=", 1)
                flags[k.strip()] = v.strip().lower() in ("true", "1", "yes", "on")
            else:
                flags[part] = True
        return flags

    # --- Auth: JWT, tokens, bcrypt ---
    access_ttl_min: Annotated[int, Field(alias="ACCESS_TTL_MIN")] = 15
    revoke_prefix: Annotated[str, Field(alias="REVOKE_PREFIX")] = "jwt:bl:"

    # --- NSFW ---
    nsfw_allow: Annotated[bool, Field(alias="NSFW_ALLOW")] = False
    nsfw_blocklist_path: Annotated[Path, Field(alias="NSFW_BLOCKLIST_PATH")] = Path("app/config/nsfw_blocklist.txt")
    
    # --- Auth: cookies, bcrypt ---
    refresh_cookie_name: Annotated[str, Field(alias="REFRESH_COOKIE_NAME")] = "refresh_token"
    refresh_ttl_days: Annotated[int, Field(alias="REFRESH_TTL_DAYS")] = 14
    refresh_cookie_secure: Annotated[bool, Field(alias="REFRESH_COOKIE_SECURE")] = True  # prod=True
    bcrypt_rounds: Annotated[int, Field(alias="BCRYPT_ROUNDS")] = 12

    # --- API limits/timeouts ---
    max_body_bytes: Annotated[int, Field(alias="MAX_BODY_BYTES")] = 25 * 1024 * 1024  # 25 MB
    max_query_value_len: Annotated[int, Field(alias="MAX_QUERY_VALUE_LEN")] = 512
    request_timeout_seconds: Annotated[int, Field(alias="REQUEST_TIMEOUT_SECONDS")] = 30 # General request timeout
    keepalive_timeout_seconds: Annotated[int, Field(alias="KEEPALIVE_TIMEOUT_SECONDS")] = 5  # uvicorn keep-alive
    
    # --- Hugging Face and offline caches ---
    hf_hub_offline: Annotated[bool, Field(alias="HF_HUB_OFFLINE")] = False
    transformers_offline: Annotated[bool, Field(alias="TRANSFORMERS_OFFLINE")] = False
    diffusers_offline: Annotated[bool, Field(alias="DIFFUSERS_OFFLINE")] = False
    hf_home: Annotated[Optional[Path], Field(alias="HF_HOME")] = None
    huggingface_hub_cache: Annotated[Optional[Path], Field(alias="HUGGINGFACE_HUB_CACHE")] = None
    transformers_cache: Annotated[Optional[Path], Field(alias="TRANSFORMERS_CACHE")] = None
    hf_token: Annotated[Optional[str], Field(alias="HF_TOKEN")] = None

    # --- Anti-DoS: generation ---
    max_concurrent_generations: Annotated[int, Field(alias="MAX_CONCURRENT_GENERATIONS")] = 2
    
    @property
    def generation_timeout_seconds(self) -> int:
        return int(self.generation_timeout_sec)

    # --- Inference: security ---
    max_gen_width: Annotated[int, Field(alias="MAX_GEN_WIDTH")] = 1024
    max_gen_height: Annotated[int, Field(alias="MAX_GEN_HEIGHT")] = 1024
    max_gen_steps: Annotated[int, Field(alias="MAX_GEN_STEPS")] = 128
    max_guidance: Annotated[float, Field(alias="MAX_GUIDANCE")] = 20.0
    max_batch: Annotated[int, Field(alias="MAX_BATCH")] = 4

    # --- Torch resourses ---
    torch_threads: Annotated[int, Field(alias="TORCH_THREADS")] = 2                # CPU threads
    cuda_vram_fraction: Annotated[float, Field(alias="CUDA_VRAM_FRACTION")] = 0.95

    # --- Metrics --
    metrics_enabled: Annotated[bool, Field(alias="METRICS_ENABLED")] = True
    gpu_metrics_enabled: Annotated[bool, Field(alias="GPU_METRICS_ENABLED")] = True
    metrics_path: Annotated[str, Field(alias="METRICS_PATH")] = "/metrics"
    
    # --- Docs and UI ---
    docs_url: Annotated[Optional[str], Field(alias="DOCS_URL")] = "/docs"
    ui_static_dir: Annotated[Optional[Path], Field(alias="UI_STATIC_DIR")] = None

    # --- Paths ---
    root_dir: Annotated[Path, Field(alias="ROOT_DIR")] = Path(__file__).resolve().parents[1]
    outputs_dir: Annotated[Path, Field(alias="OUTPUTS_DIR")] = Path(__file__).resolve().parents[1] / "outputs"
    ip_adapter_dir: Annotated[Optional[Path], Field(alias="IP_ADAPTER_DIR", validation_alias="IP_ADAPTER_DIR")] = None
    ip_image_encoder_path: Annotated[Optional[Path], Field(alias="IP_IMAGE_ENCODER_PATH", validation_alias="IP_IMAGE_ENCODER_PATH")] = None

    # --- Validators --- 
    @field_validator("device", mode="before")
    @classmethod
    def _norm_device(cls, v: Any) -> str:
        s = (str(v) if v is not None else "cuda").strip().lower()
        return "cuda" if s not in ("cpu", "cuda") else s

    @field_validator(
        "run_in_docker",
        "debug",
        "no_network",
        "no_redis",
        "enable_hsts",
        "limits_enabled",
        "file_signing_enabled",
        "file_single_use",
        "nsfw_allow",
        "refresh_cookie_secure",
        "hf_hub_offline",
        "transformers_offline",
        "diffusers_offline",
        "metrics_enabled",
        "gpu_metrics_enabled",
        mode="before",
    )
    @classmethod
    def _parse_boolish(cls, v: Any) -> Any:
        if isinstance(v, bool) or v is None:
            return v
        s = str(v).strip().lower()
        if s in {"1", "true", "yes", "on", "debug", "development", "dev"}:
            return True
        if s in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return v
    
    @field_validator("torch_dtype", mode="before")
    @classmethod
    def _norm_dtype(cls, v: Any) -> str:
        s = str(v or "fp16").lower().strip()
        if s not in ("fp16", "bf16", "fp32"):
            raise ValueError("TORCH_DTYPE must be fp16|bf16|fp32")
        return s

    @field_validator("hf_token", "hf_home", "transformers_cache", "base_url", mode="before")
    @classmethod
    def _empty_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    
    @field_validator(
        "outputs_dir",
        "hf_home",
        "huggingface_hub_cache",
        "transformers_cache",
        "ip_adapter_dir",
        "ip_image_encoder_path",
        "ui_static_dir",
        "nsfw_blocklist_path",
        "comfyui_workflow_path",
        "comfyui_workflow_map_path",
        mode="before",
    )
    @classmethod
    def _as_path(cls, v: Any) -> Any:
        if v is None or isinstance(v, Path):
            return v
        s = os.path.expanduser(os.path.expandvars(str(v).strip()))
        return Path(s)
    
    @model_validator(mode="after")
    def _resolve_relative_paths(self) -> "Settings":
        base = self.root_dir

        def norm_req(p: Path) -> Path:
            return p if p.is_absolute() else (base / p)

        def norm_opt(p: Path | None) -> Path | None:
            if p is None:
                return None
            return p if p.is_absolute() else (base / p)

        self.outputs_dir = norm_req(self.outputs_dir)
        self.nsfw_blocklist_path = norm_req(self.nsfw_blocklist_path)

        self.hf_home = norm_opt(self.hf_home)
        self.huggingface_hub_cache = norm_opt(self.huggingface_hub_cache)
        self.transformers_cache = norm_opt(self.transformers_cache)
        self.ip_adapter_dir = norm_opt(self.ip_adapter_dir)
        self.ip_image_encoder_path = norm_opt(self.ip_image_encoder_path)
        self.ui_static_dir = norm_opt(self.ui_static_dir)
        self.comfyui_workflow_path = norm_opt(self.comfyui_workflow_path)
        self.comfyui_workflow_map_path = norm_opt(self.comfyui_workflow_map_path)

        if self.hf_home:
            os.environ["HF_HOME"] = str(self.hf_home)
        if self.huggingface_hub_cache:
            os.environ["HUGGINGFACE_HUB_CACHE"] = str(self.huggingface_hub_cache)
        if self.transformers_cache:
            os.environ["TRANSFORMERS_CACHE"] = str(self.transformers_cache)
        return self

    # -- Config ---
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=None,
        case_sensitive=False
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() in ("prod", "production")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() in ("dev", "development", "local")

    def is_provider_enabled(self, provider_name: str) -> bool:
        return provider_name in (self.providers_enabled or [])


# === Initialization and validation ===
def _load_env_file() -> None:
    """Load .env file if not running in Docker."""
    if not os.getenv("RUN_IN_DOCKER"):
        load_dotenv(".env")


def _create_directories(settings: Settings) -> None:
    try:
        Path(settings.outputs_dir).mkdir(parents=True, exist_ok=True)
        
        for sub in ("access", "app", "generations", "prompts", "prompts/raw", "errors", "metrics"):
            Path(settings.log_dir, sub).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # In read-only environments (like some K8s pods), we can't create dirs.
        # This is fine as long as we log to stdout/stderr.
        pass
    except Exception as e:
        print(f"Warning: Failed to create directories: {e}")


def _validate_production_settings(settings: Settings) -> None:
    """Validate critical settings for production environment."""
    if not settings.is_production:
        return  # Skip validation in dev/staging
    
    # Validate SECRET_KEY
    if not settings.secret_key or settings.secret_key in {"CHANGE_ME", "CHANGE_ME_LONG_RANDOM"}:
        raise RuntimeError(
            "SECRET_KEY must be set to a secure value in production. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
        )
    
    # Validate DATABASE_URL for production
    db_url = urlparse(settings.database_url)
    if db_url.scheme == "sqlite":
        raise RuntimeError(
            "SQLite is not supported in production. Set DATABASE_URL to PostgreSQL."
        )
    
    if db_url.scheme.startswith("postgresql"):
        if not db_url.password or len(db_url.password) < 12:
            raise RuntimeError(
                "DATABASE_URL must include a strong password (12+ characters) in production."
            )
    
    # Validate REDIS_URL for production
    if not settings.no_redis:
        redis_url = urlparse(settings.redis_url)
        if redis_url.scheme.startswith("redis"):
            if not redis_url.password or redis_url.password.strip() == "":
                raise RuntimeError(
                    "REDIS_URL must include a password in production (redis://:password@host:port/db)."
                )


def initialize_config() -> Settings:
    _load_env_file()
    settings = Settings()
    _create_directories(settings)
    _validate_production_settings(settings)
    return settings


# Create settings instance 
_load_env_file()
settings: Settings = Settings()
_create_directories(settings)
_validate_production_settings(settings)
