"""
Sales lead capture API -- backs the public Pricing page's contact forms.

  POST /leads/       -> public, captures a lead (no auth) for human sales
                         follow-up. NOT a payment endpoint -- no charge is
                         made and no payment details are accepted here.
  GET  /leads/        -> admin only, view captured leads.

In demo mode (no database), the endpoint still returns 201 so the form UX
never breaks, but the submission is discarded -- callers should not assume
persistence without checking GET /health.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, require_roles

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadIn(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    company: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=50)
    plan: str = Field(default="starter", description="starter | professional | enterprise")
    intent: str = Field(default="subscribe", description="subscribe | enterprise | investor | consultant")
    message: Optional[str] = Field(default=None, max_length=2000)


class LeadOut(LeadIn):
    id: int
    status: str
    model_config = {"from_attributes": True}


class LeadAck(BaseModel):
    received: bool
    persisted: bool


@router.post("/", response_model=LeadAck, status_code=201)
def create_lead(data: LeadIn):
    if not DB_ENABLED:
        return LeadAck(received=True, persisted=False)
    from app import models

    db = SessionLocal()
    try:
        obj = models.SalesLead(status="new", **data.model_dump())
        db.add(obj)
        db.commit()
        return LeadAck(received=True, persisted=True)
    finally:
        db.close()


@router.get("/", response_model=List[LeadOut])
def list_leads(user: UserOut = Depends(require_roles("admin"))):
    if not DB_ENABLED:
        return []
    from app import models

    db = SessionLocal()
    try:
        return (
            db.query(models.SalesLead)
            .order_by(models.SalesLead.id.desc())
            .limit(500)
            .all()
        )
    finally:
        db.close()
