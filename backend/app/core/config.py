"""
Application configuration, loaded from environment variables.

Copy .env.example to .env and adjust for your environment. No real secrets or
credentials are baked in here: connection strings come exclusively from the
environment. The authoritative database URL resolution (DATABASE_URL ->
POSTGRES_URL -> development-only demo fallback) lives in app.db; ``database_url``
below is an optional convenience mirror and is intentionally empty by default so
nothing ever falls back to a hard-coded host or credentials.
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Saudi Business"
    app_version: str = "1.2.0"
    environment: str = "development"

    # Env-driven only. Empty by default -- never a hard-coded credentialed URL.
    # app.db is the source of truth for runtime engine selection.
    database_url: Optional[str] = None

    cors_origins: list[str] = ["*"]


settings = Settings()
