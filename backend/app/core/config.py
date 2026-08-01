"""Application settings loaded from environment variables and optional .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Curionex Studio API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Curionex Studio API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    # Override via environment or .env — never commit real credentials.
    DATABASE_URL: str = (
        "postgresql+psycopg://username:password@localhost:5432/curionex_studio"
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
