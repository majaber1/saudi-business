"""Coffee Quality Parity — targeted correctness tests (no Claude numbers as defaults)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

if not os.environ.get("DATABASE_URL"):
    _tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _tmp.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "backend"))

from ai_engine.agents.assumption import _default_value_for_field  # noqa: E402
from ai_engine.agents.financial_analyst import (  # noqa: E402
    _deterministic_extract,
    run_financial_analysis,
)
from ai_engine.agents.fnb_financial_extract import extract_fnb_financials  # noqa: E402
from ai_engine.hardening.assumption_semantics import (  # noqa: E402
    map_origin_to_provenance,
    validate_assumption_value,
)
from ai_engine.hardening.financial_gates import evaluate_financial_trust_gates  # noqa: E402
from ai_engine.models.study_state import Assumption, ProjectProfile, StudyState  # noqa: E402
from ai_engine.tools.calculator import (  # noqa: E402
    calculate_irr,
    calculate_npv,
    calculate_payback_period,
)


def _a(key: str, value: str, **kw) -> Assumption:
    return Assumption(
        key=key,
        value=value,
        source=kw.get("source", "user"),
        confidence=kw.get("confidence", "confirmed"),
        base=value,
        origin=kw.get("origin", "user"),
        provenance_class=kw.get("provenance_class"),
        semantic_type=kw.get("semantic_type"),
    )


def _fnb_state(*assumptions: Assumption) -> StudyState:
    return StudyState(
        study_id="parity_test",
        project_id="proj_parity",
        user_id="user_parity",
        language="en",
        profile=ProjectProfile(archetype="fnb", sector="F&B", language="en"),
        assumptions=list(assumptions),
    )


def test_generic_10000_placeholder_cannot_survive_default():
    for key in (
        "seats_capacity",
        "operating_hours_day",
        "avg_ticket",
        "daily_covers",
        "rent_monthly",
        "labor_monthly",
        "fitout_capex",
    ):
        assert _default_value_for_field({"key": key, "input_type": "number"}, "fnb") is None
    check = validate_assumption_value(key="avg_ticket", value="10000")
    assert check["ok"] is False
    assert check["code"] == "PLACEHOLDER_REJECTED"


def test_operating_hours_cannot_exceed_24():
    bad = validate_assumption_value(key="operating_hours_day", value="10000")
    assert bad["ok"] is False
    bad2 = validate_assumption_value(key="operating_hours_day", value="25")
    assert bad2["ok"] is False
    assert bad2["code"] == "HOURS_OUT_OF_RANGE"
    ok = validate_assumption_value(key="operating_hours_day", value="12")
    assert ok["ok"] is True


def test_invalid_percentage_rejected():
    bad = validate_assumption_value(key="food_cost_pct", value="150")
    assert bad["ok"] is False
    assert bad["code"] in {"PERCENT_OUT_OF_RANGE", "PLACEHOLDER_REJECTED"}


def test_invalid_seat_count_rejected():
    bad = validate_assumption_value(key="seats_capacity", value="10000")
    assert bad["ok"] is False
    bad2 = validate_assumption_value(key="seats_capacity", value="900")
    assert bad2["ok"] is False
    assert bad2["code"] == "SEATS_IMPLAUSIBLE"


def test_invalid_daily_orders_rejected():
    bad = validate_assumption_value(key="daily_covers", value="10000")
    assert bad["ok"] is False
    assert bad["code"] in {"PLACEHOLDER_REJECTED", "ORDERS_IMPLAUSIBLE"}


def test_invalid_average_ticket_rejected():
    bad = validate_assumption_value(key="avg_ticket", value="10000")
    assert bad["ok"] is False
    bad2 = validate_assumption_value(key="avg_ticket", value="600")
    assert bad2["ok"] is False
    assert bad2["code"] == "TICKET_IMPLAUSIBLE"


def test_unknown_safe_behavior():
    check = validate_assumption_value(key="rent_monthly", value="UNKNOWN")
    assert check["ok"] is False
    assert check["code"] == "UNKNOWN"
    assert check["value"] is None
    fnb = extract_fnb_financials(
        vals={},
        assumptions=[_a("avg_ticket", "UNKNOWN"), _a("daily_covers", "UNKNOWN")],
    )
    assert fnb is not None
    assert fnb["annual_revenues"] is None
    assert "fnb_revenue_blocked_missing_or_unknown_ticket_or_covers" in fnb["extract_notes"]


def test_estimate_provenance_mapping():
    assert map_origin_to_provenance("user") == "USER_PROVIDED"
    assert map_origin_to_provenance("document") == "EVIDENCE_BACKED"
    assert map_origin_to_provenance("ai_estimated") == "SYSTEM_ESTIMATE"
    assert map_origin_to_provenance("knowledge_reference", has_evidence_value=False) == "SYSTEM_ESTIMATE"
    assert map_origin_to_provenance("knowledge_reference", has_evidence_value=True) == "EVIDENCE_BACKED"
    assert map_origin_to_provenance(None) == "UNKNOWN"


def test_revenue_cogs_rent_labor_wiring():
    # Synthetic plausible café inputs — not Claude study numbers as product defaults.
    vals = {
        "avg_ticket": 35.0,
        "daily_covers": 120.0,
        "operating_days_year": 330.0,
        "food_cost_pct": 30.0,
        "rent_monthly": 18000.0,
        "labor_monthly": 22000.0,
        "utilities_monthly": 3000.0,
        "marketing_monthly": 2000.0,
        "equipment_capex": 80000.0,
        "fitout_capex": 150000.0,
        "owner_budget": 450000.0,
    }
    fnb = extract_fnb_financials(vals=vals)
    assert fnb is not None
    y1 = 120.0 * 35.0 * 330.0
    assert fnb["annual_revenues"][0] == y1
    assert abs(fnb["cogs_y1"] - y1 * 0.30) < 1.0
    fixed = (18000 + 22000 + 3000 + 2000) * 12
    assert abs(fnb["annual_costs"][0] - (y1 * 0.30 + fixed)) < 1.0
    assert fnb["capex"] == 230000.0
    assert fnb["working_capital"] > 0
    assert fnb["currency"] == "SAR"


def test_capex_reconciliation_and_working_capital():
    vals = {
        "avg_ticket": 40.0,
        "daily_covers": 100.0,
        "equipment_capex": 90000.0,
        "fitout_capex": 200000.0,
        "other_capex": 25000.0,
        "rent_monthly": 15000.0,
        "labor_monthly": 20000.0,
        "owner_budget": 450000.0,
    }
    fnb = extract_fnb_financials(vals=vals)
    comps = fnb["capex_components"]
    assert abs(sum(comps.values()) - fnb["capex"]) < 0.01
    assert fnb["total_initial_funding"] == fnb["capex"] + fnb["working_capital"]
    assert fnb["working_capital"] > 0


def test_budget_surplus_and_shortfall():
    base = {
        "avg_ticket": 40.0,
        "daily_covers": 80.0,
        "equipment_capex": 50000.0,
        "fitout_capex": 100000.0,
        "rent_monthly": 10000.0,
        "labor_monthly": 15000.0,
    }
    surplus = extract_fnb_financials(vals={**base, "owner_budget": 1_000_000.0})
    assert surplus["budget_status"] == "SURPLUS"
    assert surplus["budget_gap"] < 0
    shortfall = extract_fnb_financials(vals={**base, "owner_budget": 100000.0})
    assert shortfall["budget_status"] == "SHORTFALL"
    assert shortfall["budget_gap"] > 0


def test_fnb_deterministic_extract_does_not_use_services_path():
    state = _fnb_state(
        _a("avg_ticket", "38"),
        _a("daily_covers", "90"),
        _a("rent_monthly", "16000"),
        _a("labor_monthly", "21000"),
        _a("equipment_capex", "70000"),
        _a("fitout_capex", "180000"),
        _a("owner_budget", "450000"),
        _a("food_cost_pct", "32"),
    )
    extracted = _deterministic_extract(state)
    assert extracted is not None
    assert "fnb_revenue_daily_covers_x_ticket_x_days" in extracted["extract_notes"]
    assert extracted["annual_revenues"][0] == 90 * 38 * 330
    assert extracted["currency"] == "SAR"


def test_placeholder_gate_and_budget_gate():
    fr = {
        "budget_status": "SHORTFALL",
        "budget_gap": 50000,
        "revenue_projections": {"year_1": 0},
        "currency": "SAR",
    }
    assumptions = [
        _a("avg_ticket", "10000"),
        _a("daily_covers", "10000"),
        _a("operating_hours_day", "10000"),
        _a("owner_budget", "450000"),
        _a("fitout_capex", "10000"),
    ]
    gates = evaluate_financial_trust_gates(
        financial_results=fr,
        assumptions=assumptions,
        archetype="fnb",
        language="en",
    )
    assert "PLACEHOLDER_ASSUMPTION_DETECTED" in gates["codes"]
    assert "BUDGET_SHORTFALL" in gates["codes"]
    assert "HOURS_OUT_OF_RANGE" in gates["codes"]
    assert gates["status"] == "FAIL"


def test_npv_irr_payback_validity():
    cfs = [-300000, 80000, 120000, 150000]
    npv = calculate_npv(cfs, 0.12)
    assert isinstance(npv, (int, float))
    irr = calculate_irr(cfs)
    if irr is not None:
        assert -1 < irr < 5
    never = calculate_payback_period(100000, [-10, -10, -10])
    assert never is None
    ok_pb = calculate_payback_period(100000, [60000, 60000, 60000])
    assert ok_pb is not None
    assert ok_pb > 0


def test_currency_and_period_consistency_fnb():
    vals = {
        "avg_ticket": 32.0,
        "daily_covers": 110.0,
        "operating_days_year": 330.0,
        "food_cost_pct": 28.0,
        "rent_monthly": 14000.0,
        "labor_monthly": 19000.0,
        "equipment_capex": 60000.0,
        "fitout_capex": 140000.0,
        "owner_budget": 450000.0,
        "discount_rate": 0.12,
    }
    fnb = extract_fnb_financials(vals=vals)
    assert fnb["currency"] == "SAR"
    assert fnb["discount_rate"] == 0.12
    assert len(fnb["annual_revenues"]) == 3
    assert len(fnb["annual_costs"]) == 3


def test_competitor_evidence_absence_safe_behavior():
    from ai_engine.research.market.competitor import extract_competitors_from_evidence

    out = extract_competitors_from_evidence(evidence_items=[])
    assert isinstance(out, list)
    assert len(out) == 0


def test_contradiction_detection_module_available():
    from ai_engine.hardening.evidence_gates import evaluate_numeric_evidence_assumption_consistency

    assert callable(evaluate_numeric_evidence_assumption_consistency)


def test_unsupported_strong_go_blocked():
    from ai_engine.agents.decision import run_decision

    state = _fnb_state(
        _a("avg_ticket", "UNKNOWN"),
        _a("daily_covers", "UNKNOWN"),
        _a("owner_budget", "450000"),
    )
    state.claims = []
    state.financial_results = {
        "npv": None,
        "irr": None,
        "payback_years": None,
        "revenue_projections": {"year_1": 0},
        "budget_status": "UNKNOWN_BUDGET",
        "currency": "SAR",
    }
    out = run_decision(state)
    verdict = getattr(out, "verdict", None)
    assert verdict in {"INSUFFICIENT_EVIDENCE", "NO_GO", "DEFER", "GO_WITH_CONDITIONS"}
    assert verdict != "GO"


def test_fnb_schema_has_parity_keys():
    from ai_engine.archetypes.schemas import FNB_SCHEMA

    keys = {f["key"] for f in FNB_SCHEMA}
    for required in (
        "avg_ticket",
        "daily_covers",
        "rent_monthly",
        "labor_monthly",
        "owner_budget",
        "working_capital",
        "equipment_capex",
        "fitout_capex",
    ):
        assert required in keys


def test_sector_pack_source_diversity_categories():
    from ai_engine.hardening.sector_packs import get_sector_pack

    pack = get_sector_pack("fnb")
    assert pack is not None
    cats = pack.get("source_categories") or []
    for c in (
        "official_saudi",
        "market_industry_research",
        "real_estate_location",
        "competitor_primary",
        "staffing_salary",
    ):
        assert c in cats


def test_phase8c2_policy_version_unchanged_smoke():
    from ai_engine.research.quality import RESEARCH_QUALITY_POLICY_VERSION

    assert RESEARCH_QUALITY_POLICY_VERSION == "8c2-v1"


def test_run_financial_analysis_fnb_wired():
    state = _fnb_state(
        _a("avg_ticket", "36"),
        _a("daily_covers", "100"),
        _a("rent_monthly", "17000"),
        _a("labor_monthly", "20000"),
        _a("food_cost_pct", "30"),
        _a("equipment_capex", "75000"),
        _a("fitout_capex", "160000"),
        _a("owner_budget", "450000"),
    )
    # Deterministic extract must wire F&B without LLM.
    extracted = _deterministic_extract(state)
    assert extracted is not None
    assert extracted["annual_revenues"][0] == 100 * 36 * 330
    assert extracted["currency"] == "SAR"
    assert extracted.get("working_capital") is not None
    assert extracted.get("capex_components")

    mock_llm = type("L", (), {"invoke": staticmethod(lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no llm")))})()
    with patch("ai_engine.agents.financial_analyst.get_llm", return_value=mock_llm):
        run_financial_analysis(state)
    fr = state.financial_results or {}
    rev = fr.get("revenue_projections") or {}
    y1 = rev.get("year_1") or rev.get("year1")
    assert y1 and float(y1) > 0
    assert fr.get("currency") == "SAR"
    assert fr.get("working_capital") is not None
    assert fr.get("capex_components")


def test_owner_budget_cannot_become_capex_when_fnb_incomplete():
    state = _fnb_state(
        _a("owner_budget", "450000"),
        _a("avg_ticket", "UNKNOWN"),
        _a("daily_covers", "UNKNOWN"),
        _a("fitout_capex", "UNKNOWN"),
    )
    mock_llm = type(
        "L",
        (),
        {
            "invoke": staticmethod(
                lambda *a, **k: type("R", (), {"content": '{"capex": 450000, "revenue_projections": {"year_1": 0}}'})()
            )
        },
    )()
    with patch("ai_engine.agents.financial_analyst.get_llm", return_value=mock_llm):
        run_financial_analysis(state)
    fr = state.financial_results or {}
    assert float(fr.get("capex") or 0) == 0.0
    assert fr.get("budget_status") == "SURPLUS"
    assert fr.get("currency") == "SAR"
    assert any(str(n).startswith("fnb_") for n in (fr.get("extract_notes") or []))
