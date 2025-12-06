from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path
import json, os, re
from pydantic import Field, field_validator, model_validator
from typing import Literal

class Settings(BaseSettings):
    # --- Core / Environment ---
    env: Literal["dev", "development", "local", "stage", "staging", "prod", "production"] = Field("dev", alias="ENV")
    run_in_docker: bool = Field(False, alias="RUN_IN_DOCKER")
    debug: bool = Field(False, alias="DEBUG")
    
    # --- Providers ---
    providers_default_name: str = Field("diffusers", alias="PROVIDERS_DEFAULT_NAME")
    providers_enabled: list[str] = Field(
        default_factory=lambda: ["diffusers"],
        alias="PROVIDERS_ENABLED"
    )
    
    # --- Feature Flags ---
    feature_flags: dict[str, bool] = Field(
        default_factory=lambda: {
            "image_generation": True,
            "image_editing": True,
            "image_upscaling": True,
            "ip_adapter": True,
            "batch_generation": True,
        },
        alias="FEATURE_FLAGS"
    )
    
    # --- Inference/model ---
    model_id: str = Field("models/dreamshaper_6NoVae.safetensors", alias="MODEL_ID")
    device: str = Field("cuda", alias="DEVICE")
    max_steps: int = Field(128, alias="MAX_STEPS")
    max_size: int = Field(2048, alias="MAX_SIZE")
    generation_timeout_sec: int = Field(300, alias="GENERATION_TIMEOUT_SEC")
    vae_id: str | None = Field(None, alias="VAE_ID")
    torch_dtype: str = Field("fp16", alias="TORCH_DTYPE")  # fp16|bf16|fp32
    scheduler: str | None = Field(None, alias="SCHEDULER")
    seed_strict: bool = Field(False, alias="SEED_STRICT")

    # --- Database ---
    database_url: str = Field("postgresql+asyncpg://postgres:postgres@localhost:5432/amaimagery", alias="DATABASE_URL")
    
    # --- Security ---
    secret_key: str = Field("", alias="SECRET_KEY")
    jwt_alg: str = Field("HS256", alias="JWT_ALG")
    
    # --- Logging ---
    log_dir: str = Field("logs", alias="LOG_DIR")
    log_level: str = Field("INFO", alias="LOG_LEVEL")                  # DEBUG/INFO/WARNING/ERROR
    log_rotation: str = Field("00:00", alias="LOG_ROTATION")           # daily rotation
    log_retention: str = Field("30 days", alias="LOG_RETENTION")
    log_compression: str = Field("zip", alias="LOG_COMPRESSION")
    prompts_raw: int = Field(0, alias="PROMPTS_RAW")  
    log_mask_auth: bool = Field(True, alias="LOG_MASK_AUTH")

    # SMTP
    smtp_host: str = Field('localhost', alias='SMTP_HOST')
    smtp_port: int = Field(1025, alias='SMTP_PORT')
    smtp_user: str | None = Field(None, alias='SMTP_USER')
    smtp_pass: str | None = Field(None, alias='SMTP_PASS')
    smtp_from: str = Field('no-reply@example.com', alias='SMTP_FROM')
    smtp_security: str = Field('starttls', alias='SMTP_SECURITY')  # ssl | starttls | none
    smtp_timeout_sec: int = Field(15, alias='SMTP_TIMEOUT_SEC')
    
    # --- General toggles ---
    autocorrect: bool = Field(False, alias="AUTOCORRECT")
    base_url: str | None = Field(None, alias="BASE_URL")

    # Links in emails
    frontend_origin: str = Field('http://localhost:5173', alias='FRONTEND_ORIGIN')

    # TTL for password reset tokens (minutes)
    reset_token_ttl_min: int = Field(30, alias='RESET_TOKEN_TTL_MIN')
    
    # allowed hosts
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost","127.0.0.1"], alias='ALLOWED_HOSTS')

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def _parse_hosts(cls, v):
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
    redis_url: str = Field("redis://localhost:6379/0", alias='REDIS_URL')
    no_redis: bool = Field(False, alias='NO_REDIS')  # Disable Redis (for dev/testing)
    enable_hsts: bool = Field(False, alias='ENABLE_HSTS')

    # Limits
    gen_per_user_per_min: int = Field(60, alias="GEN_PER_USER_PER_MIN")
    gen_per_ip_per_min: int = Field(120, alias="GEN_PER_IP_PER_MIN")
    limits_enabled: bool = Field(True, alias="LIMITS_ENABLED")

    # Concurrency
    queue_wait_timeout_sec: float = Field(2.0, alias="QUEUE_WAIT_TIMEOUT_SEC")

    # --- Files ---
    file_signing_enabled: bool = Field(True, alias="FILE_SIGNING_ENABLED")
    file_url_ttl_sec: int = Field(86400, alias="FILE_URL_TTL_SEC")
    file_download_ttl_sec: int = Field(900, alias="FILE_DOWNLOAD_TTL_SEC")  # ≤ 15 min
    file_single_use: bool = Field(False, alias="FILE_SINGLE_USE")  
    file_allowed_exts: list[str] = Field(
        default_factory=lambda: ["png", "jpg", "jpeg", "webp"],
        alias="FILE_ALLOWED_EXTS"
    )
    file_allowed_mimes: list[str] = Field(
        default_factory=lambda: ["image/png", "image/jpeg", "image/webp"],
        alias="FILE_ALLOWED_MIMES"
    )
    
    @field_validator("file_allowed_exts", "file_allowed_mimes", "providers_enabled", mode="before")
    @classmethod
    def _parse_list_env(cls, v):
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
    def _parse_feature_flags(cls, v):
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
    access_ttl_min: int = Field(15, alias="ACCESS_TTL_MIN")
    revoke_prefix: str = Field("jwt:bl:", alias="REVOKE_PREFIX")

    # --- NSFW ---
    nsfw_allow: bool = Field(False, alias="NSFW_ALLOW")
    nsfw_blocklist_path: Path = Field(
        default=Path("app/config/nsfw_blocklist.txt"),
        alias="NSFW_BLOCKLIST_PATH"
    )
    
    # --- Auth: cookies, bcrypt ---
    refresh_cookie_name: str = Field("refresh_token", alias="REFRESH_COOKIE_NAME")
    refresh_ttl_days: int = Field(14, alias="REFRESH_TTL_DAYS")
    refresh_cookie_secure: bool = Field(True, alias="REFRESH_COOKIE_SECURE")  # prod=True
    bcrypt_rounds: int = Field(12, alias="BCRYPT_ROUNDS") 

    # --- API limits/timeouts ---
    max_body_bytes: int = Field(25 * 1024 * 1024, alias="MAX_BODY_BYTES")  # 25 MB
    max_query_value_len: int = Field(512, alias="MAX_QUERY_VALUE_LEN")
    request_timeout_seconds: int = Field(30, alias="REQUEST_TIMEOUT_SECONDS") # General request timeout
    keepalive_timeout_seconds: int = Field(5, alias="KEEPALIVE_TIMEOUT_SECONDS")  # uvicorn keep-alive
    
    # --- Hugging Face and offline caches ---
    hf_hub_offline: bool = Field(False, alias="HF_HUB_OFFLINE")
    transformers_offline: bool = Field(False, alias="TRANSFORMERS_OFFLINE")
    diffusers_offline: bool = Field(False, alias="DIFFUSERS_OFFLINE")
    hf_home: Path | None = Field(default=None, alias="HF_HOME")
    huggingface_hub_cache: Path | None = Field(default=None, alias="HUGGINGFACE_HUB_CACHE")
    transformers_cache: Path | None = Field(default=None, alias="TRANSFORMERS_CACHE")
    hf_token: str | None = Field(None, alias="HF_TOKEN")

    # --- Anti-DoS: generation ---
    max_concurrent_generations: int = Field(2, alias="MAX_CONCURRENT_GENERATIONS")
    @property
    def generation_timeout_seconds(self) -> int:
        return int(self.generation_timeout_sec)

    # --- Inference: security ---
    no_network: bool = Field(True, alias="NO_NETWORK")                  
    max_gen_width: int = Field(1024, alias="MAX_GEN_WIDTH")
    max_gen_height: int = Field(1024, alias="MAX_GEN_HEIGHT")
    max_gen_steps: int = Field(128, alias="MAX_GEN_STEPS")
    max_guidance: float = Field(20.0, alias="MAX_GUIDANCE")
    max_batch: int = Field(4, alias="MAX_BATCH")

    # --- Torch resourses ---
    torch_threads: int = Field(2, alias="TORCH_THREADS")                # CPU threads
    cuda_vram_fraction: float = Field(0.95, alias="CUDA_VRAM_FRACTION") 

    # --- Metrics --
    metrics_enabled: bool = Field(True, alias="METRICS_ENABLED")
    gpu_metrics_enabled: bool = Field(True, alias="GPU_METRICS_ENABLED")
    metrics_path: str = Field("/metrics", alias="METRICS_PATH")
    
    # --- Docs and UI ---
    docs_url: str | None = Field("/docs", alias="DOCS_URL")
    ui_static_dir: Path | None = Field(default=None, alias="UI_STATIC_DIR")

    # --- Paths ---
    root_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2],
        alias="ROOT_DIR"
    )
    outputs_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "outputs", alias="OUTPUTS_DIR")
    ip_adapter_dir: Path | None = Field(default=None, alias="IP_ADAPTER_DIR", validation_alias="IP_ADAPTER_DIR")
    ip_image_encoder_path: Path | None = Field(default=None, alias="IP_IMAGE_ENCODER_PATH", validation_alias="IP_IMAGE_ENCODER_PATH")

    # --- Validators --- 
    @field_validator("device", mode="before")
    @classmethod
    def _norm_device(cls, v):
        s = (str(v) if v is not None else "cuda").strip().lower()
        return "cuda" if s not in ("cpu", "cuda") else s
    
    @field_validator("torch_dtype", mode="before")
    @classmethod
    def _norm_dtype(cls, v):
        s = str(v or "fp16").lower().strip()
        if s not in ("fp16", "bf16", "fp32"):
            raise ValueError("TORCH_DTYPE must be fp16|bf16|fp32")
        return s

    @field_validator("model_id", "vae_id", mode="after")
    @classmethod
    def _check_local_when_offline(cls, v, info):
        try:
            no_net = bool(info.data.get("no_network"))
        except Exception:
            no_net = True
        if no_net and v:
            p = Path(str(v))
            if not p.exists():
                raise ValueError(f"{info.field_name} not found locally: {p}")
        return v
    
    @field_validator("hf_token", "hf_home", "transformers_cache", "base_url", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
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
        mode="before",
    )
    @classmethod
    def _as_path(cls, v):
        if v is None or isinstance(v, Path):
            return v
        s = os.path.expanduser(os.path.expandvars(str(v).strip()))
        return Path(s)
    
    @model_validator(mode="after")
    def _resolve_relative_paths(self):
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


# === Initialization and validation ===
def _load_env_file() -> None:
    """Load .env file if not running in Docker."""
    if not os.getenv("RUN_IN_DOCKER"):
        load_dotenv(".env")


def _create_directories(settings: Settings) -> None:
    """Create required directories for outputs and logs."""
    Path(settings.outputs_dir).mkdir(parents=True, exist_ok=True)
    
    for sub in ("access", "app", "generations", "prompts", "prompts/raw", "errors", "metrics"):
        Path(settings.log_dir, sub).mkdir(parents=True, exist_ok=True)


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
            "SQLite is not supported in production. Set DATABASE_URL to PostgreSQL "
            "(postgresql://user:password@host:port/dbname)"
        )
    
    if db_url.scheme.startswith("postgresql"):
        if (db_url.username or "") == "app" and (db_url.password or "") == "app":
            raise RuntimeError(
                "DATABASE_URL uses default credentials (app/app). "
                "Set strong username/password via environment variables."
            )
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
    settings = Settings()  # type: ignore[call-arg]
    _create_directories(settings)
    _validate_production_settings(settings)
    return settings


# Create settings instance 
_load_env_file()
settings: Settings = Settings()  # type: ignore[call-arg]
_create_directories(settings)
_validate_production_settings(settings)