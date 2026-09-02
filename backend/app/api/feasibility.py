"""
Feasibility study API: the multi-step wizard backend.

Flow:
  POST   /feasibility/            -> create a study (auto-creates a project)
  GET    /feasibility/            -> list the caller's studies (admins: all)
  GET    /feasibility/{id}        -> fetch one owned study (with latest result)
  PATCH  /feasibility/{id}/step   -> save a wizard step (merges payload)
  POST   /feasibility/{id}/compute-> run the financial engine, persist result

Ownership is enforced on the server through the study's parent project owner:
a user may only read or mutate studies whose project they own; an admin may
access any study. Ownership is never trusted from the client.

Requires persistence (DATABASE_URL). In demo mode every endpoint returns 503 so
nobody believes a study was saved when it was not.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, get_current_user

# financial-engine/ lives at the repo root, three levels above this file.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "financial-engine"))
from calculator import evaluate_feasibility, sensitivity_analysis  # noqa: E402

router = APIRouter(prefix="/feasibility", tags=["feasibility"])


def _require_db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Feasibility studies require persistence (database not configured).")
    return SessionLocal()


def _project_owner_id(db, models, project_id) -> Optional[int]:
    project = db.get(models.Project, project_id) if project_id is not None else None
    return project.owner_id if project is not None else None


def _can_access(user: UserOut, owner_id: Optional[int]) -> bool:
    """Admins access anything; everyone else only their own resources."""
    return user.role_key == "admin" or (owner_id is not None and owner_id == user.id)


def _owned_study_or_error(db, models, study_id: int, user: UserOut):
    """Fetch a study enforcing ownership via its project owner.

    404 when the study does not exist; 403 when it exists but the caller is not
    the owner (and not an admin). Never leaks another user's study contents.
    """
    study = db.get(models.FeasibilityStudy, study_id)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    owner_id = _project_owner_id(db, models, study.project_id)
    if not _can_access(user, owner_id):
        raise HTTPException(status_code=403, detail="Not authorized for this study")
    return study


class StudyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    industry: str = Field(..., min_length=1, max_length=100)
    investment: float = Field(..., gt=0)
    study_type: str = Field(default="general", max_length=50)
    project_id: Optional[int] = None


class StepIn(BaseModel):
    step: int = Field(..., ge=1, le=6)
    data: dict = Field(default_factory=dict)
    expected_revision: Optional[int] = Field(default=None, ge=1)


class ComputeIn(BaseModel):
    annual_cash_flows: List[float] = Field(..., min_length=1)
    discount_rate: float = Field(default=0.10, ge=0, le=1)


class StudyOut(BaseModel):
    id: int
    project_id: int
    title: str
    study_type: str
    status: str
    current_step: int
    revision: int
    payload: dict
    result: Optional[dict] = None

    model_config = {"from_attributes": True}


def _latest_result(db, models, study_id: int) -> Optional[dict]:
    row = (
        db.query(models.FinancialResult)
        .filter_by(study_id=study_id)
        .order_by(models.FinancialResult.id.desc())
        .first()
    )
    if row is None:
        return None
    detail = row.detail or {}
    return {
        "roi_percent": row.roi,
        "payback_years": row.payback_years,
        "npv": row.npv,
        "irr_percent": (row.irr * 100) if row.irr is not None else None,
        "break_even": row.break_even,
        "verdict": row.verdict,
        "sensitivity": detail.get("sensitivity", []),
    }


def _to_out(models, study, result: Optional[dict]) -> StudyOut:
    return StudyOut(
        id=study.id,
        project_id=study.project_id,
        title=study.title,
        study_type=study.study_type,
        status=study.status,
        current_step=study.current_step,
        revision=study.revision,
        payload=study.payload or {},
        result=result,
    )


@router.post("/", response_model=StudyOut, status_code=201)
def create_study(data: StudyCreate, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        project_id = data.project_id
        if project_id is None:
            project = models.Project(
                name=data.title,
                industry=data.industry,
                investment=data.investment,
                stage="idea",
                workflow_status="feasibility",
                owner_id=user.id,
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            project_id = project.id
        else:
            project = db.get(models.Project, project_id)
            if project is None:
                raise HTTPException(status_code=404, detail="Project not found")
            # A study may only be attached to a project the caller owns.
            if not _can_access(user, project.owner_id):
                raise HTTPException(status_code=403, detail="Not authorized for this project")

            # A project is the persistent root aggregate and has one study.
            # Returning the existing resource makes retries and double-clicks
            # idempotent without creating duplicate customer records.
            existing = (
                db.query(models.FeasibilityStudy)
                .filter(models.FeasibilityStudy.project_id == project_id)
                .order_by(models.FeasibilityStudy.id.asc())
                .first()
            )
            if existing is not None:
                return _to_out(models, existing, _latest_result(db, models, existing.id))

        study = models.FeasibilityStudy(
            project_id=project_id,
            title=data.title,
            study_type=data.study_type,
            status="draft",
            current_step=1,
            payload={"industry": data.industry, "investment": data.investment},
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        return _to_out(models, study, None)
    finally:
        db.close()


@router.get("/", response_model=List[StudyOut])
def list_studies(project_id: Optional[int] = None, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        # Only the caller's own studies (admins see all). Ownership is derived
        # from the parent project owner via a join.
        q = db.query(models.FeasibilityStudy).join(
            models.Project, models.FeasibilityStudy.project_id == models.Project.id
        )
        if user.role_key != "admin":
            q = q.filter(models.Project.owner_id == user.id)
        if project_id is not None:
            q = q.filter(models.FeasibilityStudy.project_id == project_id)
        studies = q.order_by(models.FeasibilityStudy.id.desc()).limit(100).all()
        return [_to_out(models, s, _latest_result(db, models, s.id)) for s in studies]
    finally:
        db.close()


@router.get("/{study_id}", response_model=StudyOut)
def get_study(study_id: int, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        study = _owned_study_or_error(db, models, study_id, user)
        return _to_out(models, study, _latest_result(db, models, study.id))
    finally:
        db.close()


@router.patch("/{study_id}/step", response_model=StudyOut)
def save_step(study_id: int, body: StepIn, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        study = _owned_study_or_error(db, models, study_id, user)
        if body.expected_revision is not None and study.revision != body.expected_revision:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "study_revision_conflict",
                    "message": "The study changed in another session. Reload before saving.",
                    "current_revision": study.revision,
                },
            )
        payload = dict(study.payload or {})
        payload[f"step_{body.step}"] = body.data
        study.payload = payload
        study.current_step = max(study.current_step, body.step)
        study.revision += 1
        if study.status == "draft" and body.step >= 6:
            study.status = "in_review"
        db.add(study)
        db.commit()
        db.refresh(study)
        return _to_out(models, study, _latest_result(db, models, study.id))
    finally:
        db.close()


@router.post("/{study_id}/compute", response_model=StudyOut)
def compute(study_id: int, body: ComputeIn, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        study = _owned_study_or_error(db, models, study_id, user)

        investment = float((study.payload or {}).get("investment") or 0) or 0.0
        if investment <= 0:
            project = db.get(models.Project, study.project_id)
            investment = float(project.investment) if project else 0.0
        if investment <= 0:
            raise HTTPException(status_code=422, detail="Investment amount is required before computing.")

        res = evaluate_feasibility(investment, body.annual_cash_flows, body.discount_rate)
        sens = sensitivity_analysis(investment, body.annual_cash_flows, body.discount_rate)

        result = models.FinancialResult(
            study_id=study.id,
            roi=res.roi_percent,
            npv=res.npv_value,
            irr=res.irr_value,
            payback_years=res.payback_years,
            verdict=res.verdict,
            detail={
                "sensitivity": sens,
                "discount_rate": body.discount_rate,
                "annual_cash_flows": body.annual_cash_flows,
            },
        )
        db.add(result)
        study.status = "completed"
        study.current_step = max(study.current_step, 5)
        db.add(study)
        db.commit()
        db.refresh(study)
        return _to_out(models, study, _latest_result(db, models, study.id))
    finally:
        db.close()
