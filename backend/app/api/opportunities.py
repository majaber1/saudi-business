"""
Investment Opportunities API -- the investor-facing catalog.

  GET  /opportunities/            -> public list, filterable by industry,
                                      risk_level, and an investor's available
                                      amount (min_amount <= opportunity's
                                      investment_min, i.e. "what fits my budget")
  GET  /opportunities/{id}        -> public detail
  POST /opportunities/            -> admin/consultant only (create)

Distinct from /projects (a founder's own feasibility workspace): this is
what an investor browses. expected_return_percent is always an indicative,
source-labeled estimate -- never presented as a guarantee.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, require_roles

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Investment opportunities require persistence.")
    return SessionLocal()


class OpportunityIn(BaseModel):
    title_en: str = Field(..., min_length=1, max_length=200)
    title_ar: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    summary_en: Optional[str] = None
    summary_ar: Optional[str] = None
    stage: str = Field(default="mvp", description="idea | mvp | early_revenue | growth")
    risk_level: str = Field(default="medium", description="low | medium | high")
    investment_min: Optional[float] = Field(default=None, ge=0)
    investment_max: Optional[float] = Field(default=None, ge=0)
    expected_return_percent: Optional[float] = None
    funding_goal: Optional[float] = Field(default=None, ge=0)
    source_url: Optional[str] = None


class OpportunityOut(OpportunityIn):
    id: int
    funding_committed: float = 0
    verification_status: str
    is_active: bool
    model_config = {"from_attributes": True}


@router.get("/", response_model=List[OpportunityOut])
def list_opportunities(
    industry: Optional[str] = None,
    risk_level: Optional[str] = None,
    max_amount: Optional[float] = None,
):
    """max_amount is the investor's available budget: only opportunities whose
    investment_min fits within that budget (or has no stated minimum) are
    returned -- "show me what I can actually afford to enter."""
    if not DB_ENABLED:
        return []
    from app import models

    db = SessionLocal()
    try:
        q = db.query(models.InvestmentOpportunity).filter_by(is_active=True)
        if industry:
            q = q.filter(models.InvestmentOpportunity.industry == industry)
        if risk_level:
            q = q.filter(models.InvestmentOpportunity.risk_level == risk_level)
        if max_amount is not None:
            q = q.filter(
                (models.InvestmentOpportunity.investment_min.is_(None))
                | (models.InvestmentOpportunity.investment_min <= max_amount)
            )
        return q.order_by(models.InvestmentOpportunity.id.desc()).limit(200).all()
    finally:
        db.close()


@router.get("/{opportunity_id}", response_model=OpportunityOut)
def get_opportunity(opportunity_id: int):
    if not DB_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")
    from app import models

    db = SessionLocal()
    try:
        obj = db.get(models.InvestmentOpportunity, opportunity_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found")
        return obj
    finally:
        db.close()


@router.post("/", response_model=OpportunityOut, status_code=201)
def create_opportunity(data: OpportunityIn, user: UserOut = Depends(require_roles("admin", "consultant"))):
    from app import models

    db = _db()
    try:
        obj = models.InvestmentOpportunity(verification_status="demo", is_active=True, **data.model_dump())
        db.add(obj)
        db.add(models.AuditLog(actor_id=user.id, action="opportunity.create", entity="opportunity",
                               entity_id=None, meta={}))
        db.commit()
        db.refresh(obj)
        return obj
    finally:
        db.close()
