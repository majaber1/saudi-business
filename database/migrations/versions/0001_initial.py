"""initial schema (original Saudi Business core)

Frozen, explicit Alembic DDL for the original core schema. This migration
intentionally does NOT import app.models / Base.metadata, so it can never
change when the live ORM models change. Business Qualification & Readiness
tables are added later by 0002_business_qualification. Project.is_archived /
archived_at are added later by 0003_project_archive. Neither exists here.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _ts():
    return (
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_ar", sa.String(length=200)),
        sa.Column("cr_number", sa.String()),
        sa.Column("sector", sa.String(length=100)),
        *_ts(),
    )
    op.create_index("ix_organizations_cr_number", "organizations", ["cr_number"])

        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(), nullable=False),
            sa.Column("name_en", sa.String(length=100), nullable=False),
            sa.Column("name_ar", sa.String(length=100), nullable=False),
            sa.Column("permissions", sa.JSON(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_roles_key", "roles", ["key"], unique=True)
    
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=200)),
            sa.Column("locale", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("role_key", sa.String(), sa.ForeignKey("roles.key"), nullable=False),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id")),
            *_ts(),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("industry", sa.String(length=100), nullable=False),
            sa.Column("investment", sa.Float(), nullable=False),
            sa.Column("stage", sa.String(), nullable=False),
            sa.Column("workflow_status", sa.String(), nullable=False),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id")),
            *_ts(),
        )
        op.create_index("ix_projects_industry", "projects", ["industry"])
    
        op.create_table(
            "feasibility_studies",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("study_type", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("current_step", sa.Integer(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_feasibility_studies_project_id", "feasibility_studies", ["project_id"])
    
        op.create_table(
            "documents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id")),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=100)),
            sa.Column("size_bytes", sa.Integer()),
            sa.Column("storage_ref", sa.String(length=500)),
            *_ts(),
        )
    
        op.create_table(
            "financial_assumptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("study_id", sa.Integer(), sa.ForeignKey("feasibility_studies.id"), nullable=False),
            sa.Column("capex", sa.Float(), nullable=False),
            sa.Column("opex_annual", sa.Float(), nullable=False),
            sa.Column("revenue_year1", sa.Float(), nullable=False),
            sa.Column("growth_rate", sa.Float(), nullable=False),
            sa.Column("discount_rate", sa.Float(), nullable=False),
            sa.Column("horizon_years", sa.Integer(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_financial_assumptions_study_id", "financial_assumptions", ["study_id"])
    
        op.create_table(
            "financial_results",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("study_id", sa.Integer(), sa.ForeignKey("feasibility_studies.id"), nullable=False),
            sa.Column("roi", sa.Float()),
            sa.Column("npv", sa.Float()),
            sa.Column("irr", sa.Float()),
            sa.Column("payback_years", sa.Float()),
            sa.Column("break_even", sa.Float()),
            sa.Column("verdict", sa.String()),
            sa.Column("detail", sa.JSON(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_financial_results_study_id", "financial_results", ["study_id"])
    
        op.create_table(
            "sensitivity_scenarios",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("study_id", sa.Integer(), sa.ForeignKey("feasibility_studies.id"), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("revenue_delta", sa.Float(), nullable=False),
            sa.Column("npv", sa.Float()),
            sa.Column("irr", sa.Float()),
            *_ts(),
        )
        op.create_index("ix_sensitivity_scenarios_study_id", "sensitivity_scenarios", ["study_id"])
    
        op.create_table(
            "reports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("study_id", sa.Integer(), sa.ForeignKey("feasibility_studies.id"), nullable=False),
            sa.Column("fmt", sa.String(), nullable=False),
            sa.Column("locale", sa.String(), nullable=False),
            sa.Column("version", sa.String(), nullable=False),
            sa.Column("storage_ref", sa.String(length=500)),
            *_ts(),
        )
        op.create_index("ix_reports_study_id", "reports", ["study_id"])
    
        op.create_table(
            "funding_programs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(), nullable=False),
            sa.Column("name_en", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=False),
            sa.Column("organization", sa.String(length=150)),
            sa.Column("description_en", sa.Text()),
            sa.Column("description_ar", sa.Text()),
            sa.Column("funding_type", sa.String()),
            sa.Column("eligibility", sa.JSON(), nullable=False),
            sa.Column("source_url", sa.String(length=500)),
            sa.Column("application_url", sa.String(length=500)),
            sa.Column("last_verified", sa.DateTime()),
            sa.Column("verification_status", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_funding_programs_key", "funding_programs", ["key"], unique=True)
    
        op.create_table(
            "funding_matches",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("program_key", sa.String(), sa.ForeignKey("funding_programs.key"), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("reasons", sa.JSON(), nullable=False),
            sa.Column("missing", sa.JSON(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_funding_matches_project_id", "funding_matches", ["project_id"])
    
        op.create_table(
            "idea_bank_entries",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title_en", sa.String(length=200), nullable=False),
            sa.Column("title_ar", sa.String(length=200), nullable=False),
            sa.Column("industry", sa.String(length=100), nullable=False),
            sa.Column("summary_en", sa.Text()),
            sa.Column("summary_ar", sa.Text()),
            sa.Column("problem", sa.Text()),
            sa.Column("solution", sa.Text()),
            sa.Column("revenue_model", sa.String(length=200)),
            sa.Column("investment_min", sa.Float()),
            sa.Column("investment_max", sa.Float()),
            sa.Column("difficulty", sa.String()),
            sa.Column("time_to_launch", sa.String()),
            sa.Column("vision2030_alignment", sa.String(length=200)),
            sa.Column("is_featured", sa.Boolean(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("source", sa.String(length=300)),
            *_ts(),
        )
        op.create_index("ix_idea_bank_entries_industry", "idea_bank_entries", ["industry"])
    
        op.create_table(
            "franchise_opportunities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("brand", sa.String(length=200), nullable=False),
            sa.Column("description_en", sa.Text()),
            sa.Column("description_ar", sa.Text()),
            sa.Column("sector", sa.String(length=100), nullable=False),
            sa.Column("country", sa.String()),
            sa.Column("regions", sa.JSON(), nullable=False),
            sa.Column("investment_min", sa.Float()),
            sa.Column("investment_max", sa.Float()),
            sa.Column("franchise_fee", sa.Float()),
            sa.Column("royalty_model", sa.String(length=150)),
            sa.Column("required_space", sa.String(length=100)),
            sa.Column("application_url", sa.String(length=500)),
            sa.Column("source_url", sa.String(length=500)),
            sa.Column("verification_status", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_franchise_opportunities_sector", "franchise_opportunities", ["sector"])
    
        op.create_table(
            "auctions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("seller_id", sa.Integer(), sa.ForeignKey("users.id")),
            sa.Column("asking_price", sa.Float()),
            sa.Column("reserve_price", sa.Float()),
            sa.Column("starts_at", sa.DateTime()),
            sa.Column("ends_at", sa.DateTime()),
            sa.Column("status", sa.String(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_auctions_category", "auctions", ["category"])
    
        op.create_table(
            "auction_bids",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("auction_id", sa.Integer(), sa.ForeignKey("auctions.id"), nullable=False),
            sa.Column("bidder_id", sa.Integer(), sa.ForeignKey("users.id")),
            sa.Column("amount", sa.Float()),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("message", sa.Text()),
            *_ts(),
        )
        op.create_index("ix_auction_bids_auction_id", "auction_bids", ["auction_id"])
    
        op.create_table(
            "multazim_requirements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("title_en", sa.String(length=200), nullable=False),
            sa.Column("title_ar", sa.String(length=200), nullable=False),
            sa.Column("description_en", sa.Text()),
            sa.Column("description_ar", sa.Text()),
            sa.Column("authority", sa.String(length=150)),
            sa.Column("is_mandatory", sa.Boolean(), nullable=False),
            sa.Column("source_url", sa.String(length=500)),
            *_ts(),
        )
        op.create_index("ix_multazim_requirements_category", "multazim_requirements", ["category"])
    
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id")),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("entity", sa.String(length=100)),
            sa.Column("entity_id", sa.Integer()),
            sa.Column("meta", sa.JSON(), nullable=False),
            *_ts(),
        )
        op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    

def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_multazim_requirements_category", table_name="multazim_requirements")
    op.drop_table("multazim_requirements")
    op.drop_index("ix_auction_bids_auction_id", table_name="auction_bids")
    op.drop_table("auction_bids")
    op.drop_index("ix_auctions_category", table_name="auctions")
    op.drop_table("auctions")
    op.drop_index("ix_franchise_opportunities_sector", table_name="franchise_opportunities")
    op.drop_table("franchise_opportunities")
    op.drop_index("ix_idea_bank_entries_industry", table_name="idea_bank_entries")
    op.drop_table("idea_bank_entries")
    op.drop_index("ix_funding_matches_project_id", table_name="funding_matches")
    op.drop_table("funding_matches")
    op.drop_index("ix_funding_programs_key", table_name="funding_programs")
    op.drop_table("funding_programs")
    op.drop_index("ix_reports_study_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_sensitivity_scenarios_study_id", table_name="sensitivity_scenarios")
    op.drop_table("sensitivity_scenarios")
    op.drop_index("ix_financial_results_study_id", table_name="financial_results")
    op.drop_table("financial_results")
    op.drop_index("ix_financial_assumptions_study_id", table_name="financial_assumptions")
    op.drop_table("financial_assumptions")
    op.drop_table("documents")
    op.drop_index("ix_feasibility_studies_project_id", table_name="feasibility_studies")
    op.drop_table("feasibility_studies")
    op.drop_index("ix_projects_industry", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_roles_key", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_organizations_cr_number", table_name="organizations")
    op.drop_table("organizations")
