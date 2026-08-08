"""
Database engine, session, and Base.

Connection string resolution order (secrets are never printed or logged):
  1. DATABASE_URL                     (explicit override)
  2. POSTGRES_URL                     (Vercel/Neon managed integration)
  3. SQLite demo fallback             (ONLY outside production)

Persistence is considered ENABLED (DB_ENABLED=True) whenever the URL came from
an explicit env var (DATABASE_URL or POSTGRES_URL), regardless of dialect — this
is what the test suite relies on with a throwaway SQLite file. The auto-generated
SQLite *demo fallback* (used only when no env var is set, outside production)
keeps DB_ENABLED=False so persistence-only endpoints honor their demo contract.
In production, if neither Postgres URL is present, persistence stays DISABLED
rather than silently writing to an ephemeral file. We never fabricate a
"connected" state, and never print the URL.
"""
from __future__ import annotations

import os
from typing import Iterator, Optional, Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

def _is_production() -> bool:
    env = (os.getenv("ENVIRONMENT") or os.getenv("VERCEL_ENV") or "").strip().lower()
    return env in {"production", "prod"}

def _normalize(url: Optional[str]) -> Optional[str]:
    """Normalize a Postgres URL to the psycopg2 dialect without dropping query
    params (e.g. sslmode=require that Neon needs). Non-postgres URLs (sqlite)
    are returned unchanged."""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    # Only touch the scheme; host, credentials and ?sslmode=... are preserved
    # verbatim so SSL parameters stay intact.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url

def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")

def _resolve_url() -> Tuple[Optional[str], bool]:
    """Return (engine_url, from_env). from_env=True means an explicit
    DATABASE_URL/POSTGRES_URL was provided (=> persistence enabled).

    An explicit SQLite override is only honored outside production; in
    production it is skipped entirely so production traffic never silently
    runs against an ephemeral SQLite file.
    """
    production = _is_production()
    for var in ("DATABASE_URL", "POSTGRES_URL"):
        candidate = _normalize(os.getenv(var))
        if not candidate:
            continue
        if production and _is_sqlite(candidate):
            continue
        return candidate, True
    if not production:
        return "sqlite:///./demo.db", False
    return None, False

_ENGINE_URL, _FROM_ENV = _resolve_url()
DATABASE_URL: Optional[str] = _ENGINE_URL
DB_ENABLED: bool = _FROM_ENV

_connect_args = {}
if _ENGINE_URL and _ENGINE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = (
    create_engine(_ENGINE_URL, pool_pre_ping=True, connect_args=_connect_args)
    if _ENGINE_URL
    else None
)

SessionLocal = (
    sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    if engine is not None
    else None
)

def safe_backend() -> str:
    """Return the DB backend name (e.g. 'postgresql', 'sqlite') WITHOUT any
    host, credentials, or query string - safe to expose in /health."""
    if not _ENGINE_URL:
        return "none"
    try:
        return make_url(_ENGINE_URL).get_backend_name()
    except Exception:
        return "unknown"

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a transactional session.

    Raises RuntimeError if no engine is configured so callers must explicitly
    handle demo mode rather than silently losing data.
    """
    if SessionLocal is None:
        raise RuntimeError("Database is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Create all tables from model metadata (dev/test convenience only).

    Production schema changes go through Alembic migrations, not this call.
    """
    if engine is None:
        return
    from app import models  # noqa: F401  (register models on Base.metadata)

    Base.metadata.create_all(bind=engine)

_MIGRATION_LOCK_KEY = 727384910  # arbitrary fixed pg_advisory_lock key for this app

def ensure_migrations_applied() -> None:
    """Best-effort: run `alembic upgrade head` against Postgres on cold start.

    OFF BY DEFAULT. Only runs when the account owner explicitly sets
    AUTO_MIGRATE_DB=true -- automatically mutating the production schema is a
    decision only the account owner should opt into, not something that ships
    on by default. Nothing executes until that env var is set in Vercel.

    There is no separate deploy/build step available for this @vercel/python
    serverless entrypoint to run migrations before traffic is served, and an
    agent has no access to the production connection string to run them out
    of band. Once opted in, this is the safe mechanism: idempotent (alembic
    no-ops at head), guarded by a Postgres session advisory lock so concurrent
    cold starts don't race each other's DDL, and it NEVER raises -- a failure
    here must not take the whole app down. DB-dependent endpoints will keep
    surfacing a clear error until it's fixed, same as today.

    No-op for SQLite (local dev already runs `alembic upgrade head` manually;
    a single-file local dev database has no concurrent-cold-start problem to
    guard against).
    """
    if (os.getenv("AUTO_MIGRATE_DB") or "").strip().lower() not in {"1", "true", "yes"}:
        return
    if not DB_ENABLED or engine is None or not _ENGINE_URL or not _ENGINE_URL.startswith("postgresql"):
        return
    import logging

    log = logging.getLogger(__name__)
    try:
        import sqlalchemy as sa
        from alembic import command
        from alembic.config import Config
        from pathlib import Path as _Path

        _database_dir = _Path(__file__).resolve().parents[2] / "database"
        cfg = Config(str(_database_dir / "alembic.ini"))
        cfg.set_main_option("script_location", str(_database_dir / "migrations"))

        with engine.connect() as conn:
            got_lock = conn.execute(sa.text("SELECT pg_try_advisory_lock(:k)"), {"k": _MIGRATION_LOCK_KEY}).scalar()
            if not got_lock:
                log.info("auto-migration: another instance holds the lock, skipping")
                return
            try:
                command.upgrade(cfg, "head")
                log.info("auto-migration: upgrade head complete")
            finally:
                conn.execute(sa.text("SELECT pg_advisory_unlock(:k)"), {"k": _MIGRATION_LOCK_KEY})
    except Exception:
        log.exception("auto-migration failed; DB-dependent endpoints may error until this is resolved")
