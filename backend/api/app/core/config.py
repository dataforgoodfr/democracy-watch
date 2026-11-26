from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "democracy_watch_API"
    VERSION: str = "0.1.0"
    DATABASE_URL: str | None = None
    API_PASSWORD: SecretStr | None = None
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DATABASE_POOL_TIMEOUT: int = Field(default=10, gt=0)
    DATABASE_TIMEOUT: int = Field(default=10, gt=0)
    MEILI_URL: str | None = None
    MEILI_API_KEY: SecretStr | None = None
    MEILI_TIMEOUT: int = Field(default=10, gt=0)
