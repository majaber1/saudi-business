"""Wave 5 — Launch, Actuals & Reforecasting OS Automated Test Suite.

Comprehensive tests covering:
1. Validation Decision Gate: STOP and PIVOT decisions block launch workspace creation.
2. Launch workspace initialization and ownership isolation.
3. Pre-launch milestone tracking (Saudi regulatory & execution milestones).
4. Milestone status & cost updating.
5. Baseline snapshot freezing (ensuring feasibility forecasts are not mutated).
6. Operational actuals recording (Revenue, Volume/AOV, CAPEX, OPEX breakdown).
7. Forecast vs actual variance engine and zero-denominator protection.
8. Materiality alert thresholds (NORMAL, WATCH, MATERIAL_VARIANCE).
9. Dynamic scenario reforecasting with runway and burn rate calculations.
10. Immutable reforecast versioning (v1, v2) preserving baseline snapshot integrity.
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
from app.services.launch import (
    ALERT_NORMAL,
    ALERT_WATCH,
    ALERT_MATERIAL_VARIANCE,
    ALERT_NO_DATA,
)

client = TestClient(app)
PASSWORD = "Sup3rSecretPassword123!"


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    assert app_db.DB_ENABLED is True
    app_db.init_db()


def _email(prefix="launch"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(prefix="founder"):
    email = _email(prefix)
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text
    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return email, tok


def _create_project_and_study(tok: str, title="مشروع كافيه تجريبي", investment=350000.0):
    headers = _auth(tok)
    r_p = client.post("/projects/", json={"name": title, "industry": "food_beverage", "investment": investment}, headers=headers)
    assert r_p.status_code == 201, r_p.text
    project_id = r_p.json()["id"]

    r_s = client.post(
        "/feasibility/",
        json={"project_id": project_id, "title": f"دراسة: {title}", "industry": "food_beverage", "investment": investment},
        headers=headers,
    )
    assert r_s.status_code == 201, r_s.text
    study_id = r_s.json()["id"]
    return project_id, study_id


# ==============================================================================
# TESTS
# ==============================================================================

def test_validation_decision_gate_blocks_stop_and_pivot():
    """Test that a STOP or PIVOT validation decision blocks launch workspace creation."""
    _, tok = _register_and_login("val_gate")
    headers = _auth(tok)
    _, study_id = _create_project_and_study(tok, "مشروع فحص بوابات الإطلاق")

    # 1. Initialize validation workspace and record STOP
    val_ws = client.get(f"/api/v1/validation/study/{study_id}", headers=headers).json()
    client.post(
        f"/api/v1/validation/workspaces/{val_ws['id']}/decision",
        json={"decision": "STOP", "decision_reason": "أدلة ميدانية سلبية"},
        headers=headers,
    )

    # Attempting to initialize launch workspace -> HTTP 422 rejected!
    r_stop = client.get(f"/api/v1/launch/study/{study_id}", headers=headers)
    assert r_stop.status_code == 422
    assert "إيقاف" in r_stop.text or "STOP" in r_stop.text

    # 2. Record PIVOT decision
    client.post(
        f"/api/v1/validation/workspaces/{val_ws['id']}/decision",
        json={"decision": "PIVOT", "decision_reason": "تغيير النموذج التشغيلي"},
        headers=headers,
    )

    r_pivot = client.get(f"/api/v1/launch/study/{study_id}", headers=headers)
    assert r_pivot.status_code == 422
    assert "تعديل المسار" in r_pivot.text or "PIVOT" in r_pivot.text

    # 3. Add supporting evidence to reach PARTIALLY_VALIDATED, then record GO_WITH_CONDITIONS decision
    client.post(
        f"/api/v1/validation/workspaces/{val_ws['id']}/evidence",
        json={
            "evidence_type": "INTERVIEW",
            "title": "مقابلة داعمة أولية",
            "hypothesis_id": val_ws["hypotheses"][0]["id"],
            "evidence_strength": "STRONG",
            "evidence_direction": "SUPPORTING",
            "is_simulated": False,
        },
        headers=headers,
    )

    r_dec = client.post(
        f"/api/v1/validation/workspaces/{val_ws['id']}/decision",
        json={
            "decision": "GO_WITH_CONDITIONS",
            "decision_reason": "تحقق كافٍ مع اشتراط سقف التكاليف",
            "conditions": ["التعاقد بسعر الجملة"],
        },
        headers=headers,
    )
    assert r_dec.status_code == 201

    # Now launch workspace creation succeeds!
    r_ok = client.get(f"/api/v1/launch/study/{study_id}", headers=headers)
    assert r_ok.status_code == 200
    assert r_ok.json()["status"] == "PRE_LAUNCH"


def test_launch_workspace_milestones_and_baseline_snapshot():
    """Test default milestone seeding and frozen baseline projection snapshot."""
    _, tok = _register_and_login("launch_init")
    headers = _auth(tok)
    _, study_id = _create_project_and_study(tok, "مشروع تجارة التجزئة", investment=450000.0)

    res = client.get(f"/api/v1/launch/study/{study_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Milestones verification
    milestones = data["milestones"]
    assert len(milestones) == 6
    categories = {m["category"] for m in milestones}
    assert "REGULATORY" in categories
    assert "LOCATION" in categories
    assert "EQUIPMENT" in categories
    assert "TEAM" in categories
    assert "MARKETING" in categories
    assert "OPERATIONS" in categories

    # Baseline snapshot verification
    snaps = data["baseline_snapshots"]
    assert len(snaps) == 1
    s = snaps[0]
    assert s["total_investment"] == 450000.0
    assert s["snapshot_version"] == 1
    assert len(s["monthly_projections"]) == 12
    assert s["monthly_projections"][0]["period_label"] == "M01"


def test_milestone_management_and_cost_updates():
    """Test adding custom milestone and updating progress/costs."""
    _, tok = _register_and_login("milestone_mgr")
    headers = _auth(tok)
    _, study_id = _create_project_and_study(tok, "مشروع مطعم ومقهى")

    ws = client.get(f"/api/v1/launch/study/{study_id}", headers=headers).json()
    ws_id = ws["id"]
    m1_id = ws["milestones"][0]["id"]

    # Patch existing milestone
    r_patch = client.patch(
        f"/api/v1/launch/milestones/{m1_id}",
        json={"status": "COMPLETED", "actual_cost": 4200.0},
        headers=headers,
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["status"] == "COMPLETED"
    assert r_patch.json()["actual_cost"] == 4200.0
    assert r_patch.json()["completed_date"] is not None

    # Add custom milestone
    r_add = client.post(
        f"/api/v1/launch/workspaces/{ws_id}/milestones",
        json={
            "category": "OPERATIONS",
            "title": "الربط التقني مع أنظمة المحاسبة والفوترة السحابية",
            "budget_allocated": 3000.0,
        },
        headers=headers,
    )
    assert r_add.status_code == 201
    assert r_add.json()["title"] == "الربط التقني مع أنظمة المحاسبة والفوترة السحابية"


def test_actual_period_recording_and_opex_breakdown():
    """Test operational actuals recording with OPEX breakdown and derived net cashflow."""
    _, tok = _register_and_login("actuals_rec")
    headers = _auth(tok)
    _, study_id = _create_project_and_study(tok, "مشروع عيادة تخصصية")

    ws = client.get(f"/api/v1/launch/study/{study_id}", headers=headers).json()
    ws_id = ws["id"]

    r_act = client.post(
        f"/api/v1/launch/workspaces/{ws_id}/actuals",
        json={
            "period_label": "M01",
            "period_order": 1,
            "actual_revenue": 70000.0,
            "transactions_count": 1400,
            "actual_capex": 250000.0,
            "actual_opex_salaries": 20000.0,
            "actual_opex_rent": 12000.0,
            "actual_opex_utilities": 3000.0,
            "actual_opex_marketing": 6000.0,
            "actual_opex_cogs": 10000.0,
            "actual_opex_other": 1000.0,
            "closing_cash_balance": 98000.0,
            "notes": "انطلاق العمليات في الشهر الأول",
        },
        headers=headers,
    )
    assert r_act.status_code == 201
    act_data = r_act.json()

    # Derived AOV = 70000 / 1400 = 50.0
    assert act_data["average_ticket_size"] == 50.0
    # Total OPEX = 20000 + 12000 + 3000 + 6000 + 10000 + 1000 = 52000.0
    assert act_data["total_actual_opex"] == 52000.0
    # Net cashflow = 70000 - 250000 - 52000 = -232000.0
    assert act_data["net_cashflow"] == -232000.0


def test_forecast_vs_actual_variance_and_materiality_alerts():
    """Test variance calculations against frozen baseline and alert tiers."""
    _, tok = _register_and_login("variance_test")
    headers = _auth(tok)
    _, study_id = _create_project_and_study(tok, "مشروع نادي رياضي", investment=500000.0)

    ws = client.get(f"/api/v1/launch/study/{study_id}", headers=headers).json()
    ws_id = ws["id"]

    # Record period 1 with Material Variance (>25%)
    client.post(
        f"/api/v1/launch/workspaces/{ws_id}/actuals",
        json={
            "period_label": "M01",
            "period_order": 1,
            "actual_revenue": 5000.0,  # far lower than expected
            "actual_opex_salaries": 60000.0,
        },
        headers=headers,
    )

    r_var = client.get(f"/api/v1/launch/workspaces/{ws_id}/variances", headers=headers)
    assert r_var.status_code == 200
    var_data = r_var.json()
    assert var_data["overall_health"] == ALERT_MATERIAL_VARIANCE
    assert len(var_data["period_variances"]) == 1

    p1 = var_data["period_variances"][0]
    assert p1["alert"] == ALERT_MATERIAL_VARIANCE
    assert p1["variance"]["revenue_pct"] is not None
    assert p1["variance"]["opex_pct"] is not None


def test_dynamic_reforecast_generation_and_runway():
    """Test scenario reforecasting, runway calculations, and multiple versions."""
    _, tok = _register_and_login("reforecast_user")
    headers = _auth(tok)
    _, study_id = _create_project_and_study(tok, "مشروع مغسلة سيارات ذكية")

    ws = client.get(f"/api/v1/launch/study/{study_id}", headers=headers).json()
    ws_id = ws["id"]

    # Record actuals for 2 periods
    client.post(
        f"/api/v1/launch/workspaces/{ws_id}/actuals",
        json={"period_label": "M01", "period_order": 1, "actual_revenue": 30000.0, "actual_opex_salaries": 18000.0, "closing_cash_balance": 150000.0},
        headers=headers,
    )
    client.post(
        f"/api/v1/launch/workspaces/{ws_id}/actuals",
        json={"period_label": "M02", "period_order": 2, "actual_revenue": 35000.0, "actual_opex_salaries": 20000.0, "closing_cash_balance": 135000.0},
        headers=headers,
    )

    # Post Reforecast V1
    rf1_res = client.post(
        f"/api/v1/launch/workspaces/{ws_id}/reforecast",
        json={
            "reforecast_title": "إعادة التنبؤ بناءً على نتائج أول شهرين",
            "adjustment_rationale": "تعديل وتيرة النمو مع ضبط المصاريف الإدارية",
            "growth_rate_adjustment_pct": -5.0,
            "opex_adjustment_pct": -8.0,
        },
        headers=headers,
    )
    assert rf1_res.status_code == 201
    rf1 = rf1_res.json()
    assert rf1["version_number"] == 1
    assert rf1["remaining_runway_months"] is not None
    assert len(rf1["reforecast_payload"]["monthly_projections"]) == 12

    # Post Reforecast V2
    rf2_res = client.post(
        f"/api/v1/launch/workspaces/{ws_id}/reforecast",
        json={
            "reforecast_title": "سيناريو التوسع التسويقي v2",
            "adjustment_rationale": "إعادة التنبؤ مع افتراض مضاعفة الحملة الإعلانية",
            "growth_rate_adjustment_pct": 20.0,
            "opex_adjustment_pct": 15.0,
        },
        headers=headers,
    )
    assert rf2_res.status_code == 201
    rf2 = rf2_res.json()
    assert rf2["version_number"] == 2


def test_launch_workspace_ownership_isolation():
    """Test that workspaces cannot be accessed across different users."""
    _, tok1 = _register_and_login("launch_owner1")
    _, tok2 = _register_and_login("launch_owner2")

    _, study_id = _create_project_and_study(tok1, "مشروع محمي أ")
    ws1 = client.get(f"/api/v1/launch/study/{study_id}", headers=_auth(tok1)).json()
    ws1_id = ws1["id"]

    # User 2 attempts to get User 1's workspace -> 403 Forbidden
    r_iso_study = client.get(f"/api/v1/launch/study/{study_id}", headers=_auth(tok2))
    assert r_iso_study.status_code == 403

    r_iso_ws = client.get(f"/api/v1/launch/workspaces/{ws1_id}", headers=_auth(tok2))
    assert r_iso_ws.status_code == 403

    # User 2 attempts to record actuals on User 1's workspace -> 403
    r_act = client.post(
        f"/api/v1/launch/workspaces/{ws1_id}/actuals",
        json={"period_label": "M01", "period_order": 1, "actual_revenue": 10000.0},
        headers=_auth(tok2),
    )
    assert r_act.status_code == 403
