from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    app_env: str = "development"
    debug: bool = True

    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    # Comma-separated origins. Kept as a plain string so that .env can use
    # "a,b" instead of pydantic-settings' JSON-list encoding.
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(
        default=None, validation_alias="OPENAI_BASE_URL"
    )
    # 默认值锁定演示用文本模型（decisions #23），换模型只改 .env
    openai_model: str = Field(
        default="deepseek-ai/DeepSeek-V3.1-Terminus", validation_alias="OPENAI_MODEL"
    )

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:rsm_demo_2026@127.0.0.1:5432/ruralsmartmark",
        validation_alias="DATABASE_URL",
    )

    jwt_secret: str = Field(
        default="dev-secret-change-me", validation_alias="JWT_SECRET"
    )
    jwt_expire_hours: int = Field(default=12, validation_alias="JWT_EXPIRE_HOURS")

    # 留空 = 每次随机；no-default field validator 兼容空串
    sim_seed: int | None = Field(default=None, validation_alias="SIM_SEED")

    @field_validator("sim_seed", mode="before")
    @classmethod
    def _empty_sim_seed_is_none(cls, v: object) -> object:
        return None if v == "" else v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
