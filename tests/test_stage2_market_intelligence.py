"""Stage 2 market intelligence: competitors, search, critic, and two study shapes."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from ai_engine.agents.decision import run_decision
from ai_engine.models.study_state import Assumption, Claim, ProjectProfile, StudyState
from ai_engine.research.market.competitor import research_competitors
from ai_engine.research.planner import (
    BLOCKED_SOURCES,
    archetype_research_questions,
    build_research_plan,
    extract_gaps_from_state,
)
from ai_engine.research.research_critic import review_claim_lineage
from ai_engine.research.schemas import ResearchClaim
from ai_engine.research.service import execute_research
from ai_engine.tools.search import execute_allowlisted_search, search_saudi_data


def _study(archetype: str, sector: str, city: str, idea: str) -> StudyState:
    return StudyState(
        study_id=f"stage2-{archetype}",
        project_id="p1",
        user_id="1",
        language="en",
        phase="EVIDENCE_REVIEW",
        profile=ProjectProfile(
            name=idea,
            sector=sector,
            archetype=archetype,  # type: ignore[arg-type]
            description=idea,
        ),
        structured_answers={"city": city, "business_idea": idea},
    )


def test_name_only_competitor_is_not_verified_and_url_is_not_invented():
    comps, status = research_competitors(
        business_idea="specialty coffee",
        sector="fnb",
        geography="Riyadh, Saudi Arabia",
        evidence_items=[{"competitor_name": "Barns Cafe", "statement": "Barns Cafe is nearby"}],
    )
    assert status == "NOT_VERIFIED"
    assert comps[0].status == "NOT_VERIFIED"
    assert comps[0].record_kind == "unverified_mention"
    assert comps[0].source_url is None
    assert comps[0].retrieved_at is None
    assert comps[0].rejection_reason == "missing_url"


def test_missing_url_stays_missing_even_with_a_timestamp():
    comps, status = research_competitors(
        business_idea="specialty coffee",
        sector="fnb",
        geography="Riyadh",
        evidence_items=[
            {
                "competitor_name": "Barns Cafe",
                "statement": "Barns Cafe sells coffee",
                "retrieved_at": "2026-08-15",
            }
        ],
    )
    assert status == "NOT_VERIFIED"
    assert comps[0].source_url is None
    assert comps[0].retrieved_at == "2026-08-15"


def test_invalid_timestamp_is_not_replaced():
    item = {
        "competitor_name": "Barns Cafe",
        "statement": "Barns Cafe sells coffee",
        "source_url": "https://example.com/barns",
        "retrieved_at": "tomorrow",
    }
    comps, status = research_competitors(
        business_idea="specialty coffee",
        sector="fnb",
        geography="Riyadh",
        evidence_items=[item],
    )
    assert status == "NOT_VERIFIED"
    assert comps[0].rejection_reason == "invalid_timestamp"
    assert comps[0].retrieved_at is None
    assert item["retrieved_at"] == "tomorrow"


def test_geographic_mismatch_is_not_verified():
    comps, status = research_competitors(
        business_idea="specialty coffee",
        sector="fnb",
        geography="Riyadh, Saudi Arabia",
        evidence_items=[
            {
                "competitor_name": "Dubai Roast",
                "statement": "Dubai Roast operates in Dubai",
                "source_url": "https://example.com/dubai-roast",
                "retrieved_at": "2026-08-15T10:00:00Z",
                "location": "Dubai",
                "publisher": "Example Publisher",
            }
        ],
    )
    assert status == "NOT_VERIFIED"
    assert comps[0].rejection_reason == "geographic_mismatch"
    assert comps[0].location == "Dubai"
    assert comps[0].publisher == "Example Publisher"


def test_verified_competitor_keeps_provenance_and_duplicates_collapse():
    comps, status = research_competitors(
        business_idea="specialty coffee",
        sector="fnb",
        geography="Riyadh, Saudi Arabia",
        evidence_items=[
            {
                "competitor_name": "Acme Retail Co",
                "statement": "Acme Retail Co operates in Riyadh",
                "source_url": "https://www.stats.gov.sa/en/competitor",
                "retrieved_at": "2026-08-15",
                "publisher": "GASTAT",
                "location": "Riyadh",
                "source_key": "gastat",
            },
            {
                "competitor_name": "Acme Retail Company",
                "statement": "Acme Retail Company operates in Riyadh",
                "source_url": "https://www.stats.gov.sa/en/competitor",
                "retrieved_at": "2026-08-15",
                "publisher": "GASTAT",
                "location": "Riyadh",
            },
        ],
    )
    assert status == "VERIFIED"
    verified = [c for c in comps if c.status == "VERIFIED"]
    assert len(verified) == 1
    assert verified[0].record_kind == "verified_record"
    assert verified[0].publisher == "GASTAT"
    assert verified[0].location == "Riyadh"
    assert verified[0].retrieved_at == "2026-08-15"
    assert verified[0].supporting_claim


def test_conflicting_saudi_cities_are_not_merged_into_one_verified_record():
    comps, _status = research_competitors(
        business_idea="cafe",
        sector="fnb",
        geography="Saudi Arabia",
        evidence_items=[
            {
                "competitor_name": "Acme Retail Co",
                "statement": "Acme Retail Co in Riyadh",
                "source_url": "https://example.com/riyadh",
                "retrieved_at": "2026-08-15",
                "location": "Riyadh",
            },
            {
                "competitor_name": "Acme Retail Company",
                "statement": "Acme Retail Company in Jeddah",
                "source_url": "https://example.com/jeddah",
                "retrieved_at": "2026-08-15",
                "location": "Jeddah",
            },
        ],
    )
    assert comps
    assert all(c.status == "NOT_VERIFIED" for c in comps)
    assert all(c.rejection_reason == "geographic_or_identity_conflict" for c in comps)


def test_missing_model_is_labeled_as_a_deterministic_fallback():
    from langchain_core.messages import HumanMessage

    from ai_engine.agents.discovery import run_discovery
    from ai_engine.provider import ProviderUnavailableError

    state = StudyState(
        study_id="coffee-fallback",
        project_id="p1",
        user_id="1",
        language="en",
        messages=[HumanMessage(content="A specialty coffee shop in Riyadh")],
    )
    with patch(
        "ai_engine.agents.discovery.invoke_llm",
        side_effect=ProviderUnavailableError("GROQ_API_KEY is not set"),
    ):
        classified = run_discovery(state)
    assert classified.profile is not None
    assert classified.profile.archetype == "fnb"
    assert classified.profile.classification_source == "deterministic_fallback"
    assert classified.profile.archetype_confirmed is False
    assert "temporarily unavailable" in classified.messages[-1].content


def test_search_without_a_provider_is_blocked_and_empty():
    result = asyncio.run(
        search_saudi_data("Riyadh specialty coffee competitors", environ={})
    )
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "NO_ALLOWLISTED_PROVIDER_CONFIGURED"
    assert result["results"] == []
    assert result["implemented"] is False


class _SearchResponse:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class _SearchClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "headers": dict(kwargs.get("headers") or {})})
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_tavily_fixture_keeps_only_real_urls_and_hides_the_key():
    secret = "tavily-test-secret"
    client = _SearchClient(
        [
            _SearchResponse(
                200,
                {
                    "results": [
                        {"title": "Cafe page", "url": "https://example.com/cafe", "content": "menu"},
                        {"title": "Duplicate", "url": "https://example.com/cafe", "content": "again"},
                        {"title": "Bad", "url": "javascript:alert(1)", "content": "no"},
                        {"title": "No url", "content": "missing"},
                    ]
                },
            )
        ]
    )
    result = asyncio.run(
        search_saudi_data(
            "Riyadh specialty coffee",
            environ={"TAVILY_API_KEY": secret},
            client=client,
        )
    )
    assert result["status"] == "partial"
    assert result["provider"] == "tavily"
    assert result["results"] == [
        {
            "title": "Cafe page",
            "url": "https://example.com/cafe",
            "snippet": "menu",
            "retrieved_at": result["retrieved_at"],
            "provider": "tavily",
        }
    ]
    assert secret not in str(result)
    assert client.calls[0]["url"] == "https://api.tavily.com/search"
    assert client.calls[0]["headers"]["Authorization"] == f"Bearer {secret}"


def test_brave_rate_limit_and_server_retry_do_not_invent_hits():
    import httpx

    limited = _SearchClient([_SearchResponse(429, {"web": {"results": [{"url": "https://example.com/a"}]}})])
    blocked = asyncio.run(
        search_saudi_data(
            "Riyadh coffee price",
            environ={"BRAVE_SEARCH_API_KEY": "brave-test-secret"},
            client=limited,
        )
    )
    assert blocked["reason"] == "RATE_LIMIT"
    assert blocked["results"] == []
    assert len(limited.calls) == 1

    retried = _SearchClient(
        [
            _SearchResponse(503, {}),
            _SearchResponse(200, {"web": {"results": [{"title": "Price", "url": "https://example.com/price", "description": "SAR"}]}}),
        ]
    )
    recovered = asyncio.run(
        search_saudi_data("Riyadh coffee price", environ={"BRAVE_SEARCH_API_KEY": "brave-test-secret"}, client=retried)
    )
    assert recovered["status"] == "complete"
    assert recovered["results"][0]["url"] == "https://example.com/price"
    assert len(retried.calls) == 2
    assert retried.calls[0]["url"] == "https://api.search.brave.com/res/v1/web/search"

    timed = _SearchClient([httpx.TimeoutException("slow"), httpx.TimeoutException("slow")])
    failed = asyncio.run(
        search_saudi_data("Riyadh coffee price", environ={"BRAVE_SEARCH_API_KEY": "brave-test-secret"}, client=timed)
    )
    assert failed["reason"] == "TIMEOUT"
    assert failed["results"] == []
    assert "brave-test-secret" not in str(failed)


def test_search_timeout_rate_limit_invalid_source_and_partial_hits():
    timeout = execute_allowlisted_search(
        "cpi",
        source="general",
        transport=lambda _query: (_ for _ in ()).throw(TimeoutError()),
    )
    assert timeout["status"] == "failed"
    assert timeout["reason"] == "TIMEOUT"
    assert timeout["results"] == []

    limited = execute_allowlisted_search(
        "cpi",
        source="gastat",
        transport=lambda _query: {"status_code": 429, "results": [{"url": "https://example.com"}]},
    )
    assert limited["reason"] == "RATE_LIMIT"
    assert limited["results"] == []

    invalid = execute_allowlisted_search("cpi", source="open_web_scrape")
    assert invalid["reason"] == "INVALID_SOURCE"
    assert invalid["results"] == []

    partial = execute_allowlisted_search(
        "cpi",
        source="official",
        transport=lambda _query: {
            "retrieved_at": "2026-08-15T00:00:00Z",
            "results": [
                {"title": "CPI", "url": "https://www.stats.gov.sa/cpi", "snippet": "1.6%"},
                {"title": "No URL", "snippet": "missing"},
            ],
        },
    )
    assert partial["status"] == "partial"
    assert len(partial["results"]) == 1
    assert partial["results"][0]["url"] == "https://www.stats.gov.sa/cpi"
    assert partial["results"][0]["retrieved_at"] == "2026-08-15T00:00:00Z"

    undated = execute_allowlisted_search(
        "cpi",
        source="official",
        transport=lambda _query: {"results": [{"url": "https://www.stats.gov.sa/cpi"}]},
    )
    assert undated["results"] == []
    assert undated["reason"] == "MISSING_RETRIEVAL_TIMESTAMP"

    empty = execute_allowlisted_search(
        "Riyadh coffee competitors",
        source="general",
        transport=lambda _query: {"retrieved_at": "2026-10-28T00:00:00Z", "results": []},
    )
    assert empty["status"] == "failed"
    assert empty["reason"] == "NO_VALID_HITS"
    assert empty["results"] == []


def test_critic_separates_estimates_and_rejects_a_foreign_citation():
    review = review_claim_lineage(
        [
            ResearchClaim(
                statement="GASTAT CPI is 1.6% in Saudi Arabia",
                source_type="official",
                source_url="https://www.stats.gov.sa/en/cpi",
            ),
            ResearchClaim(
                statement="Dubai rent is SAR 80 and USD 20",
                source_type="official",
                source_url="https://example.com/dubai",
            ),
            Claim(statement="I assume margin is 40%", source_type="ai_assumption", confidence=0.4),
        ],
        geography="Riyadh, Saudi Arabia",
    )
    assert review["source_backed_count"] == 1
    assert review["ai_estimates"]
    assert any("geographic_mismatch" in row["reasons"] or "conflicting_currency" in row["reasons"] for row in review["rejected"])
    assert review["blocks_investment"] is False


def test_provider_error_is_not_reported_as_complete_research():
    plan = build_research_plan(study_id="err", gaps=["Saudi inflation CPI"])
    with patch("ai_engine.research.service._knowledge_retrieve", return_value=[]):
        with patch(
            "ai_engine.research.service._live_fetch",
            return_value=(
                [
                    ResearchClaim(
                        statement="CPI 1.6%",
                        source_type="official",
                        source_url="https://www.stats.gov.sa/cpi",
                        source_key="gastat",
                    )
                ],
                {"source_key": "gastat", "outcome": "ok"},
                [],
            ),
        ):
            with patch(
                "ai_engine.research.market.service.execute_market_research",
                side_effect=RuntimeError("market provider down"),
            ):
                result = execute_research(plan)
    assert result.status != "complete"
    assert result.errors
    assert any("market provider down" in err for err in result.errors)


def test_riyadh_coffee_and_saudi_saas_do_not_get_a_favorable_decision():
    coffee = _study("fnb", "food", "Riyadh", "Riyadh specialty coffee shop")
    saas = _study("saas_digital", "software", "Riyadh", "Saudi B2B SaaS")
    for state, archetype in ((coffee, "fnb"), (saas, "saas_digital")):
        gaps = extract_gaps_from_state(state)
        assert archetype_research_questions(archetype, "Riyadh")
        assert any("Competitor set" in gap for gap in gaps)
        assert any("Pricing" in gap for gap in gaps)
        assert any("Licensing" in gap for gap in gaps)
        plan = build_research_plan(study_id=state.study_id, gaps=gaps)
        blocked = {src.source_key: src for src in plan.sources if src.blocked}
        assert "monshaat" in blocked
        assert blocked["monshaat"].block_reason == BLOCKED_SOURCES["monshaat"]["reason"]
        assert plan.gaps
        state.research_status = "failed"
        state.research_context = {
            "status": "failed",
            "evidence_created": False,
            "research_critic": {"blocks_investment": True, "unresolved_gaps": gaps},
        }
        state.phase = "DECISION_READY"
        state.claims = [
            Claim(statement="Pricing for this business is observed.", source_type="user_input", confidence=0.8),
            Claim(statement="Competitors exist in the district.", source_type="user_input", confidence=0.8),
            Claim(statement="Demand from customers is reported by the owner.", source_type="user_input", confidence=0.8),
        ]
        state.assumptions = [
            Assumption(key="capex", value="500000", source="user", confidence="confirmed", base="500000"),
            Assumption(key="monthly_fixed_opex", value="20000", source="user", confidence="confirmed", base="20000"),
            Assumption(key="revenue_year1", value="400000", source="user", confidence="confirmed", base="400000"),
            Assumption(key="discount_rate", value="12%", source="user", confidence="confirmed", base="12%"),
        ]
        state.financial_results = {
            "npv": 1000,
            "irr": 0.2,
            "irr_available": True,
            "payback_months": 18,
            "payback_available": True,
            "investment_grade": True,
            "cost_verification": "OWNER_SUPPLIED",
        }
        mock = MagicMock()
        mock.invoke.return_value = MagicMock(
            content='```json\n{"verdict": "GO", "rationale": "proceed", "conditions": []}\n```'
        )
        with patch("ai_engine.agents.decision.get_llm", return_value=mock):
            decided = run_decision(state)
        assert decided.verdict not in {"GO", "GO_WITH_CONDITIONS", "CONDITIONAL_GO"}
        assert decided.research_status == "failed"


def test_critic_does_not_fabricate_a_replacement_url():
    review = review_claim_lineage(
        [ResearchClaim(statement="Official claim without a page", source_type="official", source_url=None)]
    )
    assert review["rejected"]
    assert review["rejected"][0]["source_url"] is None
    assert review["blocks_investment"] is True
    assert "missing_http_url" in review["rejected"][0]["reasons"]
