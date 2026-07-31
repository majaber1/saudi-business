"""initial schema

Creates the full schema from the SQLAlchemy model metadata. Using
metadata.create_all keeps this initial migration in lock-step with the models
while still going through Alembic (so 'alembic upgrade head' is the single,
verifiable path to a production schema).

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


def _metadata():
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "backend"))
    from app.db import Base
    from app import models  # noqa: F401  (register tables)

    return Base.metadata


def upgrade() -> None:
    _metadata().create_all(op.get_bind())


def downgrade() -> None:
    _metadata().drop_all(op.get_bind())
