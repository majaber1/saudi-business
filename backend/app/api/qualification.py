from __future__ import annotations

"""
Business Qualification & Readiness | التأهيل والجاهزية  (Saudi Business).

Business-facing readiness API for SMEs / establishments: qualification
profiles, per-requirement status tracking, readiness scoring by category,
actionable bilingual recommendations, and a *summarized* request for a deeper
external Multazim (institutional GRC) assessment.

This module intentionally does NOT implement institutional GRC (ISO 27001
control management, NCA/SAMA/PDPL control libraries, enterprise evidence vault,
enterprise risk register, internal-audit programs, regulatory oversight, full
policy lifecycle, corrective-action enterprise workflows). Those belong to the
separate Multazim product. Only the summarized cross-product hand-off lives
here.

Replaces the lightweight, misleadingly-named multazim.py Saudi Business router.
The MultazimRequirement catalog model is preserved (still used by the admin
dashboard) but is no longer exposed under a "multazim" business API.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, get_current_user, require_roles

router = APIRouter(prefix="/api/qualification", tags=["qualification"])

# --- Domain constants -------------------------------------------------------

# Business-facing readiness categories (NOT GRC control families).
CATEGORIES = (
    "tender",
    "funding",
    "licenses",
    "certificates",
    "saudization",
    "commercial",
    "operational",
    "eligibility",
)

CATEGORY_LABELS = {
    "tender": {"en": "Tender readiness", "ar": "جاهزية المنافسات"},
    "funding": {"en": "Funding readiness", "ar": "جاهزية التمويل"},
    "licenses": {"en": "Licenses", "ar": "التراخيص"},
    "certificates": {"en": "Certificates", "ar": "الشهادات"},
    "saudization": {"en": "Saudization / workforce", "ar": "السعودة والقوى العاملة"},
    "commercial": {"en": "Commercial readiness", "ar": "الجاهزية التجارية"},
    "operational": {"en": "Operational readiness", "ar": "الجاهزية التشغيلية"},
    "eligibility": {"en": "Eligibility", "ar": "الأهلية"},
}

# Requirement status values.
STATUSES = ("missing", "pending", "valid", "expired", "not_applicable")

# Contribution of each status to the readiness score (0..1).
STATUS_WEIGHT = {
    "valid": 1.0,
    "pending": 0.5,
    "expired": 0.0,
    "missing": 0.0,
    "not_applicable": None,  # excluded from scoring entirely
}


def _require_db() -> None:
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Persistence is disabled in demo mode.")


# --- Pydantic schemas -------------------------------------------------------

class RequirementIn(BaseModel):
    category: str
    title_en: str
    title_ar: str
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    authority: Optional[str] = None
    is_mandatory: bool = True
    status: str = "missing"
    weight: float = 1.0
    document_id: Optional[int] = None
    declared_reference: Optional[str] = None
    expires_at: Optional[datetime] = None
    source_url: Optional[str] = None


class RequirementUpdate(BaseModel):
    status: Optional[str] = None
    document_id: Optional[int] = None
    declared_reference: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_mandatory: Optional[bool] = None
    weight: Optional[float] = None


class RequirementOut(RequirementIn):
    id: int
    profile_id: int


class ProfileIn(BaseModel):
    company_name_en: Optional[str] = None
    company_name_ar: Optional[str] = None
    cr_number: Optional[str] = Field(default=None, max_length=50)
    sector: Optional[str] = None
    company_size: Optional[str] = None
    saudization_rate: Optional[float] = None
    project_id: Optional[int] = None


class ProfileOut(ProfileIn):
    id: int
    owner_id: Optional[int]
    overall_score: float
    category_scores: dict
    recommendations: list


class ScoreOut(BaseModel):
    profile_id: int
    overall_score: float
    category_scores: dict
    missing: List[dict]  # bilingual missing-document analysis


class MultazimRequestIn(BaseModel):
    scope: Optional[str] = None  # iso27001 | nca | pdpl | ...


class MultazimRequestOut(BaseModel):
    id: int
    profile_id: int
    scope: Optional[str]
    status: str
    summary_score: Optional[float]
    summary_en: Optional[str]
    summary_ar: Optional[str]



# --- Serializers (call while the session is still open) --------------------

def _profile_out(p):
    return ProfileOut(
        id=p.id,
        owner_id=p.owner_id,
        project_id=p.project_id,
        company_name_en=p.company_name_en,
        company_name_ar=p.company_name_ar,
        cr_number=p.cr_number,
        sector=p.sector,
        company_size=p.company_size,
        saudization_rate=p.saudization_rate,
        overall_score=p.overall_score,
        category_scores=p.category_scores or {},
        recommendations=p.recommendations or [],
    )


def _requirement_out(r):
    return RequirementOut(
        id=r.id,
        profile_id=r.profile_id,
        category=r.category,
        title_en=r.title_en,
        title_ar=r.title_ar,
        description_en=r.description_en,
        description_ar=r.description_ar,
        authority=r.authority,
        is_mandatory=r.is_mandatory,
        status=r.status,
        weight=r.weight,
        document_id=r.document_id,
        declared_reference=r.declared_reference,
        expires_at=r.expires_at,
        source_url=r.source_url,
    )


def _multazim_out(m):
    return MultazimRequestOut(
        id=m.id,
        profile_id=m.profile_id,
        scope=m.scope,
        status=m.status,
        summary_score=m.summary_score,
        summary_en=m.summary_en,
        summary_ar=m.summary_ar,
    )


# --- Scoring & recommendations ---------------------------------------------

def _expire_overdue(reqs) -> None:
    """Mark 'valid' requirements whose expiry has passed as 'expired' (in place)."""
    # Existing migrations use timezone-naive UTC columns. Start from an aware
    # UTC clock, then remove tzinfo only at the persistence comparison boundary.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for r in reqs:
        if r.status == "valid" and r.expires_at and r.expires_at < now:
            r.status = "expired"


def _compute_scores(reqs):
    """Return (overall_score, category_scores) on a 0..100 scale.

    'not_applicable' requirements are excluded. Score is the weighted average of
    status contributions. Empty categories are omitted.
    """
    cat_num = {}
    cat_den = {}
    for r in reqs:
        contrib = STATUS_WEIGHT.get(r.status)
        if contrib is None:  # not_applicable
            continue
        w = float(r.weight or 1.0)
        cat_num[r.category] = cat_num.get(r.category, 0.0) + contrib * w
        cat_den[r.category] = cat_den.get(r.category, 0.0) + w

    category_scores = {
        c: round(100.0 * cat_num[c] / cat_den[c], 1)
        for c in cat_den
        if cat_den[c] > 0
    }
    if category_scores:
        overall = round(sum(category_scores.values()) / len(category_scores), 1)
    else:
        overall = 0.0
    return overall, category_scores


def _recommendations(reqs, category_scores):
    """Actionable bilingual recommendations derived from requirement gaps."""
    recs = []
    for r in reqs:
        if r.status in ("missing", "expired") and r.is_mandatory:
            label = CATEGORY_LABELS.get(r.category, {"en": r.category, "ar": r.category})
            action_en = "Obtain" if r.status == "missing" else "Renew"
            action_ar = "استخراج" if r.status == "missing" else "تجديد"
            recs.append({
                "category": r.category,
                "priority": "high",
                "requirement_id": r.id,
                "en": action_en + " '" + r.title_en + "' (" + label["en"] + ").",
                "ar": action_ar + " '" + r.title_ar + "' (" + label["ar"] + ").",
            })
    for cat, score in sorted(category_scores.items(), key=lambda kv: kv[1]):
        if score < 60:
            label = CATEGORY_LABELS.get(cat, {"en": cat, "ar": cat})
            recs.append({
                "category": cat,
                "priority": "medium",
                "en": "Improve " + label["en"] + " (currently " + str(score) + "%).",
                "ar": "تحسين " + label["ar"] + " (حاليًا " + str(score) + "%).",
            })
    return recs


def _missing_analysis(reqs):
    """Bilingual missing / expired document analysis."""
    out = []
    for r in reqs:
        if r.status in ("missing", "expired"):
            out.append({
                "requirement_id": r.id,
                "category": r.category,
                "status": r.status,
                "is_mandatory": r.is_mandatory,
                "title_en": r.title_en,
                "title_ar": r.title_ar,
            })
    return out


def _refresh_profile(db, profile) -> None:
    """Recompute and persist scores + recommendations for a profile."""
    _expire_overdue(profile.requirements)
    overall, cat_scores = _compute_scores(profile.requirements)
    profile.overall_score = overall
    profile.category_scores = cat_scores
    profile.recommendations = _recommendations(profile.requirements, cat_scores)
    db.commit()


# --- Ownership helper -------------------------------------------------------

def _get_owned_profile(db, models, profile_id: int, user: UserOut):
    """Fetch a profile enforcing ownership (admins may access any)."""
    obj = db.get(models.QualificationProfile, profile_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found.")
    if user.role_key != "admin" and obj.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not the owner of this profile.")
    return obj


# --- Metadata endpoints (public read) --------------------------------------

@router.get("/categories")
def list_categories():
    """Readiness categories with bilingual labels (static; safe public read)."""
    return [
        {"key": c, "en": CATEGORY_LABELS[c]["en"], "ar": CATEGORY_LABELS[c]["ar"]}
        for c in CATEGORIES
    ]


@router.get("/statuses", response_model=List[str])
def list_statuses():
    """Allowed requirement status values."""
    return list(STATUSES)


# --- Profile CRUD (owner-scoped) -------------------------------------------

@router.get("/", response_model=List[ProfileOut])
def list_profiles(user: UserOut = Depends(get_current_user)):
    """List the caller's qualification profiles (admins see all)."""
    _require_db()
    from app import models
    db = SessionLocal()
    try:
        q = db.query(models.QualificationProfile)
        if user.role_key != "admin":
            q = q.filter(models.QualificationProfile.owner_id == user.id)
        return [_profile_out(p) for p in q.order_by(models.QualificationProfile.id).all()]
    finally:
        db.close()


@router.post("/", response_model=ProfileOut, status_code=201)
def create_profile(data: ProfileIn, user: UserOut = Depends(get_current_user)):
    """Create a qualification profile owned by the caller."""
    _require_db()
    from app import models
    from app.api.auth import _audit
    db = SessionLocal()
    try:
        obj = models.QualificationProfile(owner_id=user.id, **data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        _audit(db, user.id, "create", "qualification_profile", obj.id)
        return _profile_out(obj)
    finally:
        db.close()


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: int, user: UserOut = Depends(get_current_user)):
    _require_db()
    from app import models
    db = SessionLocal()
    try:
        return _profile_out(_get_owned_profile(db, models, profile_id, user))
    finally:
        db.close()


# --- Requirements (owner-scoped) -------------------------------------------

@router.get("/{profile_id}/requirements", response_model=List[RequirementOut])
def list_requirements(profile_id: int, user: UserOut = Depends(get_current_user),
                      category: Optional[str] = None, status: Optional[str] = None):
    _require_db()
    from app import models
    db = SessionLocal()
    try:
        _get_owned_profile(db, models, profile_id, user)
        q = db.query(models.QualificationRequirement).filter(
            models.QualificationRequirement.profile_id == profile_id
        )
        if category:
            q = q.filter(models.QualificationRequirement.category == category)
        if status:
            q = q.filter(models.QualificationRequirement.status == status)
        rows = q.order_by(models.QualificationRequirement.category,
                          models.QualificationRequirement.id).all()
        return [_requirement_out(r) for r in rows]
    finally:
        db.close()


@router.post("/{profile_id}/requirements", response_model=RequirementOut, status_code=201)
def add_requirement(profile_id: int, data: RequirementIn,
                    user: UserOut = Depends(get_current_user)):
    _require_db()
    if data.category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown category '" + data.category + "'.")
    if data.status not in STATUSES:
        raise HTTPException(status_code=422, detail="Unknown status '" + data.status + "'.")
    from app import models
    from app.api.auth import _audit
    db = SessionLocal()
    try:
        profile = _get_owned_profile(db, models, profile_id, user)
        obj = models.QualificationRequirement(profile_id=profile.id, **data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        db.refresh(profile)
        _refresh_profile(db, profile)
        _audit(db, user.id, "create", "qualification_requirement", obj.id)
        return _requirement_out(obj)
    finally:
        db.close()


@router.patch("/{profile_id}/requirements/{req_id}", response_model=RequirementOut)
def update_requirement(profile_id: int, req_id: int, data: RequirementUpdate,
                       user: UserOut = Depends(get_current_user)):
    _require_db()
    from app import models
    from app.api.auth import _audit
    db = SessionLocal()
    try:
        profile = _get_owned_profile(db, models, profile_id, user)
        obj = db.get(models.QualificationRequirement, req_id)
        if not obj or obj.profile_id != profile.id:
            raise HTTPException(status_code=404, detail="Requirement not found.")
        payload = data.model_dump(exclude_unset=True)
        if "status" in payload and payload["status"] not in STATUSES:
            raise HTTPException(status_code=422, detail="Invalid status.")
        for k, v in payload.items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        db.refresh(profile)
        _refresh_profile(db, profile)
        _audit(db, user.id, "update", "qualification_requirement", obj.id)
        return _requirement_out(obj)
    finally:
        db.close()


# --- Scores & recommendations ----------------------------------------------

@router.get("/{profile_id}/score", response_model=ScoreOut)
def get_score(profile_id: int, user: UserOut = Depends(get_current_user)):
    """Readiness scores by category + overall + missing-document analysis."""
    _require_db()
    from app import models
    db = SessionLocal()
    try:
        profile = _get_owned_profile(db, models, profile_id, user)
        _refresh_profile(db, profile)
        db.refresh(profile)
        return ScoreOut(
            profile_id=profile.id,
            overall_score=profile.overall_score,
            category_scores=profile.category_scores or {},
            missing=_missing_analysis(profile.requirements),
        )
    finally:
        db.close()


@router.get("/{profile_id}/recommendations")
def get_recommendations(profile_id: int, user: UserOut = Depends(get_current_user)):
    """Actionable bilingual recommendations for the profile."""
    _require_db()
    from app import models
    db = SessionLocal()
    try:
        profile = _get_owned_profile(db, models, profile_id, user)
        _refresh_profile(db, profile)
        db.refresh(profile)
        return {"profile_id": profile.id, "recommendations": profile.recommendations or []}
    finally:
        db.close()


# --- Multazim hand-off (summarized only) -----------------------------------

@router.post("/{profile_id}/multazim-request", response_model=MultazimRequestOut, status_code=201)
def request_multazim_assessment(profile_id: int, data: MultazimRequestIn,
                                user: UserOut = Depends(get_current_user)):
    """Request a deeper external Multazim (institutional GRC) assessment.

    Saudi Business only records the request. The full GRC assessment is performed
    by the separate Multazim product; only a summarized result is stored back
    (see the summary_* fields), never the full control/evidence set.
    """
    _require_db()
    from app import models
    from app.api.auth import _audit
    db = SessionLocal()
    try:
        profile = _get_owned_profile(db, models, profile_id, user)
        obj = models.MultazimAssessmentRequest(
            profile_id=profile.id,
            requested_by=user.id,
            scope=data.scope,
            status="requested",
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        _audit(db, user.id, "create", "multazim_assessment_request", obj.id)
        return _multazim_out(obj)
    finally:
        db.close()


@router.get("/{profile_id}/multazim-request", response_model=List[MultazimRequestOut])
def list_multazim_requests(profile_id: int, user: UserOut = Depends(get_current_user)):
    """List summarized Multazim assessment requests/results for the profile."""
    _require_db()
    from app import models
    db = SessionLocal()
    try:
        _get_owned_profile(db, models, profile_id, user)
        rows = (
            db.query(models.MultazimAssessmentRequest)
            .filter(models.MultazimAssessmentRequest.profile_id == profile_id)
            .order_by(models.MultazimAssessmentRequest.id)
            .all()
        )
        return [_multazim_out(m) for m in rows]
    finally:
        db.close()

