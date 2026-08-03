"""
Application configuration, loaded from environment variables.

Copy .env.example to .env and adjust for your environment. No real secrets or
credentials are baked in here: connection strings come exclusively from the
environment. The authoritative database URL resolution (DATABASE_URL ->
POSTGRES_URL -> development-only demo fallback) lives in app.db; ``database_url``
below is an optional convenience mirror and is intentionally empty by default so
nothing ever falls back to a hard-coded host or credentials.

CORS: origins come from the ``CORS_ORIGINS`` env var (JSON list or
comma-separated). ``resolve_cors`` enforces the browser/security invariant that
a wildcard origin ("*") is NEVER combined with credentialed requests, and that
production never serves a wildcard at all.
"""
from typing import List, Optional, Tuple

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Safe localhost defaults used ONLY outside production when nothing is configured.
DEV_DEFAULT_CORS_ORIGINS: Tuple[str, ...] = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)


def _is_production(environment: str) -> bool:
    return (environment or "").strip().lower() in {"production", "prod"}


def resolve_cors(origins: List[str], environment: str) -> Tuple[List[str], bool]:
    """Return the (allow_origins, allow_credentials) pair actually safe to pass
    to CORSMiddleware.

    Invariants:
      * "*" is never returned together with allow_credentials=True (browsers
        reject it and it is a security foot-gun).
      * In production a wildcard is stripped entirely; only an explicit
        allowlist is honored. If that leaves nothing, cross-origin access is
        denied (empty list) rather than silently opening the API to everyone.
      * Outside production, an empty configuration falls back to safe localhost
        dev origins with credentials enabled.
    """
    cleaned = [o.strip() for o in (origins or []) if o and o.strip()]
    production = _is_production(environment)
    has_wildcard = "*" in cleaned
    explicit = [o for o in cleaned if o != "*"]

    if production:
        # Never expose "*" in production; require an explicit allowlist.
        return explicit, True

    # Development / other environments.
    if not cleaned:
        return list(DEV_DEFAULT_CORS_ORIGINS), True
    if has_wildcard:
        # Honor the developer's wildcard, but disable credentials so the
        # combination stays valid for browsers.
        return ["*"], False
    return explicit, True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Saudi Business"
    app_version: str = "1.2.0"
    environment: str = "development"

    # Env-driven only. Empty by default -- never a hard-coded credentialed URL.
    # app.db is the source of truth for runtime engine selection.
    database_url: Optional[str] = None

    # Raw configured origins. Accepts a JSON list (["https://a"]) or a plain
    # comma-separated string (https://a,https://b). Empty by default so
    # development gets safe localhost defaults and production must be explicit.
    cors_origins: List[str] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("["):
                import json
                try:
                    return json.loads(raw)
                except Exception:
                    pass
            return [part.strip() for part in raw.split(",") if part.strip()]
        return value

    @property
    def cors(self) -> Tuple[List[str], bool]:
        """(allow_origins, allow_credentials) safe for CORSMiddleware."""
        return resolve_cors(self.cors_origins, self.environment)


settings = Settings()
