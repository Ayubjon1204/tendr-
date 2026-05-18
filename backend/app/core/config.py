from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Tendr"
    environment: str = "development"
    debug: bool = True

    database_url: str = Field(..., description="Async SQLAlchemy DSN (asyncpg)")
    sync_database_url: str = Field(..., description="Sync DSN used by Alembic")

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    redis_url: str = "redis://localhost:6379/0"
    yandex_maps_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
