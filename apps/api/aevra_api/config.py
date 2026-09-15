from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "development-only-change-before-deploy"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AEVRA_", extra="ignore")

    env: str = "development"
    secret_key: str = Field(default=DEFAULT_SECRET, min_length=32)
    access_token_minutes: int = Field(default=30, ge=5, le=1440)
    database_url: str = "sqlite:///./aevra.db"
    seed_email: str = "owner@aevra.local"
    seed_password: str = Field(default="AevraLocalOnly!2026", min_length=12)

    @model_validator(mode="after")
    def reject_development_secret_in_production(self) -> "Settings":
        insecure_secret = self.secret_key == DEFAULT_SECRET or self.secret_key.startswith(
            "replace-"
        )
        if self.env.lower() in {"production", "staging"} and insecure_secret:
            raise ValueError("AEVRA_SECRET_KEY must be changed outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
