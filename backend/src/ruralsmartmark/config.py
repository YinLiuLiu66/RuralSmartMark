from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = f"sqlite+aiosqlite:///{BACKEND_DIR / 'data' / 'app.db'}"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.siliconflow.cn/v1"
    openai_model: str = "deepseek-ai/DeepSeek-V3.1-Terminus"
    image_model: str = "Kwai-Kolors/Kolors"
    public_base_url: str = "http://127.0.0.1:5173"
    auto_approve: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
