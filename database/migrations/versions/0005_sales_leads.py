"""sales leads (pricing page contact capture)

Adds sales_leads: a contact-capture inbox for the public Pricing page's
"Talk to sales" / "Request access" forms. NOT a payment or subscription
record -- Saudi Business does not process payments through this platform.

Revision ID: 0005_sales_leads
Revises: 0004_investment_opportunities
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_sales_leads"
down_revision = "0004_investment_opportunities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sales_leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("plan", sa.String(length=50), nullable=False, server_default="starter"),
        sa.Column("intent", sa.String(length=50), nullable=False, server_default="subscribe"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sales_leads_email", "sales_leads", ["email"])


def downgrade() -> None:
    op.drop_index("ix_sales_leads_email", table_name="sales_leads")
    op.drop_table("sales_leads")
