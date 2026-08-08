"""email verification and password reset tokens

Revision ID: 0006_account_security
Revises: 0005_sales_leads
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_account_security"
down_revision = "0005_sales_leads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))
    # Preserve existing accounts as verified; only registrations after this
    # migration enter the verification flow.
    op.execute("UPDATE users SET email_verified_at = CURRENT_TIMESTAMP")
    op.create_table(
        "account_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_account_tokens_user_id", "account_tokens", ["user_id"])
    op.create_index("ix_account_tokens_purpose", "account_tokens", ["purpose"])
    op.create_index("ix_account_tokens_token_hash", "account_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_account_tokens_token_hash", table_name="account_tokens")
    op.drop_index("ix_account_tokens_purpose", table_name="account_tokens")
    op.drop_index("ix_account_tokens_user_id", table_name="account_tokens")
    op.drop_table("account_tokens")
    op.drop_column("users", "email_verified_at")
