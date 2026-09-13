"""Phase 8C.1 — Persistent research_runs + research_evidence_refs.

Revision ID: 0031_research_runs
Revises: 0030_knowledge_sources

Additive only. Does not alter Knowledge tables beyond optional FKs from
research_evidence_refs. Downgrade drops the new tables.
"""
from alembic import op
import sqlalchemy as sa

revision = "0031_research_runs"
down_revision = "0030_knowledge_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("study_id", sa.String(64), nullable=False),
        sa.Column("project_id", sa.String(64), nullable=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column(
            "research_type",
            sa.String(80),
            nullable=False,
            server_default="gap_research",
        ),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="PLANNED"),
        sa.Column("plan_json", sa.JSON(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("source_keys_json", sa.JSON(), nullable=True),
        sa.Column(
            "knowledge_reused",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "live_fetch_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("sanitized_error_code", sa.String(80), nullable=True),
        sa.Column("sanitized_error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_research_runs_study_id", "research_runs", ["study_id"])
    op.create_index("ix_research_runs_project_id", "research_runs", ["project_id"])
    op.create_index("ix_research_runs_owner_id", "research_runs", ["owner_id"])
    op.create_index("ix_research_runs_user_id", "research_runs", ["user_id"])
    op.create_index("ix_research_runs_status", "research_runs", ["status"])
    op.create_index(
        "ix_research_runs_study_owner",
        "research_runs",
        ["study_id", "owner_id"],
    )

    op.create_table(
        "research_evidence_refs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "research_run_id",
            sa.String(36),
            sa.ForeignKey("research_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("study_id", sa.String(64), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("source_key", sa.String(80), nullable=True),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column(
            "source_document_id",
            sa.String(36),
            sa.ForeignKey("knowledge_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "chunk_id",
            sa.String(36),
            sa.ForeignKey("knowledge_chunks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("official_url", sa.String(1000), nullable=True),
        sa.Column("authority_type", sa.String(80), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(), nullable=True),
        sa.Column("evidence_type", sa.String(80), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("provenance_json", sa.JSON(), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "research_run_id",
            "idempotency_key",
            name="uq_research_evidence_ref_run_idem",
        ),
    )
    op.create_index(
        "ix_research_evidence_refs_research_run_id",
        "research_evidence_refs",
        ["research_run_id"],
    )
    op.create_index(
        "ix_research_evidence_refs_study_id",
        "research_evidence_refs",
        ["study_id"],
    )
    op.create_index(
        "ix_research_evidence_refs_owner_id",
        "research_evidence_refs",
        ["owner_id"],
    )
    op.create_index(
        "ix_research_evidence_refs_user_id",
        "research_evidence_refs",
        ["user_id"],
    )
    op.create_index(
        "ix_research_evidence_refs_source_key",
        "research_evidence_refs",
        ["source_key"],
    )
    op.create_index(
        "ix_research_evidence_refs_source_document_id",
        "research_evidence_refs",
        ["source_document_id"],
    )
    op.create_index(
        "ix_research_evidence_refs_chunk_id",
        "research_evidence_refs",
        ["chunk_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_research_evidence_refs_chunk_id", table_name="research_evidence_refs"
    )
    op.drop_index(
        "ix_research_evidence_refs_source_document_id",
        table_name="research_evidence_refs",
    )
    op.drop_index(
        "ix_research_evidence_refs_source_key", table_name="research_evidence_refs"
    )
    op.drop_index(
        "ix_research_evidence_refs_user_id", table_name="research_evidence_refs"
    )
    op.drop_index(
        "ix_research_evidence_refs_owner_id", table_name="research_evidence_refs"
    )
    op.drop_index(
        "ix_research_evidence_refs_study_id", table_name="research_evidence_refs"
    )
    op.drop_index(
        "ix_research_evidence_refs_research_run_id",
        table_name="research_evidence_refs",
    )
    op.drop_table("research_evidence_refs")

    op.drop_index("ix_research_runs_study_owner", table_name="research_runs")
    op.drop_index("ix_research_runs_status", table_name="research_runs")
    op.drop_index("ix_research_runs_user_id", table_name="research_runs")
    op.drop_index("ix_research_runs_owner_id", table_name="research_runs")
    op.drop_index("ix_research_runs_project_id", table_name="research_runs")
    op.drop_index("ix_research_runs_study_id", table_name="research_runs")
    op.drop_table("research_runs")
