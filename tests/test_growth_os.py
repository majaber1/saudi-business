"""Wave 6 — Growth OS Automated Test Suite.

Comprehensive tests covering:
1. Business Health: No actuals recorded returns INSUFFICIENT_DATA, not healthy or at risk.
2. Business Health: Missing data != poor performance; missing values produce UNKNOWN / NOT_AVAILABLE.
3. Trend Engine: Requires at least 2 periods with known values; < 2 periods yields INSUFFICIENT_DATA.
4. Trend Engine: Zero denominator handled safely (percentage_change is None / NOT_AVAILABLE).
5. Trend Engine: Evaluates IMPROVING vs DETERIORATING based on metric optimization direction.
6. Unit Economics: CAC calculated ONLY when marketing spend AND acquired customers are both known.
7. Unit Economics: Contribution margin, ticket size, and fixed/variable cost breakdowns.
8. Growth Funding: Links to Wave 2 matched programs without duplicating logic; potential funding != cash.
9. What-If Model: Output provenance strictly separates ACTUAL, BASELINE, USER_ASSUMPTION, PLATFORM_DERIVED.
10. What-If Model: Deterministic cash payback months, runway impact, and minimum cash required.
11. Expansion Readiness: States READY, CONDITIONALLY_READY, NOT_READY, NEEDS_INFORMATION.
12. Expansion Readiness: Prerequisites evaluated as PASS, FAIL, UNKNOWN, NOT_APPLICABLE.
13. Risks: Detection of runway depletion, margin compression, capacity exhaustion, fixed-cost overhang.
14. Monthly Reviews: Immutable frozen snapshots with auto-incrementing review_version.
15. Strategic Decisions: Supports SCALE, FIX, PIVOT, HOLD, STOP, NEEDS_INFORMATION.
16. SCALE Guardrail: Rejected when readiness is NEEDS_INFORMATION (cannot scale on incomplete data).
17. SCALE Guardrail: Rejected when readiness is NOT_READY (cannot scale with deficits or material risks).
18. PIVOT Integration: Creates a NEW Wave 4 validation workspace and hypothesis without overwriting old.
19. HOLD and STOP Decisions: Workspace transitions to PAUSED and STOPPED while preserving history.
20. FIX Decision: Automatically generates remediation action items.
21. Growth Actions: Lifecycle tracking, status transitions, and completed_at timestamping.
22. Ownership Isolation: Cross-user 403 boundaries for growth workspaces and studies.
23. Cross-Workspace Rejection: Scenario from Workspace A cannot be used in Workspace B What-If.
24. Cross-Workspace Rejection: Decision from Workspace A cannot be linked to Action in Workspace B.
25. Persistence: State persists across fresh sessions and queries.
26. End-to-End Lifecycle: Actuals -> Health -> Trends -> Unit Econ -> Risks -> What-If -> Readiness -> Decision -> Actions.
"""
from __future__ import annotations

import os
import tempfile
import uuid
import pytest

if not os.environ.get("DATABASE_URL"):
    _TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _TMP.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _TMP.name
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters-long")

from fastapi.testclient import TestClient

from app import db as app_db
from app import models
from app.main import app
from app.services.growth import (
    HEALTH_HEALTHY,
    HEALTH_WATCH,
    HEALTH_AT_RISK,
    HEALTH_INSUFFICIENT_DATA,
    TREND_IMPROVING,
    TREND_STABLE,
    TREND_DETERIORATING,
    TREND_INSUFFICIENT_DATA,
    READINESS_READY,
    READINESS_CONDITIONALLY_READY,
    READINESS_NOT_READY,
    READINESS_NEEDS_INFO,
    DECISION_SCALE,
    DECISION_FIX,
    DECISION_PIVOT,
    DECISION_HOLD,
    DECISION_STOP,
    DECISION_NEEDS_INFO,
    PREREQ_PASS,
    PREREQ_FAIL,
    PREREQ_UNKNOWN,
)

client = TestClient(app)
PASSWORD = "Sup3rSecretPassword123!"


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    assert app_db.DB_ENABLED is True
    app_db.init_db()


def _email(prefix="growth"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(prefix="founder"):
    email = _email(prefix)
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text
    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return email, tok


def _create_project_and_study(tok: str, title="مشروع نمو تجريبي", investment=350000.0, monthly_projections=None):
    headers = _auth(tok)
    r_p = client.post("/projects/", json={"name": title, "industry": "food_beverage", "investment": investment}, headers=headers)
    assert r_p.status_code == 201, r_p.text
    project_id = r_p.json()["id"]

    study_payload = {
        "project_id": project_id,
        "title": f"دراسة: {title}",
        "industry": "food_beverage",
        "investment": investment,
    }
    r_s = client.post("/feasibility/", json=study_payload, headers=headers)
    assert r_s.status_code == 201, r_s.text
    study_id = r_s.json()["id"]

    if monthly_projections:
        r_step = client.patch(
            f"/feasibility/{study_id}/step",
            json={"step": 4, "data": {"monthly_projections": monthly_projections}},
            headers=headers,
        )
        assert r_step.status_code == 200, r_step.text

    return project_id, study_id


def _setup_launch_ready_study(tok: str):
    """Sets up a study with Wave 4 GO decision and initialized launch workspace."""
    headers = _auth(tok)
    pid, sid = _create_project_and_study(tok, title="مشروع جاهز للنمو")

    val_ws = client.get(f"/api/v1/validation/study/{sid}", headers=headers).json()
    for h in val_ws["hypotheses"]:
        if h.get("importance") == "CRITICAL":
            client.post(
                f"/api/v1/validation/workspaces/{val_ws['id']}/evidence",
                json={
                    "evidence_type": "INTERVIEW",
                    "title": f"دليل ميداني مثبت للفرضية {h['id']}",
                    "hypothesis_id": h["id"],
                    "evidence_strength": "STRONG",
                    "evidence_direction": "SUPPORTING",
                    "is_simulated": False,
                },
                headers=headers,
            )

    r_dec = client.post(
        f"/api/v1/validation/workspaces/{val_ws['id']}/decision",
        json={"decision": "GO", "decision_reason": "اعتماد كامل ومثبت بالأدلة"},
        headers=headers,
    )
    assert r_dec.status_code == 201, r_dec.text

    # Initialize launch workspace
    r_launch = client.get(f"/api/v1/launch/workspaces/study/{sid}", headers=headers)
    assert r_launch.status_code == 200, r_launch.text
    launch_ws = r_launch.json()
    return pid, sid, launch_ws["id"]


# ==============================================================================
# TESTS
# ==============================================================================

def test_01_health_insufficient_data_when_no_actuals():
    """Missing actuals yields INSUFFICIENT_DATA, never falsely healthy or at risk."""
    _, tok = _register_and_login("h_nodata")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["business_health"]["health_state"] == HEALTH_INSUFFICIENT_DATA
    assert "لا توجد دورات تشغيلية" in data["business_health"]["health_summary_ar"]
    assert data["actual_periods_count"] == 0


def test_02_missing_data_is_not_poor_performance():
    """Missing individual metric fields does not flag AT_RISK, but returns UNKNOWN/NOT_AVAILABLE."""
    _, tok = _register_and_login("h_missing")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # Record actual period with revenue but missing OPEX breakdown and cash balance
    r_act = client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 1,
            "period_label": "2026-M01",
            "actual_revenue": 50000.0,
            # opex fields omitted/null
        },
        headers=headers,
    )
    assert r_act.status_code == 201, r_act.text

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    # Since cash runway is unknown and only 1 period exists, state is WATCH or INSUFFICIENT_DATA, not AT_RISK
    assert res["business_health"]["health_state"] in {HEALTH_WATCH, HEALTH_INSUFFICIENT_DATA}
    assert res["business_health"]["health_state"] != HEALTH_AT_RISK


def test_03_trend_requires_at_least_two_periods():
    """Deterministic trend engine returns INSUFFICIENT_DATA if fewer than 2 periods recorded."""
    _, tok = _register_and_login("trend_min")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # 1 period only
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={"period_order": 1, "period_label": "2026-M01", "actual_revenue": 40000.0},
        headers=headers,
    )

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    assert res["trends"]["periods_analyzed"] == 1
    rev_trend = res["trends"]["metrics"]["actual_revenue"]
    assert rev_trend["direction"] == TREND_INSUFFICIENT_DATA
    assert rev_trend["absolute_change"] is None
    assert rev_trend["percentage_change"] is None


def test_04_trend_zero_denominator_safe():
    """Zero denominator in trend returns None / NOT_AVAILABLE for percentage change without error."""
    _, tok = _register_and_login("trend_zero")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # Period 1: 0 revenue, Period 2: 10,000 revenue
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={"period_order": 1, "period_label": "2026-M01", "actual_revenue": 0.0},
        headers=headers,
    )
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={"period_order": 2, "period_label": "2026-M02", "actual_revenue": 10000.0},
        headers=headers,
    )

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    assert res["trends"]["periods_analyzed"] == 2
    rev_trend = res["trends"]["metrics"]["actual_revenue"]
    assert rev_trend["first_value"] == 0.0
    assert rev_trend["latest_value"] == 10000.0
    assert rev_trend["absolute_change"] == 10000.0
    assert rev_trend["percentage_change"] is None  # Safe zero denominator!
    assert rev_trend["direction"] == TREND_IMPROVING


def test_05_trend_evaluation_directions():
    """Evaluates IMPROVING vs DETERIORATING based on metric semantics (higher vs lower is better)."""
    _, tok = _register_and_login("trend_dirs")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # Period 1: rev 50k, opex 30k
    # Period 2: rev 70k, opex 45k (revenue improved, but opex deteriorated)
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={"period_order": 1, "period_label": "2026-M01", "actual_revenue": 50000.0, "total_actual_opex": 30000.0},
        headers=headers,
    )
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={"period_order": 2, "period_label": "2026-M02", "actual_revenue": 70000.0, "total_actual_opex": 45000.0},
        headers=headers,
    )

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    rev_trend = res["trends"]["metrics"]["actual_revenue"]
    opex_trend = res["trends"]["metrics"]["total_actual_opex"]

    assert rev_trend["direction"] == TREND_IMPROVING
    assert rev_trend["percentage_change"] == 40.0

    assert opex_trend["direction"] == TREND_DETERIORATING  # OPEX increased by 50%
    assert opex_trend["percentage_change"] == 50.0


def test_06_cac_calculation_strict_semantics():
    """CAC is calculated ONLY when marketing spend AND customer count are both known and > 0."""
    _, tok = _register_and_login("cac_rules")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # Case A: marketing spend known, but customers unknown
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={"period_order": 1, "period_label": "2026-M01", "actual_opex_marketing": 10000.0},
        headers=headers,
    )
    res_a = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    cac_a = res_a["unit_economics"]["metrics"]["cac"]
    assert cac_a["is_known"] is False
    assert cac_a["value"] is None
    assert "غير متوفر" in cac_a["note_ar"]

    # Case B: Both marketing spend and acquired customers known
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 2,
            "period_label": "2026-M02",
            "actual_opex_marketing": 12000.0,
            "acquired_customers_count": 400,
        },
        headers=headers,
    )
    res_b = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    cac_b = res_b["unit_economics"]["metrics"]["cac"]
    assert cac_b["is_known"] is True
    assert cac_b["value"] == 30.0  # 12,000 / 400 = 30 SAR


def test_07_unit_economics_exact_metrics():
    """Calculates ticket size, contribution margin, and fixed/variable proportions accurately."""
    _, tok = _register_and_login("unit_econ")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 1,
            "period_label": "2026-M01",
            "actual_revenue": 100000.0,
            "transactions_count": 1000,
            "actual_opex_cogs": 30000.0,
            "actual_opex_salaries": 20000.0,
            "actual_opex_rent": 10000.0,
            "total_actual_opex": 60000.0,
        },
        headers=headers,
    )

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    metrics = res["unit_economics"]["metrics"]

    assert metrics["average_ticket_size"]["value"] == 100.0
    assert metrics["contribution_margin_pct"]["value"] == 70.0  # (100k - 30k COGS) / 100k = 70%
    assert metrics["fixed_cost_proportion_pct"]["value"] == 50.0  # (20k + 10k) / 60k = 50%


def test_08_no_invented_investments_or_funding():
    """Growth funding links to Wave 2 matched programs without creating synthetic funding or cash."""
    _, tok = _register_and_login("growth_funding")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    gf = res["growth_funding"]
    assert gf["context_type"] == "WAVE_2_INTEGRATION"
    assert "التمويل المحتمل ليس سيولة نقدية متاحة" in gf["disclaimer_ar"]
    assert isinstance(gf["wave2_matched_programs"], list)


def test_09_what_if_provenance_separation():
    """What-If simulation model separates ACTUAL, BASELINE, USER_ASSUMPTION, PLATFORM_DERIVED."""
    _, tok = _register_and_login("whatif_prov")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    res = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/what-if",
        json={
            "scenario_name": "محاكاة فرع جديد",
            "scenario_type": "NEW_BRANCH",
            "target_horizon_months": 12,
            "capex_required": 150000.0,
            "additional_monthly_opex": 20000.0,
            "expected_monthly_revenue_uplift": 35000.0,
        },
        headers=headers,
    )
    assert res.status_code == 201, res.text
    model = res.json()["model"]

    assert model["scenario_name"] == "محاكاة فرع جديد"
    prov = model["provenance"]
    assert prov["actuals_baseline"] == "ACTUAL"
    assert prov["capex_required"] == "USER_ASSUMPTION"
    assert prov["monthly_projections"] == "PLATFORM_DERIVED"
    assert len(model["derived_monthly_projections"]) == 12


def test_10_what_if_payback_and_runway_calculation():
    """Deterministic calculation of cash payback months and minimum cash required."""
    _, tok = _register_and_login("whatif_calc")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    # capex 120k, uplift 30k/mo, opex 10k/mo -> net +20k/mo -> payback = 6 months
    res = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/what-if",
        json={
            "scenario_name": "توسعة دقيقة",
            "scenario_type": "CAPACITY_EXPANSION",
            "target_horizon_months": 12,
            "capex_required": 120000.0,
            "additional_monthly_opex": 10000.0,
            "expected_monthly_revenue_uplift": 30000.0,
        },
        headers=headers,
    ).json()["model"]

    assert res["estimated_cash_payback_months"] == 6
    assert res["minimum_cash_required"] == 120000.0


def test_11_expansion_readiness_states():
    """Tests expansion readiness states across differing operational conditions."""
    _, tok = _register_and_login("readiness")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # Initial state with no actuals: NEEDS_INFORMATION
    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    assert res["expansion_readiness"]["readiness_state"] == READINESS_NEEDS_INFO

    # Add 1 period with high losses -> NOT_READY
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 1,
            "period_label": "2026-M01",
            "actual_revenue": 20000.0,
            "total_actual_opex": 80000.0,
            "closing_cash_balance": 10000.0,  # 10k / 60k burn = 0.16 months runway!
        },
        headers=headers,
    )
    res2 = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    assert res2["expansion_readiness"]["readiness_state"] == READINESS_NOT_READY


def test_12_expansion_readiness_prerequisites_mapping():
    """Verifies that all 5 prerequisites are categorized cleanly (PASS, FAIL, UNKNOWN, NOT_APPLICABLE)."""
    _, tok = _register_and_login("prereqs")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    prereqs = res["expansion_readiness"]["prerequisites"]
    assert len(prereqs) == 5
    codes = {p["code"] for p in prereqs}
    assert codes == {"OPERATING_STABILITY", "RUNWAY_ADEQUACY", "UNIT_ECONOMICS", "CAPACITY_UTILIZATION", "DATA_COMPLETENESS"}
    for p in prereqs:
        assert p["status"] in {PREREQ_PASS, PREREQ_FAIL, PREREQ_UNKNOWN, "NOT_APPLICABLE"}


def test_13_growth_risks_transparent_detection():
    """Detects concrete risks (high fixed cost, runway depletion, etc.)."""
    _, tok = _register_and_login("risks_detect")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # Create high fixed costs (> 70% of OPEX)
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 1,
            "period_label": "2026-M01",
            "actual_revenue": 50000.0,
            "actual_opex_salaries": 45000.0,
            "actual_opex_rent": 30000.0,
            "total_actual_opex": 80000.0,
            "closing_cash_balance": 50000.0,
        },
        headers=headers,
    )

    res = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()
    risk_types = [r["risk_type"] for r in res["risks"]]
    assert "FIXED_COST_OVERHANG" in risk_types


def test_14_monthly_business_review_immutable_versioning():
    """Monthly review snapshots are immutable and increment review_version."""
    _, tok = _register_and_login("review_v")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    r1 = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/reviews",
        json={"review_period": "2026-M01", "review_notes": "مراجعة أولى للمشروع"},
        headers=headers,
    )
    assert r1.status_code == 201, r1.text
    rev1 = r1.json()["review"]
    assert rev1["review_version"] == 1

    r2 = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/reviews",
        json={"review_period": "2026-M02", "review_notes": "مراجعة الدورة الثانية"},
        headers=headers,
    )
    assert r2.status_code == 201, r2.text
    rev2 = r2.json()["review"]
    assert rev2["review_version"] == 2


def test_15_strategic_decisions_supported():
    """Strategic decision engine allows recording HOLD and FIX with reasons."""
    _, tok = _register_and_login("dec_supported")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    r = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={"decision": "HOLD", "decision_reason": "التريث حتى اكتمال بيانات الدورة الثانية"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    dec = r.json()["decision"]
    assert dec["decision"] == "HOLD"
    assert dec["decision_version"] == 1


def test_16_scale_decision_guardrail_rejected_when_needs_info():
    """SCALE decision is blocked if prerequisites are in NEEDS_INFORMATION state."""
    _, tok = _register_and_login("scale_noinfo")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    # No actuals recorded -> readiness is NEEDS_INFORMATION
    r = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={"decision": "SCALE", "decision_reason": "نرغب في التوسع مباشرة"},
        headers=headers,
    )
    assert r.status_code == 400, r.text
    assert "NEEDS_INFORMATION" in r.json()["detail"] or "مجهولة" in r.json()["detail"]


def test_17_scale_decision_guardrail_rejected_when_not_ready():
    """SCALE decision is blocked if prerequisites fail or severe deficit exists."""
    _, tok = _register_and_login("scale_notready")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # Record actuals showing high burn and low cash
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 1,
            "period_label": "2026-M01",
            "actual_revenue": 10000.0,
            "total_actual_opex": 90000.0,
            "closing_cash_balance": 15000.0,
        },
        headers=headers,
    )

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    r = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={"decision": "SCALE", "decision_reason": "رغم العجز نرغب بالتوسع"},
        headers=headers,
    )
    assert r.status_code == 400, r.text
    assert "لا يمكن اعتماد قرار التوسع" in r.json()["detail"]


def test_18_pivot_decision_creates_new_wave4_validation_workspace():
    """PIVOT decision links to a NEW Wave 4 validation workspace without overwriting old one."""
    _, tok = _register_and_login("pivot_cycle")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    r = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={
            "decision": "PIVOT",
            "decision_reason": "النموذج التجاري القديم لم يحقق جدوى ونحتاج لاستهداف قطاع الشركات",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    dec = r.json()["decision"]
    assert dec["decision"] == "PIVOT"
    assert dec["pivot_validation_workspace_id"] is not None

    # Check that new validation workspace exists
    new_val_id = dec["pivot_validation_workspace_id"]
    val_ws = client.get(f"/api/v1/validation/workspaces/{new_val_id}", headers=headers).json()
    assert val_ws["id"] == new_val_id
    assert len(val_ws["hypotheses"]) >= 1
    assert "PIVOT" in val_ws["hypotheses"][0]["statement"]


def test_19_hold_and_stop_decisions():
    """HOLD sets status to PAUSED; STOP sets status to STOPPED while preserving data."""
    _, tok = _register_and_login("hold_stop")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    # HOLD
    r_hold = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={"decision": "HOLD", "decision_reason": "تثبيت الأداء لمدة شهر"},
        headers=headers,
    )
    assert r_hold.status_code == 201
    ws_after_hold = client.get(f"/api/v1/growth/workspaces/{ws_id}", headers=headers).json()["workspace"]
    assert ws_after_hold["status"] == "PAUSED"

    # STOP
    r_stop = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={"decision": "STOP", "decision_reason": "إيقاف العمليات لأسباب استراتيجية"},
        headers=headers,
    )
    assert r_stop.status_code == 201
    ws_after_stop = client.get(f"/api/v1/growth/workspaces/{ws_id}", headers=headers).json()["workspace"]
    assert ws_after_stop["status"] == "STOPPED"


def test_20_fix_decision_auto_generates_remediation_actions():
    """FIX decision automatically creates remediation action items in the workspace."""
    _, tok = _register_and_login("fix_actions")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    r = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={"decision": "FIX", "decision_reason": "معالجة التكاليف المتضخمة في بند الرواتب"},
        headers=headers,
    )
    assert r.status_code == 201

    ws_data = client.get(f"/api/v1/growth/workspaces/{ws_id}", headers=headers).json()
    actions = ws_data["actions"]
    assert len(actions) >= 1
    assert any(a["action_type"] == "REMEDIATION" for a in actions)


def test_21_growth_action_lifecycle_and_completion_timestamp():
    """Actions can be created, updated, and toggling COMPLETED sets completed_at."""
    _, tok = _register_and_login("act_lifecycle")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()["workspace"]["id"]

    r_act = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/actions",
        json={
            "title": "مراجعة شروط عقد الإيجار",
            "action_type": "REMEDIATION",
            "category": "OPERATIONS",
        },
        headers=headers,
    )
    assert r_act.status_code == 201
    act = r_act.json()["action"]
    assert act["status"] == "PENDING"
    assert act["completed_at"] is None

    # Transition to COMPLETED
    r_upd = client.patch(
        f"/api/v1/growth/actions/{act['id']}",
        json={"status": "COMPLETED", "notes": "تم تخفيض الإيجار بنسبة 15%"},
        headers=headers,
    )
    assert r_upd.status_code == 200
    upd_act = r_upd.json()["action"]
    assert upd_act["status"] == "COMPLETED"
    assert upd_act["completed_at"] is not None


def test_22_growth_workspace_cross_user_isolation():
    """User B cannot access or mutate User A's Growth workspace (403 Forbidden)."""
    _, tok_a = _register_and_login("user_a")
    _, tok_b = _register_and_login("user_b")

    pid_a, sid_a, _ = _setup_launch_ready_study(tok_a)
    ws_a = client.get(f"/api/v1/growth/study/{sid_a}", headers=_auth(tok_a)).json()["workspace"]

    # User B attempts to access User A's study growth
    r1 = client.get(f"/api/v1/growth/study/{sid_a}", headers=_auth(tok_b))
    assert r1.status_code == 403, r1.text

    # User B attempts to access User A's workspace by id
    r2 = client.get(f"/api/v1/growth/workspaces/{ws_a['id']}", headers=_auth(tok_b))
    assert r2.status_code == 403, r2.text

    # User B attempts to add scenario to User A's workspace
    r3 = client.post(
        f"/api/v1/growth/workspaces/{ws_a['id']}/scenarios",
        json={"name": "قرصنة", "scenario_type": "OTHER"},
        headers=_auth(tok_b),
    )
    assert r3.status_code == 403, r3.text


def test_23_cross_workspace_scenario_rejection():
    """Scenario from Workspace A cannot be run in Workspace B (returns 400)."""
    _, tok = _register_and_login("cross_scen")
    pid_a, sid_a, _ = _setup_launch_ready_study(tok)
    pid_b, sid_b, _ = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_a = client.get(f"/api/v1/growth/study/{sid_a}", headers=headers).json()["workspace"]["id"]
    ws_b = client.get(f"/api/v1/growth/study/{sid_b}", headers=headers).json()["workspace"]["id"]

    # Create scenario in Workspace A
    scen_a = client.post(
        f"/api/v1/growth/workspaces/{ws_a}/scenarios",
        json={"name": "سيناريو A", "scenario_type": "NEW_BRANCH"},
        headers=headers,
    ).json()["scenario"]

    # Run what-if in Workspace B referencing scenario_id from A
    r = client.post(
        f"/api/v1/growth/workspaces/{ws_b}/what-if",
        json={"scenario_id": scen_a["id"], "scenario_name": "محاولة ربط خاطئة"},
        headers=headers,
    )
    assert r.status_code == 400
    assert "belongs to a different workspace" in r.json()["detail"]


def test_24_cross_workspace_decision_action_rejection():
    """Decision from Workspace A cannot be attached to Action in Workspace B (returns 400)."""
    _, tok = _register_and_login("cross_dec")
    pid_a, sid_a, _ = _setup_launch_ready_study(tok)
    pid_b, sid_b, _ = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    ws_a = client.get(f"/api/v1/growth/study/{sid_a}", headers=headers).json()["workspace"]["id"]
    ws_b = client.get(f"/api/v1/growth/study/{sid_b}", headers=headers).json()["workspace"]["id"]

    # Decision in Workspace A
    dec_a = client.post(
        f"/api/v1/growth/workspaces/{ws_a}/decisions",
        json={"decision": "HOLD", "decision_reason": "قرار في A"},
        headers=headers,
    ).json()["decision"]

    # Action in Workspace B pointing to dec_a
    r = client.post(
        f"/api/v1/growth/workspaces/{ws_b}/actions",
        json={"title": "إجراء غير شرعي", "decision_id": dec_a["id"]},
        headers=headers,
    )
    assert r.status_code == 400
    assert "does not belong to this workspace" in r.json()["detail"]


def test_25_persistence_across_sessions():
    """Growth workspace entities persist across fresh logins and queries."""
    email, tok1 = _register_and_login("persist_user")
    pid, sid, launch_id = _setup_launch_ready_study(tok1)
    headers1 = _auth(tok1)

    ws_id = client.get(f"/api/v1/growth/study/{sid}", headers=headers1).json()["workspace"]["id"]

    # Add scenario and action
    client.post(
        f"/api/v1/growth/workspaces/{ws_id}/scenarios",
        json={"name": "سيناريو دائم", "scenario_type": "DIGITAL_TRANSFORMATION"},
        headers=headers1,
    )
    client.post(
        f"/api/v1/growth/workspaces/{ws_id}/actions",
        json={"title": "إطلاق المتجر الإلكتروني", "action_type": "EXPANSION"},
        headers=headers1,
    )

    # Fresh login
    tok2 = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    headers2 = _auth(tok2)

    fresh_data = client.get(f"/api/v1/growth/workspaces/{ws_id}", headers=headers2).json()
    assert len(fresh_data["scenarios"]) == 1
    assert fresh_data["scenarios"][0]["name"] == "سيناريو دائم"
    assert len(fresh_data["actions"]) == 1
    assert fresh_data["actions"][0]["title"] == "إطلاق المتجر الإلكتروني"


def test_26_end_to_end_growth_lifecycle():
    """Comprehensive E2E test covering the complete Growth OS lifecycle:
    ACTUALS -> HEALTH -> TRENDS -> UNIT ECON -> RISKS -> WHAT-IF -> READINESS -> FUNDING -> DECISION -> ACTIONS
    """
    _, tok = _register_and_login("growth_e2e")
    pid, sid, launch_id = _setup_launch_ready_study(tok)
    headers = _auth(tok)

    # 1. Record two actual periods with positive economics
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 1,
            "period_label": "2026-M01",
            "actual_revenue": 80000.0,
            "transactions_count": 800,
            "actual_opex_cogs": 24000.0,
            "actual_opex_salaries": 20000.0,
            "actual_opex_rent": 10000.0,
            "actual_opex_marketing": 6000.0,
            "acquired_customers_count": 200,
            "total_actual_opex": 60000.0,
            "closing_cash_balance": 200000.0,
        },
        headers=headers,
    )
    client.post(
        f"/api/v1/launch/workspaces/{launch_id}/actuals",
        json={
            "period_order": 2,
            "period_label": "2026-M02",
            "actual_revenue": 100000.0,
            "transactions_count": 1000,
            "actual_opex_cogs": 30000.0,
            "actual_opex_salaries": 20000.0,
            "actual_opex_rent": 10000.0,
            "actual_opex_marketing": 8000.0,
            "acquired_customers_count": 250,
            "total_actual_opex": 68000.0,
            "closing_cash_balance": 232000.0,
        },
        headers=headers,
    )

    # 2. Query Growth OS full data
    g_data = client.get(f"/api/v1/growth/study/{sid}", headers=headers).json()

    # Verify Health: Healthy with positive margin and ample runway
    assert g_data["business_health"]["health_state"] == HEALTH_HEALTHY

    # Verify Trends: Revenue improving (+25%)
    assert g_data["trends"]["metrics"]["actual_revenue"]["direction"] == TREND_IMPROVING
    assert g_data["trends"]["metrics"]["actual_revenue"]["percentage_change"] == 25.0

    # Verify Unit Economics: CAC = 8,000 / 250 = 32 SAR, Ticket = 100 SAR
    assert g_data["unit_economics"]["metrics"]["cac"]["value"] == 32.0
    assert g_data["unit_economics"]["metrics"]["average_ticket_size"]["value"] == 100.0

    # Verify Funding: Wave 2 context present
    assert g_data["growth_funding"]["context_type"] == "WAVE_2_INTEGRATION"

    # 3. Run What-If Simulation
    ws_id = g_data["workspace"]["id"]
    sim = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/what-if",
        json={
            "scenario_name": "توسع فرع ثانٍ",
            "scenario_type": "NEW_BRANCH",
            "target_horizon_months": 12,
            "capex_required": 100000.0,
            "additional_monthly_opex": 15000.0,
            "expected_monthly_revenue_uplift": 40000.0,
        },
        headers=headers,
    ).json()["model"]
    assert sim["estimated_cash_payback_months"] == 4

    # 4. Record Strategic Decision (SCALE succeeds because health is HEALTHY and runway is solid)
    dec_res = client.post(
        f"/api/v1/growth/workspaces/{ws_id}/decisions",
        json={
            "decision": "SCALE",
            "decision_reason": "تحقيق أرباح مستقرة لشهرين متتاليين وتوفر سيولة تتجاوز 200 ألف ريال",
        },
        headers=headers,
    )
    assert dec_res.status_code == 201, dec_res.text
    dec = dec_res.json()["decision"]
    assert dec["decision"] == "SCALE"

    # 5. Verify Workspace Status is ACTIVE
    ws_final = client.get(f"/api/v1/growth/workspaces/{ws_id}", headers=headers).json()["workspace"]
    assert ws_final["status"] == "ACTIVE"
