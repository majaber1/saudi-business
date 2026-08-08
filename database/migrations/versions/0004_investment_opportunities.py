"""investment opportunities catalog

Adds the investment_opportunities table: the investor-facing catalog distinct
from `projects` (a founder's own feasibility workspace). Investors filter this
list by ticket size (investment_min/max), industry, and risk_level.

Revision ID: 0004_investment_opportunities
Revises: 0003_project_archive
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_investment_opportunities"
down_revision = "0003_project_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investment_opportunities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title_en", sa.String(length=200), nullable=False),
        sa.Column("title_ar", sa.String(length=200), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("summary_en", sa.Text(), nullable=True),
        sa.Column("summary_ar", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(length=30), nullable=False, server_default="mvp"),
        sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("investment_min", sa.Float(), nullable=True),
        sa.Column("investment_max", sa.Float(), nullable=True),
        sa.Column("expected_return_percent", sa.Float(), nullable=True),
        sa.Column("funding_goal", sa.Float(), nullable=True),
        sa.Column("funding_committed", sa.Float(), nullable=True, server_default="0"),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="demo"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_investment_opportunities_industry", "investment_opportunities", ["industry"])
    op.create_index("ix_investment_opportunities_investment_min", "investment_opportunities", ["investment_min"])


def downgrade() -> None:
    op.drop_index("ix_investment_opportunities_investment_min", table_name="investment_opportunities")
    op.drop_index("ix_investment_opportunities_industry", table_name="investment_opportunities")
    op.drop_table("investment_opportunities")
