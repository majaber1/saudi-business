"""Citation critic: unsourced official claims never become evidence."""
from __future__ import annotations

from ai_engine.research.citation_critic import screen_research_citations
from ai_engine.research.nodes.research import merge_evidence_claims
from ai_engine.research.schemas import ResearchClaim


def test_unsourced_official_claim_is_not_stored_as_evidence():
    claim = ResearchClaim(
        statement="Invented CPI is 9%",
        source_type="official",
        source_url=None,
        retrieved_date=None,
    )
    accepted, notes = screen_research_citations([claim])
    assert accepted == []
    assert notes == ["rejected_unsourced:official"]
    assert claim.source_url is None
    assert claim.retrieved_date is None
    assert merge_evidence_claims([], accepted) == []


def test_critic_does_not_invent_a_url_for_a_document_claim():
    claim = ResearchClaim(
        statement="Internal note without a source",
        source_type="document",
        source_url="   ",
    )
    accepted, notes = screen_research_citations([claim])
    assert accepted == []
    assert notes == ["rejected_unsourced:document"]
    assert claim.source_url == "   "


def test_gastat_and_misa_claims_with_url_and_timestamp_are_kept():
    gastat = ResearchClaim(
        statement="GASTAT CPI 1.6%",
        source_type="official",
        source_url="https://www.stats.gov.sa/en/cpi",
        retrieved_date="2026-08-15",
        source_key="gastat",
    )
    misa = ResearchClaim(
        statement="MISA investment climate note",
        source_type="official",
        source_url="https://misa.gov.sa/en/",
        retrieved_date="2026-08-15",
        source_key="misa",
    )
    accepted, notes = screen_research_citations([gastat, misa])
    assert notes == []
    assert [c.source_key for c in accepted] == ["gastat", "misa"]
    assert accepted[0].retrieved_date == "2026-08-15"
    merged = merge_evidence_claims([], accepted)
    assert {c.source_type for c in merged} == {"official"}
    assert all(c.source_url and c.source_url.startswith("https://") for c in merged)


def test_user_assumption_is_not_promoted_to_official():
    claim = ResearchClaim(
        statement="Owner expects 20% margin",
        source_type="ai_assumption",
        source_url=None,
    )
    accepted, notes = screen_research_citations([claim])
    assert notes == []
    assert accepted[0].source_type == "ai_assumption"
    assert accepted[0].source_url is None
