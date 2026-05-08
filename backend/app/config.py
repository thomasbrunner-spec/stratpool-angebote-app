"""
Application configuration via Pydantic Settings.
All values come from environment variables (or .env file in development).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App metadata
    app_name: str = "stratpool-app"
    environment: str = "development"  # development | staging | production
    debug: bool = False

    # API
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-opus-4-7"

    # Voyage AI
    voyage_api_key: str
    voyage_model: str = "voyage-3-large"

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Database (Postgres via Supabase)
    database_url: str

    # Auth
    jwt_secret: str  # = Supabase JWT Secret
    jwt_algorithm: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this anywhere to access config."""
    return Settings()  # type: ignore[call-arg]
