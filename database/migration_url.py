"""Migration connection-URL resolution (pure, importable, side-effect free).

Alembic DDL should run over a DIRECT / NON-POOLING connection. Managed
Postgres providers such as Neon (via Vercel) expose a transaction pooler
(PgBouncer) for normal app traffic, but running migrations through the pooler
can fail or behave inconsistently because DDL needs a real session. Providers
therefore also expose a direct endpoint, commonly as ``POSTGRES_URL_NON_POOLING``
or ``DIRECT_DATABASE_URL``.

Resolution priority (first non-empty wins):
    1. POSTGRES_URL_NON_POOLING  (Vercel/Neon direct endpoint)
    2. DIRECT_DATABASE_URL       (generic direct endpoint alias)
    3. DATABASE_URL              (explicit override / CI)
    4. POSTGRES_URL              (pooled managed URL, last resort)

The URL is returned normalized to the psycopg2 driver, with host, credentials
and query parameters (e.g. sslmode=require) preserved verbatim. Nothing here is
ever logged or printed, so credentials never leak.
"""
from __future__ import annotations

from typing import Mapping, Optional

# Ordered candidates: direct/non-pooling endpoints take precedence over pooled.
MIGRATION_URL_VARS = (
    "POSTGRES_URL_NON_POOLING",
    "DIRECT_DATABASE_URL",
    "DATABASE_URL",
    "POSTGRES_URL",
)


def normalize_pg_url(url: Optional[str]) -> Optional[str]:
    """Return the URL using the explicit psycopg2 driver, preserving host,
    credentials and query string. Non-postgres URLs (e.g. sqlite) and empty
    values are returned unchanged / as None."""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def resolve_migration_url(environ: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """Resolve the connection URL Alembic should use for migrations.

    Prefers a direct/non-pooling endpoint when configured, then falls back to
    the standard DATABASE_URL / POSTGRES_URL. Blank environment values are
    ignored so an empty var never shadows a populated one. Returns the
    normalized URL, or None when nothing is configured.
    """
    import os

    env = os.environ if environ is None else environ
    for var in MIGRATION_URL_VARS:
        candidate = normalize_pg_url(env.get(var))
        if candidate:
            return candidate
    return None
