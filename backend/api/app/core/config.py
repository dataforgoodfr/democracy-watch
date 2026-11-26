from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "democracy_watch_API"
    VERSION: str = "0.1.0"
    # Base DuckDB au modèle V3 (DATA_MODEL_V3_DUCKDB.sql) : chemin local ou URL s3://.
    DATA_PATH: str | None = None
    # Accès S3 : sans clé, le bucket est lu anonymement.
    S3_ENDPOINT: str | None = None
    S3_REGION: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: SecretStr | None = None
    API_PASSWORD: SecretStr | None = None
    MEILI_URL: str | None = None
    MEILI_API_KEY: SecretStr | None = None
    MEILI_TIMEOUT: int = Field(default=10, gt=0)
