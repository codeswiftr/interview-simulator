"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Interview Simulator"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interview_simulator"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # AI Services
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro_monthly: str = ""
    stripe_price_id_pro_annual: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Storage
    storage_bucket: str = "interview-simulator-media"
    storage_url: str = ""

    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
