from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "fastapi-production-starter"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_starter"
    database_echo: bool = False

    jwt_secret_key: str = Field(default="change-this-local-development-secret", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)

    backend_cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: bool | str) -> bool:
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        return value

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("backend_cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        for origin in value:
            if origin != "*":
                AnyUrl(origin)
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env == "production":
            insecure_secret = self.jwt_secret_key == "change-this-local-development-secret"
            wildcard_with_credentials = "*" in self.backend_cors_origins
            if insecure_secret:
                raise ValueError("JWT_SECRET_KEY must be changed in production")
            if self.debug:
                raise ValueError("DEBUG must be disabled in production")
            if wildcard_with_credentials:
                raise ValueError("Wildcard CORS origins are not allowed in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
