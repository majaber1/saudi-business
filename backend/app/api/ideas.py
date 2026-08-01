"""
Idea Bank API.

  GET  /ideas/            -> public list (optional ?industry= filter)
  GET  /ideas/{id}        -> public detail
  POST /ideas/            -> admin/consultant only (create)

Persisted to PostgreSQL when DB_ENABLED; otherwise 503 for writes and an
empty list for reads, so demo previews never show fabricated catalog data.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, require_roles

router = APIRouter(prefix="/ideas", tags=["ideas"])


def _db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Idea Bank requires persistence.")
    return SessionLocal()


class IdeaIn(BaseModel):
    title_en: str = Field(..., min_length=1, max_length=200)
    title_ar: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    summary_en: Optional[str] = None
    summary_ar: Optional[str] = None
    revenue_model: Optional[str] = None
    investment_min: Optional[float] = None
    investment_max: Optional[float] = None
    difficulty: Optional[str] = None


class IdeaOut(IdeaIn):
    id: int
    status: str
    model_config = {"from_attributes": True}


@router.get("/", response_model=List[IdeaOut])
def list_ideas(industry: Optional[str] = None):
    if not DB_ENABLED:
        return []
    from app import models
    db = SessionLocal()
    try:
        q = db.query(models.IdeaBankEntry).filter_by(status="published")
        if industry:
            q = q.filter(models.IdeaBankEntry.industry == industry)
        return q.order_by(models.IdeaBankEntry.id.desc()).limit(200).all()
    finally:
        db.close()


@router.get("/{idea_id}", response_model=IdeaOut)
def get_idea(idea_id: int):
    if not DB_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")
    from app import models
    db = SessionLocal()
    try:
        obj = db.get(models.IdeaBankEntry, idea_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found")
        return obj
    finally:
        db.close()


@router.post("/", response_model=IdeaOut, status_code=201)
def create_idea(data: IdeaIn, user: UserOut = Depends(require_roles("admin", "consultant"))):
    from app import models
    db = _db()
    try:
        obj = models.IdeaBankEntry(status="published", **data.model_dump())
        db.add(obj)
        db.add(models.AuditLog(actor_id=user.id, action="idea.create", entity="idea",
                               entity_id=None, meta={}))
        db.commit()
        db.refresh(obj)
        return obj
    finally:
        db.close()
