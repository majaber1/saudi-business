"""
Franchise Opportunities API.

  GET  /franchises/         -> public list (optional ?sector= filter)
  GET  /franchises/{id}     -> public detail
  POST /franchises/         -> admin/franchise_owner only (create)

Listings carry a verification_status; data provided by franchisors requires
direct verification and is labeled accordingly (never invented).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, require_roles

router = APIRouter(prefix="/franchises", tags=["franchises"])


def _db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Franchises require persistence.")
    return SessionLocal()


class FranchiseIn(BaseModel):
    brand: str = Field(..., min_length=1, max_length=200)
    sector: str = Field(..., min_length=1, max_length=100)
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    country: Optional[str] = None
    investment_min: Optional[float] = None
    investment_max: Optional[float] = None
    franchise_fee: Optional[float] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None


class FranchiseOut(FranchiseIn):
    id: int
    verification_status: str
    is_active: bool
    model_config = {"from_attributes": True}


@router.get("/", response_model=List[FranchiseOut])
def list_franchises(sector: Optional[str] = None):
    if not DB_ENABLED:
        return []
    from app import models
    db = SessionLocal()
    try:
        q = db.query(models.FranchiseOpportunity).filter_by(is_active=True)
        if sector:
            q = q.filter(models.FranchiseOpportunity.sector == sector)
        return q.order_by(models.FranchiseOpportunity.id.desc()).limit(200).all()
    finally:
        db.close()


@router.get("/{franchise_id}", response_model=FranchiseOut)
def get_franchise(franchise_id: int):
    if not DB_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")
    from app import models
    db = SessionLocal()
    try:
        obj = db.get(models.FranchiseOpportunity, franchise_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found")
        return obj
    finally:
        db.close()


@router.post("/", response_model=FranchiseOut, status_code=201)
def create_franchise(data: FranchiseIn, user: UserOut = Depends(require_roles("admin", "franchise_owner"))):
    from app import models
    db = _db()
    try:
        obj = models.FranchiseOpportunity(verification_status="demo", is_active=True, **data.model_dump())
        db.add(obj)
        db.add(models.AuditLog(actor_id=user.id, action="franchise.create", entity="franchise",
                               entity_id=None, meta={}))
        db.commit()
        db.refresh(obj)
        return obj
    finally:
        db.close()
