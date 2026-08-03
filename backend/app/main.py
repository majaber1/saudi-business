from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import DB_ENABLED, SessionLocal, safe_backend
from app.api.projects import router as projects_router
from app.api.financial import router as financial_router
from app.api.funding import router as funding_router
from app.api.auth import router as auth_router
from app.api.feasibility import router as feasibility_router
from app.api.reports import router as reports_router
from app.api.ideas import router as ideas_router
from app.api.franchises import router as franchises_router
from app.api.auctions import router as auctions_router
from app.api.qualification import router as qualification_router
from app.api.admin import router as admin_router

app = FastAPI(
    title=settings.app_name,
    description="Saudi Business | سعودي بزنس — AI Operating System for Investment Decisions",
    version=settings.app_version,
)

# CORS origins/credentials are resolved so a wildcard is never paired with
# credentials and production never serves "*" (see app.core.config.resolve_cors).
_cors_allow_origins, _cors_allow_credentials = settings.cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins,
    allow_credentials=_cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(financial_router)
app.include_router(funding_router)
app.include_router(feasibility_router)
app.include_router(reports_router)
app.include_router(ideas_router)
app.include_router(franchises_router)
app.include_router(auctions_router)
app.include_router(qualification_router)
app.include_router(admin_router)


def _db_ping() -> bool:
    """Attempt a trivial query to confirm live connectivity. Never raises."""
    if not DB_ENABLED:
        return False
    try:
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return True
        finally:
            db.close()
    except Exception:
        return False


def _persistence_label(backend: str, connected: bool) -> str:
    """Human-readable persistence descriptor derived from the *safe* backend
    name (never a URL). It tells the truth about four distinct states:

    1. Development demo file (sqlite:///./demo.db, DB_ENABLED=False):
       "sqlite demo fallback (local file, non-production)"
    2. In-memory sqlite (sqlite:///:memory:):
       "sqlite demo fallback (in-memory, non-persistent)"
    3. Production with NO engine/URL configured (engine is None):
       "disabled (database unconfigured)"
    4. A configured backend that fails the connectivity ping:
       "<backend> (unreachable)"
    5. A configured, reachable backend: the safe dialect name only.

    We NEVER claim durable/production storage for a demo fallback, and we NEVER
    say "in-memory" unless the engine URL is actually sqlite:///:memory:. No
    host, credentials, port, database name, or query string is ever exposed.
    """
    from app.db import DATABASE_URL as _DB_URL

    # No persistence enabled from an explicit env var.
    if not DB_ENABLED:
        if not _DB_URL:
            # No engine at all (production with neither Postgres URL present).
            return "disabled (database unconfigured)"
        if ":memory:" in _DB_URL:
            return "sqlite demo fallback (in-memory, non-persistent)"
        # Auto-generated local file demo (development only).
        return "sqlite demo fallback (local file, non-production)"

    # Persistence is configured from an env var.
    label = backend or "unknown"
    if not connected:
        return label + " (unreachable)"
    return label


@app.get("/health")
def health():
    """Liveness + database observability contract.

    Exposes only safe, non-sensitive fields. ``db_backend``/``persistence`` are
    derived from the SQLAlchemy dialect name only and never include host,
    credentials, port, database name, or query parameters.
    """
    connected = _db_ping()
    backend = safe_backend()
    return {
        "status": "running",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "db_enabled": DB_ENABLED,
        "db_backend": backend,
        "db_connected": connected,
        "persistence": _persistence_label(backend, connected),
    }
