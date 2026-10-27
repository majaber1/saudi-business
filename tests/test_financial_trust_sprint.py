"""Stage 1 financial trust: estimated costs and ambiguous rates cannot authorize GO."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

if not os.environ.get("DATABASE_URL"):
    _tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _tmp.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_ROOT / "financial-engine"))

from ai_engine.agents.decision import run_decision  # noqa: E402
from ai_engine.agents.financial_analyst import (  # noqa: E402
    _deterministic_extract,
    run_financial_analysis,
)
from ai_engine.models.study_state import Assumption, Claim, ProjectProfile, StudyState  # noqa: E402
from ai_engine.orchestrator import build_graph  # noqa: E402
from app.api.financial import FeasibilityRequest  # noqa: E402
from app.services.financial_projection import project_cash_flows  # noqa: E402
from rate_contract import resolve_api_discount_rate  # noqa: E402


def _state(**assumptions: str) -> StudyState:
    rows = [
        Assumption(key=key, value=value, source="user", confidence="confirmed", base=value)
        for key, value in assumptions.items()
    ]
    return StudyState(
        study_id="trust-sprint",
        project_id="p1",
        user_id="u1",
        language="en",
        phase="READY_FOR_ANALYSIS",
        assumptions=rows,
        profile=ProjectProfile(
            name="Services",
            sector="services",
            archetype="services",
            description="professional services",
        ),
    )


def _mock_llm():
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content='```json\n{"verdict": "GO", "rationale": "proceed", "conditions": [], "analysis_complete": true}\n```'
    )
    return mock


def test_research_node_remains_on_the_production_graph():
    graph = build_graph()
    assert "research" in graph.nodes


def test_fifty_five_percent_cost_stays_unverified_and_cannot_go():
    state = _state(
        billing_rate="350",
        utilization_rate="70%",
        consultants_headcount="20",
        initial_investment="500000",
    )
    extracted = _deterministic_extract(state)
    assert "services_opex_defaulted_from_55pct_cost_ratio" in extracted["extract_notes"]
    assert extracted["cost_verification"] == "UNVERIFIED_ESTIMATE"

    with patch("ai_engine.agents.financial_analyst.get_llm", return_value=_mock_llm()):
        analyzed = run_financial_analysis(state)
    assert analyzed.financial_results["investment_grade"] is False
    assert analyzed.financial_results["cost_verification"] == "UNVERIFIED_ESTIMATE"

    # Evidence themes are present, so a GO from the model is legal until the cost gate.
    analyzed.claims = [
        Claim(statement="Pricing is a professional services fee.", source_type="user_input", confidence=0.8),
        Claim(statement="Competitors are established consulting firms.", source_type="user_input", confidence=0.8),
        Claim(statement="Demand from customers supports the practice.", source_type="user_input", confidence=0.8),
    ]
    analyzed.phase = "DECISION_READY"
    with patch("ai_engine.agents.decision.get_llm", return_value=_mock_llm()):
        decided = run_decision(analyzed)
    assert decided.verdict == "DEFER"
    assert decided.verdict not in {"GO", "GO_WITH_CONDITIONS"}


def test_forty_five_percent_cost_fill_is_an_unverified_estimate():
    state = _state(arr="1000000", initial_investment="250000")
    extracted = _deterministic_extract(state)
    assert "opex_defaulted_from_45pct_of_revenue_missing_cost_inputs" in extracted["extract_notes"]
    assert extracted["cost_verification"] == "UNVERIFIED_ESTIMATE"
    assert extracted["annual_costs"][0] == pytest.approx(450000)


def test_bare_discount_rate_is_not_rescaled_and_blocks_a_favorable_result():
    state = _state(
        initial_investment="500000",
        monthly_fixed_opex="20000",
        revenue_year1="400000",
        discount_rate="12",
    )
    with patch("ai_engine.agents.financial_analyst.get_llm", return_value=_mock_llm()):
        analyzed = run_financial_analysis(state)
    assert analyzed.financial_results["discount_rate_status"] == "AMBIGUOUS"
    assert analyzed.financial_results.get("npv") is None
    assert analyzed.financial_results["investment_grade"] is False
    analyzed.phase = "DECISION_READY"
    with patch("ai_engine.agents.decision.get_llm", return_value=_mock_llm()):
        decided = run_decision(analyzed)
    assert decided.verdict == "INSUFFICIENT_EVIDENCE"


def test_percent_sign_and_explicit_ratio_are_accepted():
    percent = _deterministic_extract(
        _state(initial_investment="1000", monthly_fixed_opex="10", discount_rate="12%")
    )
    assert percent["discount_rate"] == pytest.approx(0.12)
    assert percent["discount_rate_status"] == "EXPLICIT"

    labeled = _state(initial_investment="1000", monthly_fixed_opex="10", discount_rate="0.12")
    labeled.assumptions[-1].rate_representation = "RATIO"
    explicit = _deterministic_extract(labeled)
    assert explicit["discount_rate"] == pytest.approx(0.12)


def test_historical_ratio_boundary_is_preserved_and_bare_twelve_is_rejected():
    ratio, label = resolve_api_discount_rate(0.10, None)
    assert ratio == pytest.approx(0.10)
    assert label == "RATIO"
    request = FeasibilityRequest(investment=1000, annual_cash_flows=[100, 100], discount_rate=0.10)
    assert request.discount_rate == pytest.approx(0.10)
    assert request.discount_rate_representation == "RATIO"
    with pytest.raises(ValidationError):
        FeasibilityRequest(investment=1000, annual_cash_flows=[100], discount_rate=12)
    percent = FeasibilityRequest(
        investment=1000,
        annual_cash_flows=[100],
        discount_rate=12,
        discount_rate_representation="PERCENT",
    )
    assert percent.discount_rate == pytest.approx(0.12)


def test_projection_does_not_invent_zero_opex_or_rescale_stored_discount():
    investment, flows, rate = project_cash_flows(
        {"capex": 500000, "revenue_year1": 100000, "opex_annual": 20000, "growth_rate": 0.10, "horizon_years": 3}
    )
    assert investment == 500000
    assert rate == pytest.approx(0.10)
    assert flows == [100000 - 20000, 100000 * 1.10 - 20000, 100000 * 1.10**2 - 20000]
    with pytest.raises(ValueError, match="not treated as zero"):
        project_cash_flows({"capex": 1, "revenue_year1": 1})
    with pytest.raises(ValueError, match="not rescaled"):
        project_cash_flows({"capex": 1, "revenue_year1": 1, "opex_annual": 1, "discount_rate": 12})
