from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import DB_ENABLED, SessionLocal, safe_backend
from app.api.auth import UserOut, require_roles

router = APIRouter(prefix="/admin", tags=["admin"])


class AuditEntry(BaseModel):
    id: int
    actor_id: Optional[int] = None
    action: str
    entity: Optional[str] = None
    entity_id: Optional[int] = None
    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    db_enabled: bool
    db_backend: str
    users: int = 0
    projects: int = 0
    studies: int = 0
    ideas: int = 0
    franchises: int = 0
    auctions: int = 0
    reports: int = 0
    multazim_requirements: int = 0
    recent_activity: List[AuditEntry] = []


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(user: UserOut = Depends(require_roles("admin"))):
    """Administrator dashboard: platform-wide counts and recent audit activity."""
    if not DB_ENABLED:
        return DashboardStats(db_enabled=False, db_backend=safe_backend())
    from app import models
    db = SessionLocal()
    try:
        def _count(model):
            try:
                return db.query(model).count()
            except Exception:
                return 0
        recent = (
            db.query(models.AuditLog)
            .order_by(models.AuditLog.id.desc())
            .limit(20)
            .all()
        )
        return DashboardStats(
            db_enabled=True,
            db_backend=safe_backend(),
            users=_count(models.User),
            projects=_count(models.Project),
            studies=_count(models.FeasibilityStudy),
            ideas=_count(models.IdeaBankEntry),
            franchises=_count(models.FranchiseOpportunity),
            auctions=_count(models.Auction),
            reports=_count(models.Report),
            multazim_requirements=_count(models.MultazimRequirement),
            recent_activity=recent,
        )
    finally:
        db.close()


@router.get("/audit", response_model=List[AuditEntry])
def audit_log(limit: int = 50, user: UserOut = Depends(require_roles("admin"))):
    """Recent audit log entries (admin only)."""
    if not DB_ENABLED:
        return []
    from app import models
    db = SessionLocal()
    try:
        limit = max(1, min(limit, 200))
        return (
            db.query(models.AuditLog)
            .order_by(models.AuditLog.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()
