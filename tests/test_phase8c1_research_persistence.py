"""Phase 8C.1 — Persistent Research Runs + durable provenance (persistence gate)."""
from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

if not os.environ.get("DATABASE_URL"):
    _TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _TMP.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _TMP.name
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters-long!!")

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "backend"))
sys.path.insert(0, str(_REPO))

from app import db as app_db  # noqa: E402
from app import models  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.services import research_persistence_service as rps  # noqa: E402
from ai_engine.research.schemas import (  # noqa: E402
    ResearchClaim,
    ResearchPlan,
    ResearchResult,
    ResearchSourceRef,
)

DATABASE_DIR = _REPO / "database"
MIGRATIONS_DIR = DATABASE_DIR / "migrations"


def setup_module(module):
    assert app_db.DB_ENABLED is True
    app_db.init_db()
    Base.metadata.create_all(bind=engine)


def _session():
    return app_db.SessionLocal()


def _user(db, email: str | None = None) -> models.User:
    u = models.User(
        email=email or f"u_{uuid.uuid4().hex[:10]}@example.com",
        hashed_password="x",
        full_name="Tester",
        role_key="entrepreneur",
        locale="en",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _knowledge(db, owner_id: int):
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())
    db.add(
        models.KnowledgeDocument(
            id=doc_id,
            owner_id=owner_id,
            title="GASTAT CPI",
            source="gastat",
            country="SA",
            document_type="official",
            assumptions={},
            confidence=0.9,
            visibility="private",
            extraction_status="ready",
        )
    )
    db.add(
        models.KnowledgeChunk(
            id=chunk_id,
            document_id=doc_id,
            owner_id=owner_id,
            content="Saudi CPI rose 1.6% YoY.",
            embedding=[],
            chunk_metadata={},
            importance=0.9,
        )
    )
    db.commit()
    return doc_id, chunk_id


def _result(
    study_id: str,
    doc_id: str | None,
    chunk_id: str | None,
    status: str = "complete",
):
    plan = ResearchPlan(
        study_id=study_id,
        gaps=["Saudi inflation CPI"],
        sources=[
            ResearchSourceRef(
                source_key="gastat",
                connector_id="live.gastat",
                reason="official CPI",
            )
        ],
        queries=["Saudi Arabia CPI"],
    )
    claims = []
    if doc_id:
        claims.append(
            ResearchClaim(
                statement="Saudi CPI rose 1.6% YoY.",
                source_type="official",
                source_url="https://www.stats.gov.sa/en/cpi",
                confidence=0.9,
                source_key="gastat",
                from_knowledge=True,
                document_id=doc_id,
                chunk_id=chunk_id,
            )
        )
    return ResearchResult(
        plan=plan,
        status=status,  # type: ignore[arg-type]
        claims=claims,
        knowledge_hits=1 if claims else 0,
        live_fetches=0,
        attempts=[
            {
                "source_key": "gastat",
                "outcome": "knowledge_hit" if claims else "empty",
                "path": "knowledge",
            }
        ],
        market_research={"status": "partial", "competitors": []},
    )


class TestResearchRunCRUD:
    def test_a_create_read_update(self):
        db = _session()
        try:
            user = _user(db)
            run = rps.create_run(
                db,
                study_id="s-a",
                owner_id=user.id,
                user_id=str(user.id),
                project_id="p-a",
                question="CPI?",
                status="PLANNED",
            )
            db.commit()
            rid = run.id
            uid = user.id
            rps.start_run(db, run_id=rid, owner_id=uid)
            rps.complete_run(
                db,
                run_id=rid,
                owner_id=uid,
                status="COMPLETE",
                result_json={"status": "complete"},
                knowledge_reused=True,
                live_fetch_count=0,
            )
            db.commit()
        finally:
            db.close()

        db2 = _session()
        try:
            loaded = rps.get_run(db2, run_id=rid, owner_id=uid)
            assert loaded is not None
            assert loaded.status == "COMPLETE"
            assert loaded.question == "CPI?"
            assert loaded.knowledge_reused is True
        finally:
            db2.close()

    def test_b_multiple_runs_preserved(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            r1 = rps.persist_research_result(
                db,
                study_id="s-multi",
                owner_id=user.id,
                result=_result("s-multi", doc_id, chunk_id, "complete"),
                user_id=str(user.id),
            )
            r2 = rps.persist_research_result(
                db,
                study_id="s-multi",
                owner_id=user.id,
                result=_result("s-multi", doc_id, chunk_id, "partial"),
                user_id=str(user.id),
            )
            assert r1 and r2 and r1.id != r2.id
            runs = rps.list_runs_for_study(
                db, study_id="s-multi", owner_id=user.id, user_id=str(user.id)
            )
            assert len(runs) >= 2
            latest = rps.load_latest_run(
                db, study_id="s-multi", owner_id=user.id, user_id=str(user.id)
            )
            assert latest is not None
            assert latest.id == r2.id
        finally:
            db.close()


class TestEvidenceRefs:
    def test_c_d_e_f_g_evidence_survives_fresh_session(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            run = rps.persist_research_result(
                db,
                study_id="s-ev",
                owner_id=user.id,
                result=_result("s-ev", doc_id, chunk_id),
                user_id=str(user.id),
                project_id="p-ev",
            )
            assert run is not None
            run_id = run.id
            uid = user.id
        finally:
            db.close()

        db2 = _session()
        try:
            loaded = rps.get_run(db2, run_id=run_id, owner_id=uid)
            assert loaded is not None
            refs = rps.load_run_evidence(db2, run_id=run_id, owner_id=uid)
            assert len(refs) >= 1
            ref = refs[0]
            assert ref.source_document_id == doc_id
            assert ref.chunk_id == chunk_id
            assert ref.official_url == "https://www.stats.gov.sa/en/cpi"
            assert ref.source_key == "gastat"
            assert ref.provenance_json is not None
        finally:
            db2.close()


class TestHydrationPreference:
    def test_j_new_persistence_preferred_over_snapshot(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            rps.persist_research_result(
                db,
                study_id="s-pref",
                owner_id=user.id,
                result=_result("s-pref", doc_id, chunk_id, "complete"),
                user_id=str(user.id),
            )
            state = {
                "research_status": "failed",
                "research_context": {"from": "snapshot_only"},
                "research_attempts": [],
                "market_research_context": None,
            }
            rps.hydrate_research_into_state(
                db, study_id="s-pref", user_id=str(user.id), state=state
            )
            assert state["research_status"] == "complete"
            assert state["research_context"].get("persisted_run_id")
            assert state["research_context"].get("from") != "snapshot_only"
            assert isinstance(state.get("market_research_context"), dict)
        finally:
            db.close()

    def test_k_legacy_snapshot_fallback(self):
        db = _session()
        try:
            user = _user(db)
            state = {
                "research_status": "partial",
                "research_context": {"from": "legacy_snapshot", "status": "partial"},
                "research_attempts": [{"outcome": "ok"}],
                "market_research_context": {"status": "partial"},
            }
            before = dict(state)
            rps.hydrate_research_into_state(
                db, study_id="s-legacy-none", user_id=str(user.id), state=state
            )
            assert state == before
        finally:
            db.close()

    def test_l_dual_write_consistency(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            result = _result("s-dual", doc_id, chunk_id)
            run = rps.persist_research_result(
                db,
                study_id="s-dual",
                owner_id=user.id,
                result=result,
                user_id=str(user.id),
            )
            assert run is not None
            state = {
                "research_status": "failed",
                "research_context": result.to_public_dict(),
                "research_attempts": list(result.attempts),
                "market_research_context": result.market_research,
            }
            rps.hydrate_research_into_state(
                db, study_id="s-dual", user_id=str(user.id), state=state
            )
            assert state["research_status"] == "complete"
            assert state["research_context"]["persisted_run_id"] == run.id
        finally:
            db.close()


class TestIdempotencyAndSafety:
    def test_m_duplicate_write_idempotency(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            result = _result("s-idem", doc_id, chunk_id)
            run_id = str(uuid.uuid4())
            r1 = rps.persist_research_result(
                db,
                study_id="s-idem",
                owner_id=user.id,
                result=result,
                user_id=str(user.id),
                run_id=run_id,
            )
            r2 = rps.persist_research_result(
                db,
                study_id="s-idem",
                owner_id=user.id,
                result=result,
                user_id=str(user.id),
                run_id=run_id,
            )
            assert r1 and r2 and r1.id == r2.id == run_id
            runs = rps.list_runs_for_study(db, study_id="s-idem", owner_id=user.id)
            assert len(runs) == 1
            refs = rps.load_run_evidence(db, run_id=run_id, owner_id=user.id)
            assert len(refs) == 1
        finally:
            db.close()

    def test_n_transaction_rollback_on_evidence_failure(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            result = _result("s-tx", doc_id, chunk_id)
            with patch.object(
                rps,
                "attach_evidence_refs",
                side_effect=RuntimeError("simulated evidence write failure"),
            ):
                out = rps.persist_research_result(
                    db,
                    study_id="s-tx",
                    owner_id=user.id,
                    result=result,
                    user_id=str(user.id),
                )
            assert out is None
            runs = rps.list_runs_for_study(db, study_id="s-tx", owner_id=user.id)
            assert runs == []
            orphans = (
                db.query(models.ResearchRun)
                .filter(
                    models.ResearchRun.study_id == "s-tx",
                    models.ResearchRun.status == "COMPLETE",
                )
                .all()
            )
            assert orphans == []
        finally:
            db.close()

    def test_o_p_tenant_isolation(self):
        db = _session()
        try:
            u1 = _user(db)
            u2 = _user(db)
            doc_id, chunk_id = _knowledge(db, u1.id)
            run = rps.persist_research_result(
                db,
                study_id="s-tenant",
                owner_id=u1.id,
                result=_result("s-tenant", doc_id, chunk_id),
                user_id=str(u1.id),
            )
            assert run is not None
            assert rps.get_run(db, run_id=run.id, owner_id=u2.id) is None
            assert (
                rps.load_latest_run(
                    db, study_id="s-tenant", owner_id=u2.id, user_id=str(u2.id)
                )
                is None
            )
            assert rps.load_run_evidence(db, run_id=run.id, owner_id=u2.id) == []
            state = {"research_status": None}
            rps.hydrate_research_into_state(
                db, study_id="s-tenant", user_id=str(u2.id), state=state
            )
            assert state.get("research_status") is None
        finally:
            db.close()


class TestAPIContract:
    def test_q_api_projection_fields(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            run = rps.persist_research_result(
                db,
                study_id="s-api",
                owner_id=user.id,
                result=_result("s-api", doc_id, chunk_id),
                user_id=str(user.id),
            )
            refs = rps.load_run_evidence(db, run_id=run.id, owner_id=user.id)
            proj = rps.run_to_api_projection(run, evidence=refs)
            for key in (
                "research_status",
                "research_context",
                "research_attempts",
                "market_research_context",
            ):
                assert key in proj
            assert proj["research_status"] == "complete"
            assert isinstance(proj["research_context"], dict)
            assert isinstance(proj["research_attempts"], list)
        finally:
            db.close()

    def test_r_study_load_prefers_persistence(self):
        from app.api.v2 import study_engine as se

        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            study_id = f"study-{uuid.uuid4().hex[:8]}"
            result = _result(study_id, doc_id, chunk_id)
            rps.persist_research_result(
                db,
                study_id=study_id,
                owner_id=user.id,
                result=result,
                user_id=str(user.id),
            )
            bad_state = {
                "project_id": "p1",
                "language": "en",
                "phase": "EVIDENCE_REVIEW",
                "research_status": "failed",
                "research_context": {"from": "bad_snapshot"},
                "research_attempts": [],
                "market_research_context": None,
                "claims": [],
                "assumptions": [],
                "messages": [],
            }
            se._save_study(study_id, bad_state, str(user.id))
            loaded = se._load_study(study_id, str(user.id))
            assert loaded is not None
            state = loaded.get("state") or loaded
            assert state.get("research_status") == "complete"
            assert (state.get("research_context") or {}).get("persisted_run_id")
        finally:
            db.close()


class TestMigration:
    def test_s_t_upgrade_downgrade_roundtrip(self, tmp_path):
        db_file = tmp_path / "phase8c1.db"
        db_url = f"sqlite:///{db_file.as_posix()}"
        ini = DATABASE_DIR / "alembic.ini"
        cfg = Config(str(ini))
        cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
        cfg.set_main_option("sqlalchemy.url", db_url)
        os.environ["DATABASE_URL"] = db_url

        script = ScriptDirectory.from_config(cfg)
        assert script.get_heads() == ["0031_research_runs"]

        command.upgrade(cfg, "0030_knowledge_sources")
        eng = sa.create_engine(db_url)
        tables = set(sa.inspect(eng).get_table_names())
        assert "research_runs" not in tables
        assert "knowledge_sources" in tables

        command.upgrade(cfg, "0031_research_runs")
        tables = set(sa.inspect(eng).get_table_names())
        assert "research_runs" in tables
        assert "research_evidence_refs" in tables
        cols = {c["name"] for c in sa.inspect(eng).get_columns("research_runs")}
        assert {
            "id",
            "study_id",
            "owner_id",
            "user_id",
            "status",
            "plan_json",
            "result_json",
            "source_keys_json",
            "knowledge_reused",
            "live_fetch_count",
        }.issubset(cols)
        ref_cols = {
            c["name"] for c in sa.inspect(eng).get_columns("research_evidence_refs")
        }
        assert {
            "id",
            "research_run_id",
            "source_document_id",
            "chunk_id",
            "official_url",
            "idempotency_key",
        }.issubset(ref_cols)

        command.downgrade(cfg, "0030_knowledge_sources")
        tables = set(sa.inspect(eng).get_table_names())
        assert "research_runs" not in tables
        assert "research_evidence_refs" not in tables

        command.upgrade(cfg, "0031_research_runs")
        assert "research_runs" in set(sa.inspect(eng).get_table_names())


class TestAcceptanceFreshReload:
    def test_18_fresh_session_reload_and_reopen(self):
        db = _session()
        try:
            user = _user(db)
            doc_id, chunk_id = _knowledge(db, user.id)
            study_id = f"accept-{uuid.uuid4().hex[:8]}"
            result = _result(study_id, doc_id, chunk_id)
            run = rps.persist_research_result(
                db,
                study_id=study_id,
                owner_id=user.id,
                result=result,
                user_id=str(user.id),
                project_id="accept-project",
            )
            assert run is not None
            uid = user.id
            run_id = run.id
        finally:
            db.close()

        db2 = _session()
        try:
            latest = rps.load_latest_run(
                db2, study_id=study_id, owner_id=uid, user_id=str(uid)
            )
            assert latest is not None
            assert latest.id == run_id
            assert latest.status == "COMPLETE"
            assert latest.question and "inflation" in latest.question.lower()
            refs = rps.load_run_evidence(db2, run_id=run_id, owner_id=uid)
            assert refs
            assert refs[0].source_document_id == doc_id
            assert refs[0].chunk_id == chunk_id
            assert refs[0].official_url
            state: dict = {}
            rps.hydrate_research_into_state(
                db2, study_id=study_id, user_id=str(uid), state=state
            )
            assert state["research_status"] == "complete"
            assert state["research_context"]["persisted_run_id"] == run_id
        finally:
            db2.close()
