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
    role_key: Mapped[str] = mapped_column(String(50), ForeignKey("roles.key"), default="entrepreneur")
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"))

    organization: Mapped[Optional["Organization"]] = relationship(back_populates="users")
    projects: Mapped[list["Project"]] = relationship(back_populates="owner")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    investment: Mapped[float] = mapped_column(Float, nullable=False)
    stage: Mapped[str] = mapped_column(String(30), default="idea")
    workflow_status: Mapped[str] = mapped_column(String(30), default="created")
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
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="studies")
    assumptions: Mapped[list["FinancialAssumption"]] = relationship(back_populates="study")
    results: Mapped[list["FinancialResult"]] = relationship(back_populates="study")
    scenarios: Mapped[list["SensitivityScenario"]] = relationship(back_populates="study")


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


class Auction(TimestampMixin, Base):
    __tablename__ = "auctions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    seller_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    asking_price: Mapped[Optional[float]] = mapped_column(Float)
    reserve_price: Mapped[Optional[float]] = mapped_column(Float)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="draft")

    bids: Mapped[list["AuctionBid"]] = relationship(back_populates="auction")


class AuctionBid(TimestampMixin, Base):
    __tablename__ = "auction_bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey("auctions.id"), index=True, nullable=False)
    bidder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Optional[float]] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String(30), default="expression_of_interest")
    message: Mapped[Optional[str]] = mapped_column(Text)

    auction: Mapped["Auction"] = relationship(back_populates="bids")


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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    storage_ref: Mapped[Optional[str]] = mapped_column(String(500))


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
