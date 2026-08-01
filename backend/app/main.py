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
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
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


@app.get("/health")
def health():
    connected = _db_ping()
    return {
        "status": "running",
        "service": settings.app_name,
        "environment": settings.environment,
        "persistence": "postgres" if DB_ENABLED else "demo (in-memory)",
        "db_enabled": DB_ENABLED,
        "db_backend": safe_backend(),
        "db_connected": connected,
    }
