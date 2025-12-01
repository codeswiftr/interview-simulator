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

    # Error Monitoring (optional)
    sentry_dsn: str = ""

    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        return self.database_url

    def validate_for_production(self) -> None:
        """Validate that required environment variables are set for production.
        
        Raises:
            ValueError: If critical env vars are missing in production mode
        """
        if self.debug:
            # In debug mode, allow missing optional vars
            return
        
        missing_vars = []
        
        # Critical database
        if not self.database_url or self.database_url.startswith("postgresql+asyncpg://postgres:postgres@localhost"):
            missing_vars.append("DATABASE_URL")
        
        # Critical AI services
        if not self.anthropic_api_key:
            missing_vars.append("ANTHROPIC_API_KEY")
        if not self.openai_api_key:
            missing_vars.append("OPENAI_API_KEY")
        
        # Critical security
        if not self.secret_key or self.secret_key == "change-me-in-production":
            missing_vars.append("SECRET_KEY")
        
        # Stripe (required for subscriptions, but allow if not using)
        # We'll only warn, not fail, for Stripe
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables for production: {', '.join(missing_vars)}. "
                "Please set these in your environment or .env file."
            )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
