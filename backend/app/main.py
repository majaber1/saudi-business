from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import DB_ENABLED
from app.api.projects import router as projects_router
from app.api.financial import router as financial_router
from app.api.funding import router as funding_router
from app.api.auth import router as auth_router

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


@app.get("/health")
def health():
    return {
        "status": "running",
        "service": settings.app_name,
        "environment": settings.environment,
        "persistence": "postgres" if DB_ENABLED else "demo (in-memory)",
        "db_enabled": DB_ENABLED,
    }
