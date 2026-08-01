from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, require_roles

router = APIRouter(prefix="/multazim", tags=["multazim"])


class RequirementIn(BaseModel):
    category: str
    title_en: str
    title_ar: str
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    authority: Optional[str] = None
    is_mandatory: bool = True
    source_url: Optional[str] = None


class RequirementOut(RequirementIn):
    id: int
    model_config = {"from_attributes": True}


@router.get("/", response_model=List[RequirementOut])
def list_requirements(category: Optional[str] = None, authority: Optional[str] = None):
    """List Multazim compliance requirements (bilingual). Public read."""
    if not DB_ENABLED:
        return []
    from app import models
    db = SessionLocal()
    try:
        q = db.query(models.MultazimRequirement)
        if category:
            q = q.filter(models.MultazimRequirement.category == category)
        if authority:
            q = q.filter(models.MultazimRequirement.authority == authority)
        return q.order_by(models.MultazimRequirement.category, models.MultazimRequirement.id).all()
    finally:
        db.close()


@router.get("/categories", response_model=List[str])
def list_categories():
    """Distinct requirement categories for filtering."""
    if not DB_ENABLED:
        return []
    from app import models
    db = SessionLocal()
    try:
        rows = db.query(models.MultazimRequirement.category).distinct().all()
        return sorted({r[0] for r in rows if r[0]})
    finally:
        db.close()


@router.get("/{requirement_id}", response_model=RequirementOut)
def get_requirement(requirement_id: int):
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Persistence is disabled in demo mode.")
    from app import models
    db = SessionLocal()
    try:
        obj = db.get(models.MultazimRequirement, requirement_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Requirement not found.")
        return obj
    finally:
        db.close()


@router.post("/", response_model=RequirementOut, status_code=201)
def create_requirement(
    data: RequirementIn,
    user: UserOut = Depends(require_roles("admin", "gov_reviewer")),
):
    """Create a Multazim requirement. Admin or Government Reviewer only."""
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Persistence is disabled in demo mode.")
    from app import models
    from app.api.auth import _audit
    db = SessionLocal()
    try:
        obj = models.MultazimRequirement(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        _audit(db, user.id, "create", "multazim_requirement", obj.id, {"category": obj.category})
        return obj
    finally:
        db.close()
