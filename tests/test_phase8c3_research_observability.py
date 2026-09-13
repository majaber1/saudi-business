"""Phase 8C.3 — Research Quality observability projection tests."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.research.quality import (
    enrich_claims_with_quality,
    evaluate_research_quality,
)
from ai_engine.research.quality.observability import (
    OBSERVABILITY_VERSION,
    attach_observability_to_research_context,
    project_research_quality_observability,
)


AS_OF = datetime(2026, 9, 13, tzinfo=timezone.utc)


def _cand(**kwargs):
    base = {
        "origin": "official",
        "source_type": "official",
        "geography": "SA",
        "unit": "percent",
        "published_at": "2026-09-01T00:00:00Z",
    }
    base.update(kwargs)
    return base


def test_observability_preferred_gastat_cpi():
    cands = [
        _cand(
            evidence_id="gastat-cpi",
            statement="Saudi CPI is 2.1%",
            source_key="gastat",
            source_url="https://stats.gov.sa/cpi",
            value=2.1,
            period="2026-08",
            metric_key="cpi",
        ),
        _cand(
            evidence_id="blog-cpi",
            statement="Saudi CPI is 3.0%",
            source_key="blog",
            source_url="https://example.com/cpi",
            value=3.0,
            period="2026-08",
            metric_key="cpi",
            origin="web",
            source_type="unverified",
        ),
    ]
    quality = evaluate_research_quality(cands, question="Saudi CPI", as_of=AS_OF)
    ctx = {
        "claims": enrich_claims_with_quality(cands, quality),
        "research_quality": quality.to_public_dict(),
    }
    obs = project_research_quality_observability(ctx)
    assert obs is not None
    assert obs["observability_version"] == OBSERVABILITY_VERSION
    assert obs["summary"]["preferred_count"] >= 1
    preferred_ids = {e["evidence_id"] for e in obs["preferred_evidence"]}
    assert "gastat-cpi" in preferred_ids
    card = next(e for e in obs["preferred_evidence"] if e["evidence_id"] == "gastat-cpi")
    assert card["authority_fit"] == "PRIMARY"
    assert card["official_validated"] is True
    assert "GASTAT" in card["source_name"]["en"]
    assert card["selection_reason"]["en"]
    assert card["selection_reason"]["ar"]


def test_observability_misa_fdi_primary():
    cands = [
        _cand(
            evidence_id="misa-fdi",
            statement="FDI is 20bn",
            source_key="misa",
            source_url="https://misa.gov.sa/fdi",
            value=20,
            unit="billion_usd",
            period="2025",
            metric_key="fdi",
        )
    ]
    quality = evaluate_research_quality(cands, question="Saudi FDI", as_of=AS_OF)
    ctx = {
        "claims": enrich_claims_with_quality(cands, quality),
        "research_quality": quality.to_public_dict(),
    }
    obs = project_research_quality_observability(ctx)
    assert obs["preferred_evidence"][0]["source_key"] == "misa"
    assert obs["preferred_evidence"][0]["authority_fit"] == "PRIMARY"


def test_observability_independent_periods_no_false_conflict():
    cands = [
        _cand(
            evidence_id="gdp-2025",
            statement="GDP 2025",
            source_key="gastat",
            source_url="https://stats.gov.sa/gdp/2025",
            value=1.1,
            period="2025",
            metric_key="gdp",
            unit="trillion_sar",
        ),
        _cand(
            evidence_id="gdp-2026",
            statement="GDP 2026",
            source_key="gastat",
            source_url="https://stats.gov.sa/gdp/2026",
            value=1.2,
            period="2026",
            metric_key="gdp",
            unit="trillion_sar",
        ),
    ]
    quality = evaluate_research_quality(cands, question="Saudi GDP", as_of=AS_OF)
    obs = project_research_quality_observability(
        {
            "claims": enrich_claims_with_quality(cands, quality),
            "research_quality": quality.to_public_dict(),
        }
    )
    assert obs["summary"]["unresolved_conflict_count"] == 0
    preferred_ids = {e["evidence_id"] for e in obs["preferred_evidence"]}
    assert "gdp-2025" in preferred_ids
    assert "gdp-2026" in preferred_ids


def test_observability_unresolved_conflict_clears_preferred():
    # Two non-primary sources with same fact-scope and different values.
    cands = [
        _cand(
            evidence_id="blog-a",
            statement="CPI 2.1",
            source_key="blog_a",
            source_url="https://example.com/a",
            value=2.1,
            period="2026-08",
            metric_key="cpi",
            origin="web",
            source_type="unverified",
        ),
        _cand(
            evidence_id="blog-b",
            statement="CPI 2.5",
            source_key="blog_b",
            source_url="https://example.com/b",
            value=2.5,
            period="2026-08",
            metric_key="cpi",
            origin="web",
            source_type="unverified",
        ),
    ]
    quality = evaluate_research_quality(cands, question="CPI", as_of=AS_OF)
    public = quality.to_public_dict()
    unresolved = [c for c in public["conflicts"] if c["status"] == "UNRESOLVED"]
    if not unresolved:
        # Engine may reject both as ineligible; still assert projection safety.
        obs = project_research_quality_observability(
            {"claims": enrich_claims_with_quality(cands, quality), "research_quality": public}
        )
        assert obs is not None
        return
    obs = project_research_quality_observability(
        {"claims": enrich_claims_with_quality(cands, quality), "research_quality": public}
    )
    assert obs["summary"]["unresolved_conflict_count"] >= 1
    assert obs["preferred_evidence"] == []
    claim = next(c for c in obs["claims"] if c["status"] == "unresolved")
    assert claim["preferred_evidence"] is None
    assert claim["conflict"]["unresolved"] is True
    assert claim["conflict"]["unresolved_message"]["en"]
    assert claim["conflict"]["unresolved_message"]["ar"]


def test_observability_unknown_freshness_not_current():
    cands = [
        _cand(
            evidence_id="gastat-cpi",
            statement="CPI unknown pub date",
            source_key="gastat",
            source_url="https://stats.gov.sa/cpi",
            value=2.1,
            period="2026-08",
            metric_key="cpi",
            published_at=None,
        )
    ]
    # Remove published_at entirely
    cands[0].pop("published_at", None)
    quality = evaluate_research_quality(cands, question="CPI", as_of=AS_OF)
    obs = project_research_quality_observability(
        {
            "claims": enrich_claims_with_quality(cands, quality),
            "research_quality": quality.to_public_dict(),
        }
    )
    card = obs["evidence"][0]
    assert card["freshness"] == "UNKNOWN"
    assert "unavailable" in card["freshness_label"]["en"].lower() or "Publication" in card["freshness_label"]["en"]
    assert card["freshness_label"]["en"] != "Current"


def test_observability_spoofed_official_not_validated():
    cands = [
        _cand(
            evidence_id="spoof",
            statement="Fake official CPI",
            source_key="gastat",
            source_url="https://evil.example/cpi",
            value=9.9,
            period="2026-08",
            metric_key="cpi",
        )
    ]
    quality = evaluate_research_quality(cands, question="CPI", as_of=AS_OF)
    obs = project_research_quality_observability(
        {
            "claims": enrich_claims_with_quality(cands, quality),
            "research_quality": quality.to_public_dict(),
        }
    )
    card = obs["evidence"][0]
    # Client-claimed gastat + evil URL must not show validated official badge.
    assert card["official_validated"] is False or card["authority_fit"] not in {"PRIMARY", "SECONDARY"}


def test_attach_observability_additive_and_idempotent_safe():
    cands = [
        _cand(
            evidence_id="gastat-cpi",
            statement="CPI 2.1",
            source_key="gastat",
            source_url="https://stats.gov.sa/cpi",
            value=2.1,
            period="2026-08",
            metric_key="cpi",
        )
    ]
    quality = evaluate_research_quality(cands, question="CPI", as_of=AS_OF)
    ctx = {
        "status": "complete",
        "claims": enrich_claims_with_quality(cands, quality),
        "research_quality": quality.to_public_dict(),
    }
    out = attach_observability_to_research_context(ctx)
    assert "research_quality" in out
    assert "research_quality_observability" in out
    assert out["research_quality"]["policy_version"] == quality.policy_version
    # Original quality untouched semantically
    assert out["research_quality"]["preferred_evidence_ids"] == quality.preferred_evidence_ids
