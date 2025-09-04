from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_id: str = "models/dreamshaper_6NoVae.safetensors"
    device: str = "cpu"              
    max_steps: int = 32
    max_size: int = 768
    out_dir: str = "outputs"
    vae_id: str | None = None
    
    # --- logging ---
    log_dir: str = "logs"
    log_level: str = "INFO"                     # DEBUG/INFO/WARNING/ERROR
    log_rotation: str = "00:00"                 # суточная ротация
    log_retention: str = "30 days"
    log_compression: str = "zip"
    prompts_raw: int = 0                        # 1=сохранять raw-тексты в prompts/raw/

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

settings = Settings()
Path(settings.out_dir).mkdir(parents=True, exist_ok=True)
for sub in ("access","app","generations","prompts","prompts/raw","errors","metrics"):
    Path(settings.log_dir, sub).mkdir(parents=True, exist_ok=True)