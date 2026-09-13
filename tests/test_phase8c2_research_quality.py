"""Phase 8C.2 — Source Ranking, Freshness & Conflict Intelligence."""
from __future__ import annotations

import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

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
from ai_engine.research.quality import (  # noqa: E402
    RESEARCH_QUALITY_POLICY_VERSION,
    classify_claim_type,
    classify_non_conflict,
    enrich_claims_with_quality,
    evaluate_research_quality,
)
from ai_engine.research.quality.engine import evaluate_freshness  # noqa: E402
from ai_engine.research.schemas import (  # noqa: E402
    ResearchClaim,
    ResearchPlan,
    ResearchResult,
    ResearchSourceRef,
)
from ai_engine.research.market.market_signal import (  # noqa: E402
    detect_signal_conflicts,
    research_market_signals,
)
from ai_engine.research.market.schemas import MarketSignal  # noqa: E402

AS_OF = datetime(2026, 9, 13, tzinfo=timezone.utc)


def setup_module(module):
    assert app_db.DB_ENABLED is True
    app_db.init_db()
    from app.api.v2 import study_engine as _study_engine  # noqa: F401

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


def _cand(**kwargs):
    base = {
        "source_type": "official",
        "geography": "SA",
        "unit": "percent",
        "confidence": 0.9,
    }
    base.update(kwargs)
    base.setdefault("evidence_id", str(uuid.uuid4()))
    return base


class TestClaimType:
    def test_cpi_inflation(self):
        assert classify_claim_type(text="Saudi CPI inflation rate") == "INFLATION"
        assert classify_claim_type(metric_key="cpi_inflation") == "INFLATION"

    def test_gdp(self):
        assert classify_claim_type(text="Saudi GDP growth Q1") == "GDP"

    def test_fdi(self):
        assert (
            classify_claim_type(text="FDI foreign direct investment inflow")
            == "INVESTMENT_FDI"
        )

    def test_unknown_not_guessed(self):
        assert classify_claim_type(text="") == "UNKNOWN"
        assert classify_claim_type(text=None) == "UNKNOWN"


class TestSourceRanking:
    def test_a_cpi_gastat_beats_misa(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="misa-cpi",
                    source_key="misa",
                    statement="Investment climate note mentions inflation briefly",
                    metric_key="cpi_inflation",
                    value=2.0,
                    period="2026-08",
                    published_at="2026-08-01",
                    source_url="https://misa.gov.sa/en/investment",
                ),
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                ),
            ],
            question="What is Saudi CPI inflation?",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert result.preferred_evidence_ids[0] == "gastat-cpi"
        by_id = {e.evidence_id: e for e in result.evaluations}
        assert by_id["gastat-cpi"].authority_fit == "PRIMARY"
        assert by_id["misa-cpi"].authority_fit in {"RELATED", "UNRELATED", "SECONDARY"}

    def test_b_gdp_gastat_preferred(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="gastat-gdp",
                    source_key="gastat",
                    statement="GDP growth 3.1%",
                    metric_key="gdp_growth",
                    value=3.1,
                    period="2026-Q1",
                    published_at="2026-06-01",
                    source_url="https://www.stats.gov.sa/en/gdp",
                ),
                _cand(
                    evidence_id="misa-gdp",
                    source_key="misa",
                    statement="Investment briefing cites GDP",
                    metric_key="gdp_growth",
                    value=4.0,
                    period="2026-Q1",
                    published_at="2026-06-02",
                    source_url="https://misa.gov.sa/en/fdi",
                ),
            ],
            question="Saudi GDP growth",
            claim_type="GDP",
            as_of=AS_OF,
        )
        assert result.preferred_evidence_ids[0] == "gastat-gdp"

    def test_c_fdi_misa_preferred(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="gastat-fdi",
                    source_key="gastat",
                    statement="National accounts note",
                    metric_key="fdi_inflow",
                    value=10,
                    period="2025",
                    published_at="2026-01-01",
                    source_url="https://www.stats.gov.sa/en/econ",
                ),
                _cand(
                    evidence_id="misa-fdi",
                    source_key="misa",
                    statement="FDI inflow USD 19bn",
                    metric_key="fdi_inflow",
                    value=19,
                    period="2025",
                    published_at="2026-02-01",
                    source_url="https://misa.gov.sa/en/fdi-statistics",
                ),
            ],
            question="Saudi FDI inflow",
            claim_type="INVESTMENT_FDI",
            as_of=AS_OF,
        )
        assert result.preferred_evidence_ids[0] == "misa-fdi"
        by_id = {e.evidence_id: e for e in result.evaluations}
        assert by_id["misa-fdi"].authority_fit == "PRIMARY"

    def test_d_relevance_beats_generic_trust(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="global-blog",
                    source_key="global_macro_blog",
                    statement="World CPI commentary",
                    metric_key="cpi_inflation",
                    value=3.0,
                    period="2026-08",
                    published_at="2026-08-20",
                    source_url="https://example.com/world-cpi",
                    trust_score=0.99,
                    geography="GLOBAL",
                ),
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                    trust_score=0.7,
                ),
            ],
            question="Saudi CPI inflation",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert result.preferred_evidence_ids[0] == "gastat-cpi"

    def test_e_ai_assumption_never_outranks(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="ai-1",
                    source_key="model",
                    source_type="ai_assumption",
                    statement="I assume CPI is 2%",
                    metric_key="cpi_inflation",
                    value=2.0,
                    period="2026-08",
                    published_at="2026-09-01",
                    source_url=None,
                    document_id=None,
                    chunk_id=None,
                    trust_score=1.0,
                ),
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        by_id = {e.evidence_id: e for e in result.evaluations}
        assert by_id["ai-1"].selection_status == "REJECTED_AI_ASSUMPTION"
        assert by_id["ai-1"].eligible is False
        assert result.preferred_evidence_ids == ["gastat-cpi"]

    def test_f_registry_only_never_selected(self):
        result = evaluate_research_quality(
            [
                {
                    "evidence_id": "registry-only",
                    "source_key": "gastat",
                    "source_type": "official",
                    "statement": "placeholder without provenance",
                    "metric_key": "cpi_inflation",
                    "value": 1.0,
                    "period": "2026-08",
                    "geography": "SA",
                }
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert result.preferred_evidence_ids == []
        assert result.evaluations[0].selection_status == "REJECTED_INELIGIBLE"

    def test_g_unsupported_cannot_self_certify(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="self-cert",
                    source_key="unknown_blog",
                    statement="CPI is 9%",
                    metric_key="cpi_inflation",
                    value=9.0,
                    period="2026-08",
                    published_at="2026-08-01",
                    source_url="https://random.example/cpi",
                    trust_score=1.0,
                    authority_type="PRIMARY",
                ),
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                    trust_score=0.5,
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        by_id = {e.evidence_id: e for e in result.evaluations}
        assert by_id["self-cert"].authority_fit == "UNRELATED"
        assert result.preferred_evidence_ids[0] == "gastat-cpi"

    def test_h_user_document_not_official(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="user-doc",
                    source_key="user_upload",
                    source_type="document",
                    statement="My uploaded note on CPI",
                    metric_key="cpi_inflation",
                    value=5.0,
                    period="2026-08",
                    published_at="2026-08-01",
                    document_id=str(uuid.uuid4()),
                    chunk_id=str(uuid.uuid4()),
                    source_url=None,
                    authority_type="user",
                ),
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        by_id = {e.evidence_id: e for e in result.evaluations}
        assert by_id["user-doc"].authority_fit == "UNRELATED"
        assert result.preferred_evidence_ids[0] == "gastat-cpi"


class TestFreshness:
    def test_a_recent_current(self):
        state, _, reasons = evaluate_freshness(
            claim_type="INFLATION", published_at="2026-08-01", as_of=AS_OF
        )
        assert state == "CURRENT"
        assert any("within_current_window" in r for r in reasons)

    def test_b_older_stale(self):
        state, _, reasons = evaluate_freshness(
            claim_type="INFLATION", published_at="2024-01-01", as_of=AS_OF
        )
        assert state == "STALE"
        assert any("beyond_acceptable_window" in r for r in reasons)

    def test_c_unknown_published(self):
        state, _, reasons = evaluate_freshness(
            claim_type="INFLATION", published_at=None, as_of=AS_OF
        )
        assert state == "UNKNOWN"
        assert "published_at_missing" in reasons

    def test_d_retrieved_not_substitute(self):
        state, _, _ = evaluate_freshness(
            claim_type="GDP",
            published_at=None,
            retrieved_at="2026-09-13",
            as_of=AS_OF,
        )
        assert state == "UNKNOWN"

    def test_e_claim_specific_windows(self):
        pricing = evaluate_freshness(
            claim_type="PRICING", published_at="2026-05-01", as_of=AS_OF
        )[0]
        market = evaluate_freshness(
            claim_type="MARKET_SIZE", published_at="2026-05-01", as_of=AS_OF
        )[0]
        assert pricing == "ACCEPTABLE"
        assert market == "CURRENT"

    def test_f_regulation_not_age_stale(self):
        state, _, reasons = evaluate_freshness(
            claim_type="GENERAL_REGULATION",
            published_at="2000-01-01",
            as_of=AS_OF,
        )
        assert state == "NOT_APPLICABLE"
        assert "regulation_age_not_decisive" in reasons

    def test_g_future_date_not_current(self):
        state, _, reasons = evaluate_freshness(
            claim_type="INFLATION", published_at="2027-01-01", as_of=AS_OF
        )
        assert state == "UNKNOWN"
        assert "published_at_in_future" in reasons


class TestConflict:
    def test_a_same_scope_different_value(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="a",
                    source_key="gastat",
                    statement="CPI 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi-a",
                ),
                _cand(
                    evidence_id="b",
                    source_key="misa",
                    statement="CPI 2.1%",
                    metric_key="cpi_inflation",
                    value=2.1,
                    period="2026-08",
                    published_at="2026-08-10",
                    source_url="https://misa.gov.sa/en/cpi-b",
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert len(result.conflicts) == 1
        assert result.conflicts[0].status in {
            "RESOLVED_PREFERRED_SOURCE",
            "UNRESOLVED",
        }
        assert set(result.conflicts[0].candidates) == {"a", "b"}

    def test_b_different_period_not_conflict(self):
        a = _cand(
            evidence_id="a",
            source_key="gastat",
            metric_key="gdp_growth",
            value=3.0,
            period="2025",
            statement="GDP 2025",
            published_at="2026-01-01",
            source_url="https://www.stats.gov.sa/en/gdp-2025",
        )
        b = _cand(
            evidence_id="b",
            source_key="gastat",
            metric_key="gdp_growth",
            value=4.0,
            period="2026",
            statement="GDP 2026",
            published_at="2026-06-01",
            source_url="https://www.stats.gov.sa/en/gdp-2026",
        )
        assert classify_non_conflict(a, b) == "TEMPORAL_CHANGE"
        result = evaluate_research_quality(
            [a, b], question="Saudi GDP", claim_type="GDP", as_of=AS_OF
        )
        assert result.conflicts == []

    def test_c_different_geography_not_conflict(self):
        a = _cand(
            evidence_id="a",
            source_key="gastat",
            metric_key="cpi_inflation",
            value=1.6,
            period="2026-08",
            geography="SA",
            statement="National CPI",
            published_at="2026-08-15",
            source_url="https://www.stats.gov.sa/en/cpi",
        )
        b = _cand(
            evidence_id="b",
            source_key="gastat",
            metric_key="cpi_inflation",
            value=2.2,
            period="2026-08",
            geography="RIYADH",
            statement="Riyadh CPI",
            published_at="2026-08-15",
            source_url="https://www.stats.gov.sa/en/cpi-riyadh",
        )
        assert classify_non_conflict(a, b) == "SCOPE_MISMATCH"
        result = evaluate_research_quality(
            [a, b], question="Saudi CPI", claim_type="INFLATION", as_of=AS_OF
        )
        assert result.conflicts == []

    def test_d_duplicate_same_value_no_conflict(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="a",
                    source_key="gastat",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    statement="CPI 1.6",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi-a",
                ),
                _cand(
                    evidence_id="b",
                    source_key="gastat",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    statement="CPI 1.6 again",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi-b",
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert result.conflicts == []

    def test_e_primary_resolves(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="CPI 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                ),
                _cand(
                    evidence_id="blog-cpi",
                    source_key="macro_blog",
                    statement="CPI 3.0%",
                    metric_key="cpi_inflation",
                    value=3.0,
                    period="2026-08",
                    published_at="2026-08-20",
                    source_url="https://example.com/cpi",
                ),
            ],
            question="Saudi CPI inflation",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert len(result.conflicts) == 1
        c = result.conflicts[0]
        assert c.status == "RESOLVED_PREFERRED_SOURCE"
        assert c.preferred_evidence_ref == "gastat-cpi"
        assert "blog-cpi" in c.candidates

    def test_f_equal_quality_unresolved(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="blog-a",
                    source_key="blog_a",
                    statement="CPI inflation 1.5%",
                    metric_key="cpi_inflation",
                    value=1.5,
                    period="2026-08",
                    published_at="2026-08-10",
                    source_url="https://example.com/a",
                ),
                _cand(
                    evidence_id="blog-b",
                    source_key="blog_b",
                    statement="CPI inflation 1.9%",
                    metric_key="cpi_inflation",
                    value=1.9,
                    period="2026-08",
                    published_at="2026-08-11",
                    source_url="https://example.com/b",
                ),
            ],
            question="Saudi CPI inflation",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert len(result.conflicts) == 1
        assert result.conflicts[0].status == "UNRESOLVED"
        assert result.conflicts[0].preferred_evidence_ref is None

    def test_g_never_averaged(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="a",
                    source_key="gastat",
                    statement="CPI 1.0%",
                    metric_key="cpi_inflation",
                    value=1.0,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi-a",
                ),
                _cand(
                    evidence_id="b",
                    source_key="misa",
                    statement="CPI 3.0%",
                    metric_key="cpi_inflation",
                    value=3.0,
                    period="2026-08",
                    published_at="2026-08-10",
                    source_url="https://misa.gov.sa/en/cpi-b",
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        values = result.conflicts[0].values
        assert 2.0 not in values
        assert set(float(v) for v in values) == {1.0, 3.0}

    def test_h_non_selected_remains(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="CPI 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                ),
                _cand(
                    evidence_id="alt-cpi",
                    source_key="macro_blog",
                    statement="CPI 2.5%",
                    metric_key="cpi_inflation",
                    value=2.5,
                    period="2026-08",
                    published_at="2026-08-12",
                    source_url="https://example.com/alt",
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        c = result.conflicts[0]
        assert c.preferred_evidence_ref == "gastat-cpi"
        assert "alt-cpi" in c.candidates
        assert len(c.candidates) == 2

    def test_i_unit_mismatch_not_conflict(self):
        a = _cand(
            evidence_id="a",
            source_key="gastat",
            metric_key="cpi_inflation",
            value=1.6,
            period="2026-08",
            unit="percent",
            statement="CPI percent",
            published_at="2026-08-15",
            source_url="https://www.stats.gov.sa/en/cpi-pct",
        )
        b = _cand(
            evidence_id="b",
            source_key="gastat",
            metric_key="cpi_inflation",
            value=160,
            period="2026-08",
            unit="index",
            statement="CPI index",
            published_at="2026-08-15",
            source_url="https://www.stats.gov.sa/en/cpi-idx",
        )
        assert classify_non_conflict(a, b) == "SCOPE_MISMATCH"
        result = evaluate_research_quality(
            [a, b], question="Saudi CPI", claim_type="INFLATION", as_of=AS_OF
        )
        assert result.conflicts == []

    def test_market_signal_scope_aware(self):
        signals = [
            MarketSignal(
                metric="cpi_inflation",
                value=1.6,
                period="2026-08",
                source="gastat",
                evidence_reference="a",
                geography="SA",
                unit="percent",
            ),
            MarketSignal(
                metric="cpi_inflation",
                value=2.2,
                period="2026-08",
                source="gastat",
                evidence_reference="b",
                geography="RIYADH",
                unit="percent",
            ),
        ]
        assert detect_signal_conflicts(signals) == []


class TestEvidenceQuality:
    def test_primary_complete_high(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                    document_id=str(uuid.uuid4()),
                    chunk_id=str(uuid.uuid4()),
                )
            ],
            question="Saudi CPI inflation",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        ev = result.evaluations[0]
        assert ev.quality_state == "HIGH"
        assert ev.quality_score >= 80
        assert ev.authority_fit == "PRIMARY"
        assert result.policy_version == RESEARCH_QUALITY_POLICY_VERSION

    def test_stale_reflected(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="old",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.0%",
                    metric_key="cpi_inflation",
                    value=1.0,
                    period="2023-01",
                    published_at="2023-01-01",
                    source_url="https://www.stats.gov.sa/en/cpi-old",
                    document_id=str(uuid.uuid4()),
                )
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        ev = result.evaluations[0]
        assert ev.freshness == "STALE"
        assert ev.quality_components.freshness < 40

    def test_exact_beats_generic_official(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="misa-unrelated",
                    source_key="misa",
                    statement="Investment license counts",
                    metric_key="investor_licenses",
                    value=100,
                    period="2026-08",
                    published_at="2026-08-20",
                    source_url="https://misa.gov.sa/en/licenses",
                ),
                _cand(
                    evidence_id="gastat-cpi",
                    source_key="gastat",
                    statement="Saudi CPI inflation 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                ),
            ],
            question="Saudi CPI inflation",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert result.preferred_evidence_ids[0] == "gastat-cpi"

    def test_incomplete_provenance_reduces(self):
        complete = evaluate_research_quality(
            [
                _cand(
                    evidence_id="full",
                    source_key="gastat",
                    statement="CPI 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                    document_id=str(uuid.uuid4()),
                    chunk_id=str(uuid.uuid4()),
                )
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        ).evaluations[0]
        partial = evaluate_research_quality(
            [
                _cand(
                    evidence_id="partial",
                    source_key="gastat",
                    statement="CPI 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at=None,
                    source_url="https://www.stats.gov.sa/en/cpi2",
                    document_id=None,
                    chunk_id=None,
                )
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        ).evaluations[0]
        assert complete.quality_score > partial.quality_score
        assert partial.freshness == "UNKNOWN"

    def test_deterministic_repeat(self):
        cands = [
            _cand(
                evidence_id="gastat-cpi",
                source_key="gastat",
                statement="Saudi CPI inflation 1.6%",
                metric_key="cpi_inflation",
                value=1.6,
                period="2026-08",
                published_at="2026-08-15",
                source_url="https://www.stats.gov.sa/en/cpi",
                document_id="doc-1",
                chunk_id="chunk-1",
            )
        ]
        a = evaluate_research_quality(
            cands, question="Saudi CPI", claim_type="INFLATION", as_of=AS_OF
        )
        b = evaluate_research_quality(
            cands, question="Saudi CPI", claim_type="INFLATION", as_of=AS_OF
        )
        assert a.to_public_dict() == b.to_public_dict()
        assert a.policy_version == RESEARCH_QUALITY_POLICY_VERSION

    def test_no_llm_import_required(self):
        import ai_engine.research.quality.engine as eng

        src = Path(eng.__file__).read_text(encoding="utf-8")
        assert "openai" not in src.lower()
        assert "anthropic" not in src.lower()
        assert "ChatCompletion" not in src


class TestQualityPersistence:
    def test_persist_quality_metadata_survives_reload(self):
        db = _session()
        try:
            user = _user(db)
            study_id = f"s-8c2-{uuid.uuid4().hex[:8]}"
            doc_id, chunk_id = str(uuid.uuid4()), str(uuid.uuid4())
            db.add(
                models.KnowledgeDocument(
                    id=doc_id,
                    owner_id=user.id,
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
                    owner_id=user.id,
                    content="Saudi CPI rose 1.6% YoY.",
                    embedding=[],
                    chunk_metadata={},
                    importance=0.9,
                )
            )
            db.commit()

            claims = [
                ResearchClaim(
                    statement="Saudi CPI rose 1.6% YoY.",
                    source_type="official",
                    source_url="https://www.stats.gov.sa/en/cpi",
                    confidence=0.9,
                    source_key="gastat",
                    from_knowledge=True,
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    metric_key="cpi_inflation",
                    value=1.6,
                    unit="percent",
                    period="2026-08",
                    published_at="2026-08-15",
                    geography="SA",
                ),
                ResearchClaim(
                    statement="Assumed CPI 5%",
                    source_type="ai_assumption",
                    confidence=0.2,
                    source_key="model",
                    metric_key="cpi_inflation",
                    value=5.0,
                    unit="percent",
                    period="2026-08",
                    geography="SA",
                ),
            ]
            quality = evaluate_research_quality(
                claims,
                question="Saudi CPI inflation",
                claim_type="INFLATION",
                as_of=AS_OF,
            )
            for claim, item in zip(claims, enrich_claims_with_quality(claims, quality)):
                claim.research_quality = item.get("research_quality")

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
            result = ResearchResult(
                plan=plan,
                status="complete",
                claims=claims,
                knowledge_hits=1,
                research_quality=quality.to_public_dict(),
            )
            run = rps.persist_research_result(
                db,
                study_id=study_id,
                owner_id=user.id,
                user_id=str(user.id),
                result=result,
                research_type="gap_research",
            )
            assert run is not None
            run_id = run.id
            db.commit()
        finally:
            db.close()

        db2 = _session()
        try:
            run2 = db2.query(models.ResearchRun).filter(models.ResearchRun.id == run_id).one()
            rq = (run2.result_json or {}).get("research_quality") or {}
            assert rq.get("policy_version") == RESEARCH_QUALITY_POLICY_VERSION
            assert rq.get("claim_type") == "INFLATION"
            assert rq.get("preferred_evidence_ids")
            refs = (
                db2.query(models.ResearchEvidenceRef)
                .filter(models.ResearchEvidenceRef.research_run_id == run_id)
                .all()
            )
            assert refs
            gastat_refs = [r for r in refs if r.source_key == "gastat"]
            assert gastat_refs
            prov = gastat_refs[0].provenance_json or {}
            assert prov.get("claim_type") == "INFLATION" or (
                (prov.get("research_quality") or {}).get("claim_type") == "INFLATION"
            )
        finally:
            db2.close()

    def test_tenant_isolation(self):
        db = _session()
        try:
            u1 = _user(db)
            u2 = _user(db)
            study_id = f"s-8c2-t-{uuid.uuid4().hex[:8]}"
            plan = ResearchPlan(
                study_id=study_id,
                gaps=["FDI"],
                sources=[
                    ResearchSourceRef(
                        source_key="misa", connector_id="live.misa", reason="fdi"
                    )
                ],
                queries=["Saudi FDI"],
            )
            claim = ResearchClaim(
                statement="FDI inflow 19bn",
                source_type="official",
                source_url="https://misa.gov.sa/en/fdi",
                confidence=0.9,
                source_key="misa",
                metric_key="fdi_inflow",
                value=19,
                period="2025",
                published_at="2026-02-01",
                geography="SA",
            )
            quality = evaluate_research_quality(
                [claim],
                question="Saudi FDI",
                claim_type="INVESTMENT_FDI",
                as_of=AS_OF,
            )
            claim.research_quality = enrich_claims_with_quality([claim], quality)[0][
                "research_quality"
            ]
            result = ResearchResult(
                plan=plan,
                status="complete",
                claims=[claim],
                research_quality=quality.to_public_dict(),
            )
            run = rps.persist_research_result(
                db,
                study_id=study_id,
                owner_id=u1.id,
                user_id=str(u1.id),
                result=result,
            )
            assert run is not None
            db.commit()
            run_id = run.id
            assert rps.get_run(db, run_id=run_id, owner_id=u2.id) is None
            owned = rps.get_run(db, run_id=run_id, owner_id=u1.id)
            assert owned is not None
            assert (owned.result_json or {}).get("research_quality", {}).get(
                "claim_type"
            ) == "INVESTMENT_FDI"
        finally:
            db.close()


class TestControlledScenarios:
    def test_scenario_a_saudi_inflation(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="gastat-live-like",
                    source_key="gastat",
                    statement="Consumer Price Index (CPI) inflation rose 1.6% YoY",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/statistics-programs/cpi",
                    document_id=str(uuid.uuid4()),
                    chunk_id=str(uuid.uuid4()),
                )
            ],
            question="Saudi inflation CPI",
            as_of=AS_OF,
        )
        assert result.claim_type == "INFLATION"
        ev = result.evaluations[0]
        assert ev.authority_fit == "PRIMARY"
        assert ev.eligible is True
        assert ev.provenance in {"COMPLETE", "PARTIAL"}
        assert ev.freshness in {
            "CURRENT",
            "ACCEPTABLE",
            "STALE",
            "UNKNOWN",
            "NOT_APPLICABLE",
        }

    def test_scenario_b_saudi_fdi(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="misa-live-like",
                    source_key="misa",
                    statement="Foreign direct investment (FDI) inflow reached 19",
                    metric_key="fdi_inflow",
                    value=19,
                    period="2025",
                    published_at="2026-03-01",
                    source_url="https://misa.gov.sa/en/investment-statistics",
                    document_id=str(uuid.uuid4()),
                )
            ],
            question="Saudi FDI investment inflow",
            as_of=AS_OF,
        )
        assert result.claim_type == "INVESTMENT_FDI"
        assert result.evaluations[0].authority_fit == "PRIMARY"

    def test_scenario_c_conflict_fixture(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="gastat",
                    source_key="gastat",
                    statement="CPI 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at="2026-08-15",
                    source_url="https://www.stats.gov.sa/en/cpi",
                ),
                _cand(
                    evidence_id="blog",
                    source_key="blog",
                    statement="CPI 4.0%",
                    metric_key="cpi_inflation",
                    value=4.0,
                    period="2026-08",
                    published_at="2026-08-16",
                    source_url="https://example.com/cpi",
                ),
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert result.conflicts
        assert result.conflicts[0].status == "RESOLVED_PREFERRED_SOURCE"
        assert result.conflicts[0].preferred_evidence_ref == "gastat"

    def test_scenario_d_unknown_publication(self):
        result = evaluate_research_quality(
            [
                _cand(
                    evidence_id="undated",
                    source_key="gastat",
                    statement="CPI 1.6%",
                    metric_key="cpi_inflation",
                    value=1.6,
                    period="2026-08",
                    published_at=None,
                    retrieved_at="2026-09-13",
                    source_url="https://www.stats.gov.sa/en/cpi",
                )
            ],
            question="Saudi CPI",
            claim_type="INFLATION",
            as_of=AS_OF,
        )
        assert result.evaluations[0].freshness == "UNKNOWN"

    def test_market_signals_still_detect_same_scope_conflict(self):
        _, conflicts, status = research_market_signals(
            [
                {
                    "statement": "Inflation CPI 1.6% in 2026",
                    "source_type": "official",
                    "source_url": "https://www.stats.gov.sa/a",
                    "source_key": "gastat",
                    "geography": "SA",
                    "unit": "percent",
                },
                {
                    "statement": "Inflation CPI 2.2% in 2026",
                    "source_type": "official",
                    "source_url": "https://www.stats.gov.sa/b",
                    "source_key": "gastat",
                    "geography": "SA",
                    "unit": "percent",
                },
            ]
        )
        assert status == "CONFLICT"
        assert conflicts
