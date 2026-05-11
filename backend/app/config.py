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
    # Used by the skill-driven PPT renderer. Sonnet 4.6 turned out to spin in
    # error-recovery loops on this task; Opus 4.7 is more efficient end-to-end
    # despite its higher per-token cost. Without few-shots input-tokens stay
    # well under 100k, so total cost remains around $0.15-0.30 per render.
    render_model: str = "claude-opus-4-7"

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

    # Redis (Arq job queue for async offer generation)
    redis_url: str = "redis://redis:6379/0"

    # Berater profile (primary consultant on the right of the cover slide).
    # Single-tenant for now — moves to a per-user profile when we onboard a
    # second user. The secondary consultant is per-offer (see consultants table).
    berater_name: str = "Thomas Brunner"
    berater_titel: str = "Senior Partner"
    berater_tel: str = ""
    berater_email: str = "tbrunner@eragroup.com"

    # Storage bucket for rendered Word/PPT artifacts
    render_storage_bucket: str = "offer-renders"

    # Anthropic Skills + few-shot pool (Code-Execution rendering)
    era_presentation_skill_id: str = ""
    era_word_skill_id: str = ""
    few_shot_file_ids: str = ""

    @property
    def few_shot_file_id_list(self) -> list[str]:
        return [s.strip() for s in self.few_shot_file_ids.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this anywhere to access config."""
    return Settings()  # type: ignore[call-arg]
