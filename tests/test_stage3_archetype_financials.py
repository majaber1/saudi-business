"""Stage 3 line items for specialty coffee and Saudi SaaS."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from ai_engine.models.study_state import Assumption, ProjectProfile, StudyState
from ai_engine.tools.archetype_lines import (
    project_archetype_lines,
    project_driver_scenario,
    rows_from_mapping,
)
from ai_engine.tools.calculator import calculate_npv
from ai_engine.tools.investment_trust import apply_investment_trust


def _coffee(**extra):
    values = {
        "avg_ticket": 25,
        "daily_covers": 80,
        "operating_days_per_month": 26,
        "rent_monthly": 15000,
        "labor_monthly": 18000,
        "food_cost_pct": 0.30,
        "fitout_capex": 400000,
        "discount_rate": {"value": 0.12, "origin": "user", "rate_representation": "RATIO"},
    }
    values.update(extra)
    return project_archetype_lines("fnb", rows_from_mapping(values))


def test_coffee_lines_match_monthly_formula_and_annual_sum():
    result = _coffee()
    by_id = {line["id"]: line for line in result["lines"]}
    assert by_id["revenue"]["monthly"] == 25 * 80 * 26
    assert by_id["rent"]["monthly"] == 15000
    assert by_id["payroll"]["monthly"] == 18000
    assert by_id["operating_cost"]["monthly"] == (25 * 80 * 26) * 0.30
    assert result["monthly_net"] == 3400
    assert result["annual_cash_flows"] == [3400 * 12]
    assert sum(result["monthly_cash_flows"]) == result["annual_cash_flows"][0]
    assert result["cash_flow_basis"] == "PRE_TAX_OPERATING_PROJECTION"
    assert result["tax_lines_included"] is False
    assert result["investment_grade"] is True
    assert result["npv"] == calculate_npv([-400000, 3400 * 12], 0.12)
    assert {item["key"] for item in by_id["revenue"]["lineage"]} == {
        "avg_ticket",
        "daily_covers",
        "operating_days_per_month",
    }


def test_missing_coffee_rent_is_not_zero_and_blocks_investment_grade():
    result = _coffee(rent_monthly=None)
    rent = next(line for line in result["lines"] if line["id"] == "rent")
    assert rent["monthly"] is None
    assert rent["status"] == "MISSING"
    assert result["monthly_net"] is None
    assert result["monthly_cash_flows"] is None
    assert result["investment_grade"] is False
    assert result["verdict_override"] == "INSUFFICIENT_EVIDENCE"
    state = StudyState(
        study_id="s",
        project_id="p",
        user_id="u",
        verdict="GO",
        financial_results=result,
    )
    assert apply_investment_trust(state).verdict == "INSUFFICIENT_EVIDENCE"


def test_estimated_payroll_cannot_authorize_go():
    result = _coffee(labor_monthly={"value": 18000, "origin": "ai_estimated", "ai_estimated": True})
    assert result["cost_verification"] == "UNVERIFIED_ESTIMATE"
    assert result["investment_grade"] is False
    assert result["verdict_override"] == "DEFER"
    assert result["npv"] is None
    state = StudyState(study_id="s", project_id="p", user_id="u", verdict="GO", financial_results=result)
    assert apply_investment_trust(state).verdict == "DEFER"


def test_bare_food_cost_percent_is_not_rescaled():
    result = _coffee(food_cost_pct=30)
    operating = next(line for line in result["lines"] if line["id"] == "operating_cost")
    assert operating["status"] == "AMBIGUOUS"
    assert operating["monthly"] is None
    assert result["verdict_override"] == "INSUFFICIENT_EVIDENCE"


def test_driver_scenario_is_reproducible_and_rejects_a_bare_multiplier():
    base = {
        "avg_ticket": 25,
        "daily_covers": 80,
        "operating_days_per_month": 26,
        "rent_monthly": 15000,
        "labor_monthly": 18000,
        "food_cost_pct": 0.30,
    }
    first = project_driver_scenario("fnb", base, {"rent_monthly": 20000})
    second = project_driver_scenario("fnb", base, {"rent_monthly": 20000})
    assert first["monthly_net"] == second["monthly_net"] == 3400 - 5000
    assert first["scenario_overrides"] == ["rent_monthly"]
    rejected = project_driver_scenario("fnb", base, {"multiplier": 1.2})
    assert rejected["reason"] == "bare_multiplier_rejected"
    assert rejected["investment_grade"] is False


def test_negative_coffee_cash_flow_is_not_a_go():
    result = _coffee(rent_monthly=80000)
    assert result["monthly_net"] < 0
    assert result["verdict_override"] == "NO_GO"
    state = StudyState(study_id="s", project_id="p", user_id="u", verdict="GO", financial_results=result)
    assert apply_investment_trust(state).verdict == "NO_GO"


def test_saas_lines_and_missing_hosting_are_explicit():
    complete = project_archetype_lines(
        "saas_digital",
        rows_from_mapping(
            {
                "mrr": 80000,
                "acquisition_cost_monthly": 20000,
                "hosting_monthly": 5000,
                "capex": 100000,
                "discount_rate": {"value": "10%", "origin": "user"},
            }
        ),
    )
    by_id = {line["id"]: line for line in complete["lines"]}
    assert by_id["subscription_revenue"]["monthly"] == 80000
    assert by_id["acquisition_cost"]["monthly"] == 20000
    assert by_id["hosting"]["monthly"] == 5000
    assert complete["monthly_net"] == 55000
    assert complete["annual_cash_flows"] == [55000 * 12]
    assert complete["discount_rate"] == 0.10
    missing = project_archetype_lines(
        "saas_digital",
        rows_from_mapping({"mrr": 80000, "acquisition_cost_monthly": 20000, "cac": 400, "target_customers": 100}),
    )
    hosting = next(line for line in missing["lines"] if line["id"] == "hosting")
    acquisition = next(line for line in missing["lines"] if line["id"] == "acquisition_cost")
    assert hosting["monthly"] is None
    assert hosting["status"] == "MISSING"
    assert acquisition["monthly"] == 20000
    assert missing["monthly_net"] is None
    assert missing["investment_grade"] is False


def test_edited_assumptions_make_the_previous_projection_stale():
    from ai_engine.tools.archetype_lines import mark_projection_stale, project_study_archetype

    state = StudyState(
        study_id="coffee",
        project_id="p",
        user_id="u",
        assumptions_version=2,
        profile=ProjectProfile(name="Coffee", sector="food", archetype="fnb"),
        assumptions=[
            Assumption(key="coffee_revenue_monthly", value="52000", source="user", confidence="confirmed", base="52000"),
            Assumption(key="rent_monthly", value="15000", source="user", confidence="confirmed", base="15000"),
            Assumption(key="labor_monthly", value="18000", source="user", confidence="confirmed", base="18000"),
            Assumption(key="other_operating_cost_monthly", value="15600", source="user", confidence="confirmed", base="15600"),
        ],
    )
    current = project_study_archetype(state)
    assert current is not None
    assert current["assumptions_version"] == 2
    assert current["monthly_net"] == 52000 - 15000 - 18000 - 15600
    stale = mark_projection_stale(current)
    assert stale["stale"] is True
    assert stale["monthly_net"] == current["monthly_net"]
    assert stale["investment_grade"] is False
    assert stale["verdict_override"] == "INSUFFICIENT_EVIDENCE"


def test_financial_analyst_uses_the_archetype_model_for_fnb():
    from ai_engine.agents.financial_analyst import run_financial_analysis

    state = StudyState(
        study_id="coffee",
        project_id="p",
        user_id="u",
        language="en",
        phase="READY_FOR_ANALYSIS",
        profile=ProjectProfile(name="Coffee", sector="food", archetype="fnb"),
        assumptions=[
            Assumption(key="avg_ticket", value="25", source="user", confidence="confirmed", base="25"),
            Assumption(key="daily_covers", value="80", source="user", confidence="confirmed", base="80"),
            Assumption(key="operating_days_per_month", value="26", source="user", confidence="confirmed", base="26"),
            Assumption(key="rent_monthly", value="15000", source="user", confidence="confirmed", base="15000"),
            Assumption(key="labor_monthly", value="18000", source="user", confidence="confirmed", base="18000"),
            Assumption(key="food_cost_pct", value="0.30", source="user", confidence="confirmed", base="0.30", rate_representation="RATIO"),
            Assumption(key="fitout_capex", value="400000", source="user", confidence="confirmed", base="400000"),
            Assumption(key="discount_rate", value="0.12", source="user", confidence="confirmed", base="0.12", rate_representation="RATIO"),
        ],
    )
    with patch("ai_engine.agents.financial_analyst.get_llm", side_effect=AssertionError("llm should not price this model")):
        analyzed = run_financial_analysis(state)
    assert analyzed.financial_results["model_family"] == "specialty_coffee"
    assert analyzed.financial_results["monthly_net"] == 3400
    assert analyzed.phase == "ANALYZED"
