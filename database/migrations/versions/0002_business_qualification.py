"""business qualification & readiness schema

Explicit, incremental migration that adds the Business Qualification & Readiness
tables on top of the original 0001_initial schema. Written with explicit DDL
(not metadata.create_all) so that upgrading an existing 0001-era database is
exercised, reviewable, and reversible.

Tables:
  - qualification_profiles
  - qualification_requirements
  - multazim_assessment_requests

Revision ID: 0002_business_qualification
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_business_qualification"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qualification_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("company_name_en", sa.String(length=200), nullable=True),
        sa.Column("company_name_ar", sa.String(length=200), nullable=True),
        sa.Column("cr_number", sa.String(length=50), nullable=True),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("company_size", sa.String(length=30), nullable=True),
        sa.Column("saudization_rate", sa.Float(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("category_scores", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_qualification_profiles_owner_id", "qualification_profiles", ["owner_id"])
    op.create_index("ix_qualification_profiles_project_id", "qualification_profiles", ["project_id"])
    op.create_index("ix_qualification_profiles_sector", "qualification_profiles", ["sector"])

    op.create_table(
        "qualification_requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("qualification_profiles.id"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("title_en", sa.String(length=200), nullable=False),
        sa.Column("title_ar", sa.String(length=200), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("description_ar", sa.Text(), nullable=True),
        sa.Column("authority", sa.String(length=150), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="missing"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("declared_reference", sa.String(length=300), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_qualification_requirements_profile_id", "qualification_requirements", ["profile_id"])
    op.create_index("ix_qualification_requirements_category", "qualification_requirements", ["category"])

    op.create_table(
        "multazim_assessment_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("qualification_profiles.id"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("scope", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="requested"),
        sa.Column("summary_score", sa.Float(), nullable=True),
        sa.Column("summary_en", sa.Text(), nullable=True),
        sa.Column("summary_ar", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_multazim_assessment_requests_profile_id", "multazim_assessment_requests", ["profile_id"])
    op.create_index("ix_multazim_assessment_requests_requested_by", "multazim_assessment_requests", ["requested_by"])


def downgrade() -> None:
    op.drop_index("ix_multazim_assessment_requests_requested_by", table_name="multazim_assessment_requests")
    op.drop_index("ix_multazim_assessment_requests_profile_id", table_name="multazim_assessment_requests")
    op.drop_table("multazim_assessment_requests")

    op.drop_index("ix_qualification_requirements_category", table_name="qualification_requirements")
    op.drop_index("ix_qualification_requirements_profile_id", table_name="qualification_requirements")
    op.drop_table("qualification_requirements")

    op.drop_index("ix_qualification_profiles_sector", table_name="qualification_profiles")
    op.drop_index("ix_qualification_profiles_project_id", table_name="qualification_profiles")
    op.drop_index("ix_qualification_profiles_owner_id", table_name="qualification_profiles")
    op.drop_table("qualification_profiles")
