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
    openai_model: str = "deepseek-ai/DeepSeek-V4.1-Flash"
    image_model: str = "Tongyi-MAI/Z-Image-Turbo"
    image_base_url: str = ""
    image_size: str = ""
    image_negative_prompt: str = "真实人物肖像, 照片, 品牌logo, 低清晰度"
    image_timeout_seconds: float = 120.0
    search_provider: str = "firecrawl"
    firecrawl_api_key: str = ""
    search_max_results: int = 5
    search_max_scrapes: int = 4
    search_timeout_seconds: float = 60.0
    controller_request_limit: int = 10
    controller_tool_calls_limit: int = 12
    research_request_limit: int = 10
    research_tool_calls_limit: int = 16
    research_max_tokens: int = 8192
    public_base_url: str = "http://127.0.0.1:5173"
    auto_approve: bool = False
    llm_fallback_to_mock: bool = True
    llm_timeout_seconds: float = 180.0
    llm_thinking_budget: int = 2048
    llm_max_tokens: int = 4096

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def artifact_path(self) -> Path:
        return BACKEND_DIR / "data" / "artifacts"

    @property
    def image_cache_path(self) -> Path:
        return BACKEND_DIR / "data" / "image-cache"

    @property
    def resolved_image_base_url(self) -> str:
        return (self.image_base_url or self.openai_base_url).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
