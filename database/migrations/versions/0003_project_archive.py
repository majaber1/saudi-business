"""project soft-archive columns

Adds Project.is_archived / archived_at so projects can be archived (hidden from
the default list) without hard-deleting rows, keeping dependent feasibility
studies and reports intact.

This migration is IDEMPOTENT with respect to those two columns: on a fresh
database 0001_initial builds the projects table straight from model metadata
(which already includes the new columns), so this migration only ADDs them when
they are absent (the real "existing 0001-era DB" upgrade path). Likewise the
downgrade only drops them when present.

Revision ID: 0003_project_archive
Revises: 0002_business_qualification
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_project_archive"
down_revision = "0002_business_qualification"
branch_labels = None
depends_on = None


def _project_columns():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return {c["name"] for c in insp.get_columns("projects")}


def upgrade() -> None:
    existing = _project_columns()
    if "is_archived" not in existing:
        op.add_column(
            "projects",
            sa.Column(
                "is_archived",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    if "archived_at" not in existing:
        op.add_column(
            "projects",
            sa.Column("archived_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    existing = _project_columns()
    if "archived_at" in existing:
        op.drop_column("projects", "archived_at")
    if "is_archived" in existing:
        op.drop_column("projects", "is_archived")
