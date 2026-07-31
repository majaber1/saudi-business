"""
Database engine, session, and Base.

Persistence is driven entirely by the DATABASE_URL environment variable.
If it is unset (e.g. on a preview with no DB provisioned) the app runs in a
safe *demo mode*: DB_ENABLED is False and routers fall back to an in-memory
store instead of raising. We never pretend data is persisted when it is not.
"""
from __future__ import annotations

import os
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _normalize(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    # Heroku/Vercel style prefix -> SQLAlchemy dialect
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DATABASE_URL: Optional[str] = _normalize(os.getenv("DATABASE_URL"))
DB_ENABLED: bool = DATABASE_URL is not None

# SQLite (used by the test suite) needs a special connect arg.
_connect_args = {}
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = (
    create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
    if DB_ENABLED
    else None
)

SessionLocal = (
    sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    if engine is not None
    else None
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a transactional session.

    Raises RuntimeError if called while persistence is disabled so callers
    must explicitly handle demo mode rather than silently losing data.
    """
    if SessionLocal is None:
        raise RuntimeError("Database is not configured (DATABASE_URL unset).")
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
