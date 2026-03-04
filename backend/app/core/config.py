from functools import lru_cache
from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Proassist API"
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 120
    token_encryption_key: str
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    google_required_scopes: str = (
        "openid email profile "
        "https://www.googleapis.com/auth/gmail.send "
        "https://www.googleapis.com/auth/drive.file"
    )
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    worker_secret: str = "dev-worker-secret"

    @field_validator("token_encryption_key")
    @classmethod
    def validate_token_encryption_key(cls, value: str) -> str:
        Fernet(value.encode("utf-8"))
        return value

    @property
    def google_required_scopes_list(self) -> list[str]:
        return [scope.strip() for scope in self.google_required_scopes.split() if scope.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
