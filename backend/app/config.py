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
    openrouter_api_key: str = ""
    groq_api_key: str = ""

    # AI Provider Selection (openai, openrouter, groq)
    transcription_provider: str = "openai"  # openai or groq
    content_analysis_provider: str = "anthropic"  # anthropic or openrouter

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro_monthly: str = ""
    stripe_price_id_pro_annual: str = ""
    stripe_price_id_team_monthly: str = ""
    stripe_price_id_team_annual: str = ""
    stripe_trial_days: int = 7

    # CORS origins - set via CORS_ORIGINS env var
    # Production: Set to specific domains only (e.g., "https://app.codeswiftr.com,https://interview-simulator-4bo.pages.dev")
    # Development: Defaults include localhost ports for local development
    cors_origins: list[str] = [
        # Production domains (always allowed)
        "https://app.codeswiftr.com",
        "https://interview-simulator-4bo.pages.dev",
    ]

    # Development-only CORS origins (automatically added when debug=True or environment=development)
    # These are NOT included in production by default
    _dev_cors_origins: list[str] = [
        # Vite dev server (default: 5173)
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Vite preview server (default: 4173)
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        # Additional Vite fallback ports (5174-5176)
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        # Legacy/alternative dev ports
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Local development domain (via Caddy/reverse proxy)
        "http://app.codeswiftr.local:8080",
        "http://app.codeswiftr.local",
    ]

    @property
    def effective_cors_origins(self) -> list[str]:
        """Get CORS origins based on environment.

        In development/debug mode, includes localhost origins.
        In production, only includes production domains.
        """
        origins = list(self.cors_origins)
        if self.debug or self.environment == "development":
            origins.extend(self._dev_cors_origins)
        return origins

    # Storage
    storage_bucket: str = "interview-simulator-media"
    storage_url: str = ""

    # Error Monitoring (optional)
    sentry_dsn: str = ""

    # Email / SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@codeswiftr.com"

    # Resend (preferred email provider)
    # Note: Domain must be verified in Resend dashboard
    # Use hello@codeswiftr.com as it's the verified sender
    resend_api_key: str = ""
    resend_from_email: str = "hello@codeswiftr.com"
    resend_from_name: str = "Interview Simulator"

    # Frontend URL for email links
    frontend_url: str = "http://localhost:5173"

    # Feature flags (soft-launch defaults)
    video_features_enabled: bool = False

    # Analytics (PostHog)
    posthog_api_key: str = ""
    posthog_host: str = "https://app.posthog.com"

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
        security_issues = []

        # Critical database
        if not self.database_url or self.database_url.startswith(
            "postgresql+asyncpg://postgres:postgres@localhost"
        ):
            missing_vars.append("DATABASE_URL")

        # Critical AI services
        if not self.anthropic_api_key:
            missing_vars.append("ANTHROPIC_API_KEY")
        if not self.openai_api_key:
            missing_vars.append("OPENAI_API_KEY")

        # Critical security
        if not self.secret_key or self.secret_key == "change-me-in-production":
            missing_vars.append("SECRET_KEY")

        # CORS security validation
        if "*" in self.cors_origins or any("*" in origin for origin in self.cors_origins):
            security_issues.append(
                "CORS origins contain wildcards. This is a security risk. "
                "Please set CORS_ORIGINS environment variable to specific domains."
            )

        # Ensure HTTPS origins in production
        for origin in self.cors_origins:
            if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
                continue  # Allow localhost for development/testing
            if not origin.startswith("https://"):
                security_issues.append(f"CORS origin '{origin}' should use HTTPS in production")

        # Stripe (required for subscriptions, but allow if not using)
        # We'll only warn, not fail, for Stripe

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables for production: {', '.join(missing_vars)}. "
                "Please set these in your environment or .env file."
            )

        if security_issues:
            raise ValueError(
                f"Security configuration issues detected: {'; '.join(security_issues)}"
            )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
