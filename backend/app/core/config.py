"""Application settings loaded from environment variables and optional .env file."""

from functools import lru_cache

from pydantic import field_validator
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

    # Authentication — JWT_SECRET_KEY has no production default.
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Project codes — prefix is configurable; sequence provides the number.
    PROJECT_CODE_PREFIX: str = "CRX"
    PROJECT_CODE_PAD_WIDTH: int = 4

    # Comma-separated browser origins allowed to call the API (empty = CORS off).
    # Example: http://localhost:3000,http://127.0.0.1:3000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Fernet key (url-safe base64) for encrypting AI provider API keys at rest.
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    AI_CREDENTIALS_KEY: str = ""

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        if not value:
            raise ValueError("JWT_ALGORITHM must not be empty")
        return value

    @field_validator("PROJECT_CODE_PREFIX")
    @classmethod
    def validate_project_code_prefix(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("PROJECT_CODE_PREFIX must not be empty")
        return cleaned

    @field_validator("PROJECT_CODE_PAD_WIDTH")
    @classmethod
    def validate_project_code_pad_width(cls, value: int) -> int:
        if value < 1 or value > 10:
            raise ValueError("PROJECT_CODE_PAD_WIDTH must be between 1 and 10")
        return value

    def require_jwt_secret(self) -> str:
        """Return JWT secret or fail safely when unset."""
        secret = self.JWT_SECRET_KEY.strip()
        if not secret:
            raise RuntimeError(
                "JWT_SECRET_KEY is not configured. Set it via environment "
                "or .env before using authentication."
            )
        return secret

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a clean list (empty disables CORS middleware)."""
        if not self.CORS_ORIGINS.strip():
            return []
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
