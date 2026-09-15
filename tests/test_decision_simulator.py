"""Phase 10: Decision Simulator — deterministic scenarios with deltas, decision gates, trust."""
import os
import sys
import tempfile
import uuid
from pathlib import Path

if not os.environ.get("DATABASE_URL"):
    handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    handle.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + handle.name

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from app import db as app_db  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def setup_module(module):
    app_db.init_db()


def _headers(prefix: str):
    email = f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"
    password = "Sup3rSecret!"
    assert client.post("/auth/register", json={"email": email, "password": password}).status_code == 201
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _study(headers, archetype="saas_digital"):
    project = client.post(
        "/projects/", headers=headers, json={"name": "Test Project", "industry": archetype, "investment": 500000}
    ).json()
    return client.post(
        "/feasibility/",
        headers=headers,
        json={"project_id": project["id"], "title": "Test Study", "industry": archetype, "investment": 500000},
    ).json()


def _set_assumption(headers, study_id, key, value):
    resp = client.post(
        f"/studies/{study_id}/assumptions/",
        headers=headers,
        json={"key": key, "label_en": key, "label_ar": key, "value_number": value, "origin": "USER"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _setup_baseline(headers, study_id, capex=500000, revenue=300000, opex=150000):
    _set_assumption(headers, study_id, "capex", capex)
    _set_assumption(headers, study_id, "revenue_year1", revenue)
    _set_assumption(headers, study_id, "opex_annual", opex)


# --- /simulate endpoint ---

def test_simulate_returns_full_result_structure():
    headers = _headers("sim_struct")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"scenario_name": "Price +10%", "assumption_overrides": {"revenue_year1": 330000}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert "scenario" in body
    assert "baseline" in body
    assert "delta" in body
    assert "decision_impact" in body
    assert "risk_impact" in body
    assert "trust" in body
    assert "warnings" in body
    assert body["is_hypothetical"] is True


def test_simulate_baseline_never_modified():
    headers = _headers("sim_immutable")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"assumption_overrides": {"revenue_year1": 999999}},
    )

    active = client.get(f"/studies/{study['id']}/assumptions/", headers=headers).json()
    revenue = next(a for a in active if a["key"] == "revenue_year1")
    assert revenue["value_number"] == 300000


def test_simulate_delta_computation():
    headers = _headers("sim_delta")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"assumption_overrides": {"revenue_year1": 330000}},
    ).json()

    delta = resp["delta"]
    assert delta["annual_revenue"]["baseline"] == 300000
    assert delta["annual_revenue"]["scenario"] == 330000
    assert delta["annual_revenue"]["absolute"] == 30000


def test_simulate_decision_impact_deterministic():
    headers = _headers("sim_decision")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"assumption_overrides": {"revenue_year1": 330000}},
    ).json()

    di = resp["decision_impact"]
    assert di["baseline_decision"] in ("GO", "CONDITIONAL_GO", "NO_GO", "INSUFFICIENT_EVIDENCE")
    assert di["scenario_decision"] in ("GO", "CONDITIONAL_GO", "NO_GO", "INSUFFICIENT_EVIDENCE")
    assert isinstance(di["changed"], bool)


def test_simulate_trust_does_not_upgrade_from_overrides():
    headers = _headers("sim_trust")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp_base = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"assumption_overrides": {}},
    ).json()

    resp_better = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"assumption_overrides": {"revenue_year1": 9999999}},
    ).json()

    assert resp_base["trust"]["grade"] == resp_better["trust"]["grade"]
    assert resp_base["trust"]["verified_pct"] == resp_better["trust"]["verified_pct"]
    assert "not by scenario overrides" in resp_better["trust"]["note"].lower()


def test_simulate_persistence():
    headers = _headers("sim_persist")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"scenario_name": "Persist Test", "assumption_overrides": {"revenue_year1": 350000}},
    ).json()

    scenario_id = resp["scenario"]["id"]

    get_resp = client.get(f"/studies/{study['id']}/scenarios/{scenario_id}", headers=headers)
    assert get_resp.status_code == 200
    saved = get_resp.json()
    assert saved["scenario_name"] == "Persist Test"
    assert saved["financial_result_snapshot"]["npv"] == resp["scenario"]["financial_result_snapshot"]["npv"]


def test_simulate_source_values_distinguish_baseline_vs_override():
    headers = _headers("sim_source")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"assumption_overrides": {"revenue_year1": 330000}},
    ).json()

    sv = resp["scenario"]["source_assumption_values"]
    assert sv["revenue_year1"]["origin"] == "SCENARIO_ASSUMPTION"
    assert sv["capex"]["origin"] == "BASELINE"


def test_simulate_custom_type_accepted():
    headers = _headers("sim_custom")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"scenario_type": "CUSTOM", "scenario_name": "My Custom", "assumption_overrides": {"opex_annual": 200000}},
    )
    assert resp.status_code == 200
    assert resp.json()["scenario"]["scenario_type"] == "CUSTOM"


def test_simulate_risk_impact():
    headers = _headers("sim_risk")
    study = _study(headers)
    _setup_baseline(headers, study["id"], capex=500000, revenue=300000, opex=150000)

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"assumption_overrides": {"revenue_year1": 50000}},
    ).json()

    risk = resp["risk_impact"]
    assert isinstance(risk, list)
    categories = [r["category"] for r in risk]
    assert "revenue_override" in categories


# --- /variables/meta endpoint ---

def test_variables_meta_returns_keys():
    headers = _headers("sim_vars")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    resp = client.get(f"/studies/{study['id']}/scenarios/variables/meta", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "variables" in body
    assert "current_values" in body
    keys = [v["key"] for v in body["variables"]]
    assert "capex" in keys
    assert "revenue_year1" in keys


# --- single scenario endpoint ---

def test_get_single_scenario():
    headers = _headers("sim_single")
    study = _study(headers)
    _setup_baseline(headers, study["id"])

    created = client.post(
        f"/studies/{study['id']}/scenarios/",
        headers=headers,
        json={"scenario_type": "BASE"},
    ).json()

    got = client.get(f"/studies/{study['id']}/scenarios/{created['id']}", headers=headers)
    assert got.status_code == 200
    assert got.json()["id"] == created["id"]


def test_get_nonexistent_scenario_404():
    headers = _headers("sim_404")
    study = _study(headers)
    resp = client.get(f"/studies/{study['id']}/scenarios/99999", headers=headers)
    assert resp.status_code == 404


# --- Tabea validation scenarios ---

def test_tabea_scenario_a_price_increase():
    """Scenario A: revenue +10% — NPV should improve."""
    headers = _headers("tabea_a")
    study = _study(headers, archetype="fnb")
    _setup_baseline(headers, study["id"], capex=850000, revenue=720000, opex=480000)

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"scenario_name": "Price +10%", "assumption_overrides": {"revenue_year1": 792000}},
    ).json()

    assert resp["delta"]["npv"]["scenario"] > resp["delta"]["npv"]["baseline"]
    assert resp["is_hypothetical"] is True


def test_tabea_scenario_b_demand_decrease():
    """Scenario B: revenue -20% — NPV should worsen."""
    headers = _headers("tabea_b")
    study = _study(headers, archetype="fnb")
    _setup_baseline(headers, study["id"], capex=850000, revenue=720000, opex=480000)

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"scenario_name": "Demand -20%", "assumption_overrides": {"revenue_year1": 576000}},
    ).json()

    assert resp["delta"]["npv"]["scenario"] < resp["delta"]["npv"]["baseline"]


def test_tabea_scenario_c_cac_and_churn():
    """Scenario C: opex +25% (CAC+churn proxy) — financial stress test."""
    headers = _headers("tabea_c")
    study = _study(headers, archetype="fnb")
    _setup_baseline(headers, study["id"], capex=850000, revenue=720000, opex=480000)

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=headers,
        json={"scenario_name": "CAC +25% + Churn", "assumption_overrides": {"opex_annual": 600000}},
    ).json()

    assert resp["delta"]["operating_result"]["scenario"] < resp["delta"]["operating_result"]["baseline"]
    assert resp["trust"]["grade"] in ("INVESTMENT_GRADE", "MODERATE_TRUST", "NOT_INVESTMENT_GRADE")


def test_simulate_ownership_isolation():
    owner = _headers("sim_iso_own")
    other = _headers("sim_iso_oth")
    study = _study(owner)
    _setup_baseline(owner, study["id"])

    resp = client.post(
        f"/studies/{study['id']}/scenarios/simulate",
        headers=other,
        json={"assumption_overrides": {"revenue_year1": 100000}},
    )
    assert resp.status_code == 403
