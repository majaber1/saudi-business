"""
ORM models for Saudi Business | سعودي بزنس.

Types are kept portable (generic String/Integer/Float/JSON) so the same models
run on SQLite (tests) and PostgreSQL (production). Every table has created_at /
updated_at timestamps and appropriate indexes and foreign keys.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200))
    cr_number: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100))

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    projects: Mapped[list["Project"]] = relationship(back_populates="organization")


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(100), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    locale: Mapped[str] = mapped_column(String(5), default="ar")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    role_key: Mapped[str] = mapped_column(String(50), ForeignKey("roles.key"), default="entrepreneur")
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"))

    organization: Mapped[Optional["Organization"]] = relationship(back_populates="users")
    projects: Mapped[list["Project"]] = relationship(back_populates="owner")


class AccountToken(TimestampMixin, Base):
    """Single-use, hashed email-verification or password-reset token."""

    __tablename__ = "account_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    investment: Mapped[float] = mapped_column(Float, nullable=False)
    stage: Mapped[str] = mapped_column(String(30), default="idea")
    workflow_status: Mapped[str] = mapped_column(String(30), default="created")
    # Soft-archive: archived projects are hidden from the default list but
    # never hard-deleted, so dependent feasibility studies / reports are not
    # orphaned. is_archived is the authoritative flag; archived_at records when.
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"))

    owner: Mapped[Optional["User"]] = relationship(back_populates="projects")
    organization: Mapped[Optional["Organization"]] = relationship(back_populates="projects")
    studies: Mapped[list["FeasibilityStudy"]] = relationship(back_populates="project")


class FeasibilityStudy(TimestampMixin, Base):
    __tablename__ = "feasibility_studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    study_type: Mapped[str] = mapped_column(String(50), default="general")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="studies")
    assumptions: Mapped[list["FinancialAssumption"]] = relationship(back_populates="study")
    results: Mapped[list["FinancialResult"]] = relationship(back_populates="study")
    scenarios: Mapped[list["SensitivityScenario"]] = relationship(back_populates="study")
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(back_populates="study")
    study_assumptions: Mapped[list["StudyAssumption"]] = relationship(
        back_populates="study", foreign_keys="StudyAssumption.study_id"
    )
    business_profile: Mapped[Optional["BusinessProfile"]] = relationship(back_populates="study", uselist=False)


class FinancialAssumption(TimestampMixin, Base):
    __tablename__ = "financial_assumptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), index=True, nullable=False)
    capex: Mapped[float] = mapped_column(Float, default=0.0)
    opex_annual: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_year1: Mapped[float] = mapped_column(Float, default=0.0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.0)
    discount_rate: Mapped[float] = mapped_column(Float, default=0.10)
    horizon_years: Mapped[int] = mapped_column(Integer, default=5)

    study: Mapped["FeasibilityStudy"] = relationship(back_populates="assumptions")


class FinancialResult(TimestampMixin, Base):
    __tablename__ = "financial_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), index=True, nullable=False)
    roi: Mapped[Optional[float]] = mapped_column(Float)
    npv: Mapped[Optional[float]] = mapped_column(Float)
    irr: Mapped[Optional[float]] = mapped_column(Float)
    payback_years: Mapped[Optional[float]] = mapped_column(Float)
    break_even: Mapped[Optional[float]] = mapped_column(Float)
    verdict: Mapped[Optional[str]] = mapped_column(String(30))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)

    study: Mapped["FeasibilityStudy"] = relationship(back_populates="results")


class SensitivityScenario(TimestampMixin, Base):
    __tablename__ = "sensitivity_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50))  # conservative | base | optimistic
    revenue_delta: Mapped[float] = mapped_column(Float, default=0.0)
    npv: Mapped[Optional[float]] = mapped_column(Float)
    irr: Mapped[Optional[float]] = mapped_column(Float)

    study: Mapped["FeasibilityStudy"] = relationship(back_populates="scenarios")


class BusinessProfile(TimestampMixin, Base):
    """Structured, reusable business facts for a Study (one profile per study).

    Both the feasibility flow and the funding flow (Entry 3: "أبحث عن تمويل")
    read/write this same row, so a user who already described their business
    is never asked to re-enter it. Distinct from Project (name/industry/
    investment/stage, the lightweight root record) and from the later
    CompanyFinancialProfile (period financial statements for existing
    businesses) -- this is the qualitative "what is this business" record.
    """

    __tablename__ = "business_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), unique=True, index=True, nullable=False)

    business_activity: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    customer_segment: Mapped[Optional[str]] = mapped_column(String(200))

    capacity_value: Mapped[Optional[float]] = mapped_column(Float)
    capacity_unit: Mapped[Optional[str]] = mapped_column(String(50))

    legal_entity_type: Mapped[Optional[str]] = mapped_column(String(50))
    ownership_notes: Mapped[Optional[str]] = mapped_column(Text)

    is_existing_business: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    company_age_years: Mapped[Optional[float]] = mapped_column(Float)
    current_revenue: Mapped[Optional[float]] = mapped_column(Float)

    study: Mapped["FeasibilityStudy"] = relationship(back_populates="business_profile")


class EvidenceItem(TimestampMixin, Base):
    """A single sourced fact attached to a study, with full provenance.

    Every factual claim a study's analysis, report, or AI advisor relies on
    must trace back to a row here (or be recorded as an explicit
    StudyAssumption). authority_level and source_type together let the UI/API
    tell a VERIFIED_FACT apart from an UNVERIFIED claim; both are always
    computed/validated server-side (see app.services.source_registry) so
    client input can never self-certify as official evidence.
    """

    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), index=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # official_statistic|regulation|funding_program|market_report|news|survey|user_document|ai_inference|other
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_name: Mapped[Optional[str]] = mapped_column(String(200))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    publisher: Mapped[Optional[str]] = mapped_column(String(200))

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    value_number: Mapped[Optional[float]] = mapped_column(Float)
    value_text: Mapped[Optional[str]] = mapped_column(String(300))
    unit: Mapped[Optional[str]] = mapped_column(String(50))

    geography: Mapped[Optional[str]] = mapped_column(String(100))
    sector: Mapped[Optional[str]] = mapped_column(String(100))

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    # Temporal validity: when this fact is/was actually in effect, distinct
    # from when it was published or retrieved. superseded_by_id lets a newer
    # snapshot supersede an older one without deleting audit history.
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime)
    superseded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("evidence_items.id"))

    confidence: Mapped[str] = mapped_column(String(20), default="medium")  # low|medium|high
    # verified|user_provided|unverified -- never "fact" without one of these.
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified", nullable=False)
    # OFFICIAL_PRIMARY|OFFICIAL_SECONDARY|REGULATOR|REPUTABLE_INSTITUTION|
    # COMMERCIAL_SOURCE|USER_DOCUMENT|AI_INFERENCE|UNVERIFIED
    authority_level: Mapped[str] = mapped_column(String(30), default="UNVERIFIED", nullable=False)

    # The actual retrieved text/quote the claim is based on, plus a checksum
    # so later edits/staleness are detectable.
    snapshot_text: Mapped[Optional[str]] = mapped_column(Text)
    snapshot_hash: Mapped[Optional[str]] = mapped_column(String(64))

    study: Mapped["FeasibilityStudy"] = relationship(back_populates="evidence_items")


class StudyAssumption(TimestampMixin, Base):
    """A versioned, provenance-tagged assumption used in a study's analysis.

    Distinct from EvidenceItem: an assumption is a value the study *uses*
    (rent, headcount, utilization...), which may or may not be derived from
    evidence. Writing a new assumption for a key that already has an active
    row retires the old row (is_active=False) and bumps version rather than
    overwriting it, so the assumption's history stays inspectable.
    """

    __tablename__ = "study_assumptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), index=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    evidence_id: Mapped[Optional[int]] = mapped_column(ForeignKey("evidence_items.id"))

    key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    label_en: Mapped[str] = mapped_column(String(200), nullable=False)
    label_ar: Mapped[str] = mapped_column(String(200), nullable=False)

    value_number: Mapped[Optional[float]] = mapped_column(Float)
    value_text: Mapped[Optional[str]] = mapped_column(String(300))
    unit: Mapped[Optional[str]] = mapped_column(String(50))

    # USER|EVIDENCE_DERIVED|AI_SUGGESTED|DEFAULT -- AI_SUGGESTED must never be
    # silently treated as a verified market fact by any downstream consumer.
    origin: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(20), default="medium")
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    study: Mapped["FeasibilityStudy"] = relationship(back_populates="study_assumptions", foreign_keys=[study_id])
    evidence: Mapped[Optional["EvidenceItem"]] = relationship()


class FundingProgram(TimestampMixin, Base):
    __tablename__ = "funding_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    organization: Mapped[Optional[str]] = mapped_column(String(150))
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_ar: Mapped[Optional[str]] = mapped_column(Text)
    funding_type: Mapped[Optional[str]] = mapped_column(String(80))
    eligibility: Mapped[dict] = mapped_column(JSON, default=dict)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    application_url: Mapped[Optional[str]] = mapped_column(String(500))
    last_verified: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verification_status: Mapped[str] = mapped_column(String(30), default="requires_verification")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class FundingMatch(TimestampMixin, Base):
    __tablename__ = "funding_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    program_key: Mapped[str] = mapped_column(String(50), ForeignKey("funding_programs.key"), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    missing: Mapped[list] = mapped_column(JSON, default=list)


class IdeaBankEntry(TimestampMixin, Base):
    __tablename__ = "idea_bank_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), index=True)
    summary_en: Mapped[Optional[str]] = mapped_column(Text)
    summary_ar: Mapped[Optional[str]] = mapped_column(Text)
    problem: Mapped[Optional[str]] = mapped_column(Text)
    solution: Mapped[Optional[str]] = mapped_column(Text)
    revenue_model: Mapped[Optional[str]] = mapped_column(String(200))
    investment_min: Mapped[Optional[float]] = mapped_column(Float)
    investment_max: Mapped[Optional[float]] = mapped_column(Float)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))
    time_to_launch: Mapped[Optional[str]] = mapped_column(String(50))
    vision2030_alignment: Mapped[Optional[str]] = mapped_column(String(200))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="published")
    source: Mapped[Optional[str]] = mapped_column(String(300))


class FranchiseOpportunity(TimestampMixin, Base):
    __tablename__ = "franchise_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand: Mapped[str] = mapped_column(String(200), nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_ar: Mapped[Optional[str]] = mapped_column(Text)
    sector: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[Optional[str]] = mapped_column(String(80))
    regions: Mapped[list] = mapped_column(JSON, default=list)
    investment_min: Mapped[Optional[float]] = mapped_column(Float)
    investment_max: Mapped[Optional[float]] = mapped_column(Float)
    franchise_fee: Mapped[Optional[float]] = mapped_column(Float)
    royalty_model: Mapped[Optional[str]] = mapped_column(String(150))
    required_space: Mapped[Optional[str]] = mapped_column(String(100))
    application_url: Mapped[Optional[str]] = mapped_column(String(500))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    verification_status: Mapped[str] = mapped_column(String(30), default="demo")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class InvestmentOpportunity(TimestampMixin, Base):
    """Investor-facing catalog: projects/ventures open for outside investment.

    Distinct from Project (a founder's own feasibility workspace) -- an
    opportunity is what an investor browses and filters by ticket size.
    expected_return_percent is always an indicative, source-labeled estimate,
    never presented as a guarantee (see Source of truth README section 6).
    """

    __tablename__ = "investment_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), index=True)
    summary_en: Mapped[Optional[str]] = mapped_column(Text)
    summary_ar: Mapped[Optional[str]] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(String(30), default="mvp")  # idea|mvp|early_revenue|growth
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")  # low|medium|high
    investment_min: Mapped[Optional[float]] = mapped_column(Float, index=True)
    investment_max: Mapped[Optional[float]] = mapped_column(Float)
    expected_return_percent: Mapped[Optional[float]] = mapped_column(Float)
    funding_goal: Mapped[Optional[float]] = mapped_column(Float)
    funding_committed: Mapped[Optional[float]] = mapped_column(Float, default=0)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    verification_status: Mapped[str] = mapped_column(String(30), default="demo")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MultazimRequirement(TimestampMixin, Base):
    __tablename__ = "multazim_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_ar: Mapped[Optional[str]] = mapped_column(Text)
    authority: Mapped[Optional[str]] = mapped_column(String(150))
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    # Optional link into a specific study (e.g. an existing company's
    # financial statements attached to a funding study). Nullable/additive so
    # existing project-only documents (funding proposal uploads) are unaffected.
    study_id: Mapped[Optional[int]] = mapped_column(ForeignKey("feasibility_studies.id"), index=True)
    # financial_statement|bank_statement|cr_document|asset_schedule|
    # debt_schedule|guarantee|project_proposal|other
    document_type: Mapped[Optional[str]] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    storage_ref: Mapped[Optional[str]] = mapped_column(String(500))

    extracted_facts: Mapped[list["ExtractedFinancialFact"]] = relationship(back_populates="document")


class ExtractedFinancialFact(TimestampMixin, Base):
    """A structured fact traced to a specific uploaded document.

    There is currently no automated OCR/document-understanding integration
    configured in this environment (see docs/architecture/CURRENT_STATE_AUDIT.md);
    every row here is entered by a human who read the source document, which
    is why extraction_status defaults to "user_entered" rather than an
    automated-confidence tier. The schema is forward-compatible with an
    automated pipeline (extraction_status/confidence are free strings, not a
    DB enum) so that capability can be added later without a migration --
    but nothing in this codebase currently claims to parse documents
    automatically, and a low-confidence row must never be presented as a
    verified financial fact (see review_status).
    """

    __tablename__ = "extracted_financial_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), index=True, nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value_number: Mapped[Optional[float]] = mapped_column(Float)
    value_text: Mapped[Optional[str]] = mapped_column(String(300))
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    period: Mapped[Optional[str]] = mapped_column(String(50))
    source_location: Mapped[Optional[str]] = mapped_column(String(200))

    extraction_status: Mapped[str] = mapped_column(String(30), default="user_entered", nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    review_status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False)

    document: Mapped["Document"] = relationship(back_populates="extracted_facts")
    study: Mapped["FeasibilityStudy"] = relationship()


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(ForeignKey("feasibility_studies.id"), index=True, nullable=False)
    fmt: Mapped[str] = mapped_column(String(10))  # pdf | docx
    locale: Mapped[str] = mapped_column(String(5), default="ar")
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    storage_ref: Mapped[Optional[str]] = mapped_column(String(500))


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (UniqueConstraint("id", name="uq_audit_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


# ---------------------------------------------------------------------------
# Business Qualification & Readiness | التأهيل والجاهزية  (Saudi Business)
#
# Lightweight, business-facing readiness tracking for SMEs / establishments:
# qualification profiles, per-requirement status, and a *summarized* request
# for a deeper Multazim (institutional GRC) assessment. This intentionally does
# NOT implement full GRC (control libraries, evidence vault, risk register,
# internal audit, policy lifecycle) — that lives in the separate Multazim
# product. Only the summarized cross-product hand-off is modeled here.
# ---------------------------------------------------------------------------


class QualificationProfile(TimestampMixin, Base):
    """A company's Business Qualification & Readiness profile.

    Owned by a user (and optionally scoped to a project). Aggregates readiness
    across categories such as tender readiness, funding readiness, Saudization,
    and commercial/operational readiness.
    """

    __tablename__ = "qualification_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)

    company_name_en: Mapped[Optional[str]] = mapped_column(String(200))
    company_name_ar: Mapped[Optional[str]] = mapped_column(String(200))
    cr_number: Mapped[Optional[str]] = mapped_column(String(50))  # Commercial Registration
    sector: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(30))  # micro|small|medium|large
    saudization_rate: Mapped[Optional[float]] = mapped_column(Float)  # 0..1

    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    category_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)

    owner: Mapped[Optional["User"]] = relationship()
    requirements: Mapped[list["QualificationRequirement"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class QualificationRequirement(TimestampMixin, Base):
    """A single eligibility / readiness requirement within a profile.

    Categories (business-facing, not GRC controls): tender, funding, licenses,
    certificates, saudization, commercial, operational, eligibility.
    Status is one of: missing | pending | valid | expired | not_applicable.
    """

    __tablename__ = "qualification_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("qualification_profiles.id"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), index=True)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_ar: Mapped[Optional[str]] = mapped_column(Text)
    authority: Mapped[Optional[str]] = mapped_column(String(150))
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="missing")
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    document_id: Mapped[Optional[int]] = mapped_column(ForeignKey("documents.id"))
    declared_reference: Mapped[Optional[str]] = mapped_column(String(300))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))

    profile: Mapped["QualificationProfile"] = relationship(back_populates="requirements")


class MultazimAssessmentRequest(TimestampMixin, Base):
    """A request from Saudi Business for a deeper external Multazim assessment.

    Saudi Business only stores the request and a *summarized* result payload
    (score + short bilingual summary). It never stores the full institutional
    GRC assessment (controls, evidence, findings) — that stays in Multazim.
    """

    __tablename__ = "multazim_assessment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("qualification_profiles.id"), index=True, nullable=False
    )
    requested_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    scope: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="requested")

    summary_score: Mapped[Optional[float]] = mapped_column(Float)
    summary_en: Mapped[Optional[str]] = mapped_column(Text)
    summary_ar: Mapped[Optional[str]] = mapped_column(Text)


class SalesLead(TimestampMixin, Base):
    """A captured sales/investor-interest lead from the public Pricing page.

    Intentionally NOT a payment or subscription record -- Saudi Business does
    not process payments. This is a contact-capture inbox for a human sales
    follow-up (email/call), the actual first step of a B2B sales pipeline.
    """

    __tablename__ = "sales_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    plan: Mapped[str] = mapped_column(String(50), default="starter")  # starter|professional|enterprise
    intent: Mapped[str] = mapped_column(String(50), default="subscribe")  # subscribe|enterprise|investor|consultant
    message: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="new")  # new|contacted|closed


class ServiceEntitlement(TimestampMixin, Base):
    __tablename__ = "service_entitlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    service_key: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String(30), default="starter")
    quota: Mapped[Optional[int]] = mapped_column(Integer)
    used: Mapped[int] = mapped_column(Integer, default=0)
    reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Proposal(TimestampMixin, Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    proposal_type: Mapped[str] = mapped_column(String(50), default="commercial")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    locale: Mapped[str] = mapped_column(String(5), default="ar")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    feasibility_study_id: Mapped[Optional[int]] = mapped_column(ForeignKey("feasibility_studies.id"))


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text)
    entity: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class AnalyticsEvent(TimestampMixin, Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    service_key: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    entity: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
