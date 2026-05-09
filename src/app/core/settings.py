from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".example.env", ".env"], env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vega_app"

    vega_ws_url: str = "ws://127.0.0.1:8002"
    vega_ws_login: str
    vega_ws_password: SecretStr

    s3_endpoint_url: str | None = None
    s3_bucket: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_region: str = "us-east-1"


settings = Settings()
