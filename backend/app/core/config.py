from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    app_name: str = "Firx Kitchen MVP"
    debug: bool = True

    # Platform database (central): tenants, users, memberships
    database_url: str = (
        "postgresql+asyncpg://firx:firx@localhost:5432/firx_platform"
    )

    # Tenant operational databases use PostgreSQL schemas on the same server
    # for the MVP (schema-per-tenant). Each tenant row stores its schema name.
    # This stays 100% compatible with Database-per-Tenant later (a tenant
    # schema can be moved to its own physical database without model changes).

    jwt_secret: str = "change-me-in-production-firx-mvp"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24
    refresh_token_minutes: int = 60 * 24 * 30

    file_storage_dir: str = "data/files"
    max_upload_mb: int = 20

    # Allowed demo/login bootstrap
    allow_registration: bool = True

    # AI pipeline: default provider + optional credentials for real providers.
    # Keep empty to use the deterministic mock provider.
    #
    # Selection precedence (see app/ai/providers.get_provider):
    #   request `provider_name` > AI_PROVIDER > APP_AI_PROVIDER
    #   > APP_AI_DEFAULT_PROVIDER > "mock"
    ai_default_provider: str = "mock"
    ai_timeout: float = 60.0
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
