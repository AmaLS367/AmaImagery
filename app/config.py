from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from urllib.parse import urlparse

from pathlib import Path
import warnings, json, os

class Settings(BaseSettings):
    model_id: str = "models/dreamshaper_6NoVae.safetensors"
    device: str = "cuda"              
    max_steps: int = 32
    max_size: int = 768
    out_dir: str = "outputs"
    vae_id: str | None = None

    # --- auth/db ---
    database_url: str = Field("sqlite:///./genai.db", alias="DATABASE_URL")
    secret_key: str = Field("CHANGE_ME_LONG_RANDOM", alias="SECRET_KEY")
    jwt_alg: str = Field("HS256", alias="JWT_ALG")
    
    # --- logging ---
    log_dir: str = "logs"
    log_level: str = "INFO"                     # DEBUG/INFO/WARNING/ERROR
    log_rotation: str = "00:00"                 # суточная ротация
    log_retention: str = "30 days"
    log_compression: str = "zip"
    prompts_raw: int = 0                      # 1=сохранять raw-тексты в prompts/raw/

    # SMTP
    smtp_host: str = Field('localhost', alias='SMTP_HOST')
    smtp_port: int = Field(1025, alias='SMTP_PORT')
    smtp_user: str | None = Field(None, alias='SMTP_USER')
    smtp_pass: str | None = Field(None, alias='SMTP_PASS')
    smtp_from: str = Field('no-reply@example.com', alias='SMTP_FROM')
    smtp_security: str = Field('starttls', alias='SMTP_SECURITY')  # ssl | starttls | none
    smtp_timeout_sec: int = Field(15, alias='SMTP_TIMEOUT_SEC')

    # Ссылки в письмах
    frontend_origin: str = Field('http://localhost:5173', alias='FRONTEND_ORIGIN')

    # TTL токена сброса
    reset_token_ttl_min: int = Field(30, alias='RESET_TOKEN_TTL_MIN')

    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost","127.0.0.1"], alias='ALLOWED_HOSTS')

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def _parse_hosts(cls, v):
        if v is None or v == "":
            return ["localhost", "127.0.0.1"]
        if isinstance(v, str):
            s = v.strip()
            # JSON-список
            if s.startswith("["):
                try:
                    data = json.loads(s)
                    return [str(x).strip() for x in data if str(x).strip()]
                except Exception:
                    pass
            # CSV/через ; или пробелы
            parts = s.replace(";", ",").split(",")
            return [p.strip() for p in parts if p.strip()]
        return v

    redis_url: str = Field("redis://localhost:6379/0", alias='REDIS_URL')
    enable_hsts: bool = Field(False, alias='ENABLE_HSTS')

    # Limits / Лимиты
    gen_per_user_per_min: int = Field(60, alias="GEN_PER_USER_PER_MIN")
    gen_per_ip_per_min: int = Field(120, alias="GEN_PER_IP_PER_MIN")
    limits_enabled: bool = Field(True, alias="LIMITS_ENABLED")

    # Конкурентность
    queue_wait_timeout_sec: float = Field(2.0, alias="QUEUE_WAIT_TIMEOUT_SEC")

    file_signing_enabled: bool = Field(True, alias="FILE_SIGNING_ENABLED")
    file_url_ttl_sec: int = Field(86400, alias="FILE_URL_TTL_SEC")

    access_ttl_min: int = Field(15, alias="ACCESS_TTL_MIN")
    revoke_prefix: str = Field("jwt:bl:", alias="REVOKE_PREFIX")

    log_mask_auth: bool = Field(True, alias="LOG_MASK_AUTH")

    generation_timeout_sec: int = Field(300, alias="GENERATION_TIMEOUT_SEC")

    ui_mount_enabled: bool = Field(True, alias="UI_MOUNT_ENABLED")
    ui_static_dir: str | None = Field(None, alias="UI_STATIC_DIR")

    nsfw_allow: bool = Field(False, alias="NSFW_ALLOW")
    nsfw_blocklist_path: str = Field("config/nsfw_blocklist.txt", alias="NSFW_BLOCKLIST_PATH")

    refresh_cookie_name: str = Field("refresh_token", alias="REFRESH_COOKIE_NAME")
    refresh_ttl_days: int = Field(14, alias="REFRESH_TTL_DAYS")
    refresh_cookie_secure: bool = Field(True, alias="REFRESH_COOKIE_SECURE")  # prod=True
    bcrypt_rounds: int = Field(12, alias="BCRYPT_ROUNDS") 

    # --- API limits/timeouts ---
    max_body_bytes: int = Field(25 * 1024 * 1024, alias="MAX_BODY_BYTES")  # 25 MB
    max_query_value_len: int = Field(512, alias="MAX_QUERY_VALUE_LEN")
    request_timeout_seconds: int = Field(30, alias="REQUEST_TIMEOUT_SECONDS")  # общий таймаут обработки
    keepalive_timeout_seconds: int = Field(5, alias="KEEPALIVE_TIMEOUT_SECONDS")  # uvicorn keep-alive

    # --- Files ---
    file_download_ttl_sec: int = Field(900, alias="FILE_DOWNLOAD_TTL_SEC")  # ≤ 15 мин
    file_single_use: bool = Field(False, alias="FILE_SINGLE_USE")  # включай в проде при необходимости
    file_allowed_exts: list[str] = Field(default_factory=lambda: ["png", "jpg", "jpeg", "webp"])
    file_allowed_mimes: list[str] = Field(default_factory=lambda: ["image/png", "image/jpeg", "image/webp"])

    # --- Anti-DoS: генерация ---
    max_concurrent_generations: int = Field(2, alias="MAX_CONCURRENT_GENERATIONS")
    @property
    def generation_timeout_seconds(self) -> int:
        return int(self.generation_timeout_sec)

    # --- Inference: безопасность ---
    no_network: bool = Field(True, alias="NO_NETWORK")                  
    max_gen_width: int = Field(1024, alias="MAX_GEN_WIDTH")
    max_gen_height: int = Field(1024, alias="MAX_GEN_HEIGHT")
    max_gen_steps: int = Field(50, alias="MAX_GEN_STEPS")
    max_guidance: float = Field(20.0, alias="MAX_GUIDANCE")
    max_batch: int = Field(4, alias="MAX_BATCH")

    # --- Torch ресурсы ---
    torch_threads: int = Field(2, alias="TORCH_THREADS")                # CPU threads
    cuda_vram_fraction: float = Field(0.95, alias="CUDA_VRAM_FRACTION") # 0..1, если CUDA есть

    # --- Ip adapter path --
    ip_adapter_dir: str | None = Field(None, alias="IP_ADAPTER_DIR")

    # --- Metrics --
    metrics_enabled: bool = Field(True, alias="METRICS_ENABLED")
    gpu_metrics_enabled: bool = Field(True, alias="GPU_METRICS_ENABLED")
    metrics_path: str = Field("/metrics", alias="METRICS_PATH")

    # --- Paths --
    root_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    outputs_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "outputs", alias="OUTPUTS_DIR")
    
    ip_adapter_dir: str | None = Field(default=None, validation_alias="IP_ADAPTER_DIR")
    ip_image_encoder_path: str | None = Field(default=None, validation_alias="IP_IMAGE_ENCODER_PATH")

    @field_validator("device", mode="before")
    @classmethod
    def _norm_device(cls, v):
        s = (str(v) if v is not None else "cuda").strip().lower()
        return "cuda" if s not in ("cpu", "cuda") else s

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=None,
        case_sensitive=False
    )

if not os.getenv("RUN_IN_DOCKER"):
    from dotenv import load_dotenv
    load_dotenv(".env")

settings = Settings() # type: ignore
Path(settings.out_dir).mkdir(parents=True, exist_ok=True)
for sub in ("access","app","generations","prompts","prompts/raw","errors","metrics"):
    Path(settings.log_dir, sub).mkdir(parents=True, exist_ok=True)

if not settings.secret_key or settings.secret_key in {"CHANGE_ME","CHANGE_ME_LONG_RANDOM"}:
    raise RuntimeError("SECRET_KEY must be set via env")

_pg = urlparse(settings.database_url)
if _pg.scheme == "postgresql" and (_pg.username or "") == "app" and (_pg.password or "") == "app":
    raise RuntimeError("DATABASE_URL uses default credentials (app/app). Set strong user/password via env.")

_ru = urlparse(settings.redis_url)
if _ru.scheme.startswith("redis") and (not _ru.password or _ru.password.strip() == ""):
    # Allow no password for local development
    if os.getenv("ENV", "dev").lower() not in ["dev", "development", "local"]:
        raise RuntimeError("REDIS_URL must include a password (redis://:password@host:port/db).")