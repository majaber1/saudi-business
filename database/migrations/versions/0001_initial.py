"""initial schema (original Saudi Business core)

Creates the original core schema from the SQLAlchemy model metadata, EXCLUDING
the Business Qualification & Readiness tables. Those tables are added by the
incremental migration 0002_business_qualification so that upgrading an existing
0001-era database (e.g. Neon) is exercised and verified, not just a fresh build.

We intentionally build the table list from live metadata MINUS the qualification
tables. This keeps 0001 in lock-step with the original models while leaving the
qualification schema to an explicit incremental migration.

Revision ID: 0001_initial
Revises:
"""
import sys
from pathlib import Path

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

# Tables introduced AFTER the original schema. Created by 0002, not here.
QUALIFICATION_TABLES = {
    "qualification_profiles",
    "qualification_requirements",
    "multazim_assessment_requests",
}


def _original_tables():
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "backend"))
    from app.db import Base
    from app import models  # noqa: F401  (register tables on Base.metadata)

    md = Base.metadata
    return [t for name, t in md.tables.items() if name not in QUALIFICATION_TABLES]


def upgrade() -> None:
    bind = op.get_bind()
    from app.db import Base  # noqa: F401

    tables = _original_tables()
    Base.metadata.create_all(bind=bind, tables=tables)


def downgrade() -> None:
    bind = op.get_bind()
    from app.db import Base  # noqa: F401

    tables = _original_tables()
    Base.metadata.drop_all(bind=bind, tables=tables)
