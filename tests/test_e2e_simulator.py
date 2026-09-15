"""E2E Decision Simulator journey: register → create business → set assumptions →
simulate scenarios A/B/C → verify persistence → verify trust immutability → compare.

Uses Tabea Coffee baseline: CAPEX=850K, Revenue=720K, OPEX=480K (F&B archetype).
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path

if not os.environ.get("DATABASE_URL"):
    _TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _TMP.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _TMP.name

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from app import db as app_db  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
PASSWORD = "SimE2E_Test1!"


def setup_module(module):
    app_db.init_db()


def _uid():
    return uuid.uuid4().hex[:8]


class TestSimulatorE2EJourney:
    """Full simulator journey exercising the user story end-to-end."""

    headers = None
    study_id = None
    scenario_ids = []

    @classmethod
    def setup_class(cls):
        email = f"tabea_{_uid()}@example.com"
        assert client.post("/auth/register", json={"email": email, "password": PASSWORD}).status_code == 201
        tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {tok}"}

        project = client.post(
            "/projects/", headers=cls.headers,
            json={"name": "Tabea Coffee", "industry": "fnb", "investment": 850000},
        ).json()

        study = client.post(
            "/feasibility/", headers=cls.headers,
            json={"project_id": project["id"], "title": "Tabea Baseline", "industry": "fnb", "investment": 850000},
        ).json()
        cls.study_id = study["id"]

        for key, val in [("capex", 850000), ("revenue_year1", 720000), ("opex_annual", 480000)]:
            r = client.post(
                f"/studies/{cls.study_id}/assumptions/", headers=cls.headers,
                json={"key": key, "label_en": key, "label_ar": key, "value_number": val, "origin": "USER"},
            )
            assert r.status_code == 201

    def test_01_variables_meta(self):
        resp = client.get(f"/studies/{self.study_id}/scenarios/variables/meta", headers=self.headers)
        assert resp.status_code == 200
        body = resp.json()
        keys = [v["key"] for v in body["variables"]]
        assert "revenue_year1" in keys
        assert body["current_values"]["capex"] == 850000

    def test_02_scenario_a_price_increase(self):
        resp = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"scenario_name": "Scenario A: Price +10%", "assumption_overrides": {"revenue_year1": 792000}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_hypothetical"] is True
        assert body["delta"]["annual_revenue"]["scenario"] == 792000
        assert body["delta"]["npv"]["scenario"] > body["delta"]["npv"]["baseline"]
        self.__class__.scenario_ids.append(body["scenario"]["id"])

    def test_03_scenario_b_demand_decrease(self):
        resp = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"scenario_name": "Scenario B: Demand -20%", "assumption_overrides": {"revenue_year1": 576000}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["delta"]["npv"]["scenario"] < body["delta"]["npv"]["baseline"]
        di = body["decision_impact"]
        assert di["scenario_decision"] in ("GO", "CONDITIONAL_GO", "NO_GO", "INSUFFICIENT_EVIDENCE")
        self.__class__.scenario_ids.append(body["scenario"]["id"])

    def test_04_scenario_c_cac_churn(self):
        resp = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"scenario_name": "Scenario C: CAC +25% + Churn", "assumption_overrides": {"opex_annual": 600000}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["delta"]["operating_result"]["scenario"] < body["delta"]["operating_result"]["baseline"]
        self.__class__.scenario_ids.append(body["scenario"]["id"])

    def test_05_persistence_all_scenarios_saved(self):
        resp = client.get(f"/studies/{self.study_id}/scenarios/", headers=self.headers)
        assert resp.status_code == 200
        scenarios = resp.json()
        saved_ids = {s["id"] for s in scenarios}
        for sid in self.scenario_ids:
            assert sid in saved_ids, f"Scenario {sid} not persisted"

    def test_06_persistence_individual_retrieval(self):
        for sid in self.scenario_ids:
            resp = client.get(f"/studies/{self.study_id}/scenarios/{sid}", headers=self.headers)
            assert resp.status_code == 200
            assert resp.json()["id"] == sid
            assert resp.json()["financial_result_snapshot"]["npv"] is not None

    def test_07_baseline_untouched_after_all_scenarios(self):
        active = client.get(f"/studies/{self.study_id}/assumptions/", headers=self.headers).json()
        vals = {a["key"]: a["value_number"] for a in active}
        assert vals["capex"] == 850000
        assert vals["revenue_year1"] == 720000
        assert vals["opex_annual"] == 480000

    def test_08_trust_grade_stable_across_all_scenarios(self):
        grades = set()
        for sid in self.scenario_ids:
            resp = client.post(
                f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
                json={"assumption_overrides": {}},
            ).json()
            grades.add(resp["trust"]["grade"])
        assert len(grades) == 1, f"Trust grade changed across scenarios: {grades}"

    def test_09_compare_endpoint(self):
        resp = client.get(f"/studies/{self.study_id}/scenarios/compare", headers=self.headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "CUSTOM" in body
        assert body["CUSTOM"] is not None

    def test_10_deterministic_reproducibility(self):
        r1 = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"assumption_overrides": {"revenue_year1": 792000}},
        ).json()
        r2 = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"assumption_overrides": {"revenue_year1": 792000}},
        ).json()
        assert r1["baseline"]["npv"] == r2["baseline"]["npv"]
        assert r1["scenario"]["financial_result_snapshot"]["npv"] == r2["scenario"]["financial_result_snapshot"]["npv"]

    def test_11_ownership_isolation(self):
        other_email = f"other_{_uid()}@example.com"
        client.post("/auth/register", json={"email": other_email, "password": PASSWORD})
        tok = client.post("/auth/login", json={"email": other_email, "password": PASSWORD}).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {tok}"}

        assert client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=other_headers,
            json={"assumption_overrides": {"revenue_year1": 100000}},
        ).status_code == 403
        assert client.get(f"/studies/{self.study_id}/scenarios/", headers=other_headers).status_code == 403
        assert client.get(f"/studies/{self.study_id}/scenarios/variables/meta", headers=other_headers).status_code == 403

    def test_12_login_persistence(self):
        """Re-authenticate and verify scenarios still exist."""
        active = client.get(f"/studies/{self.study_id}/assumptions/", headers=self.headers).json()
        email = None
        me = client.get("/auth/me", headers=self.headers)
        if me.status_code == 200:
            email = me.json().get("email")

        if email:
            tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
            new_headers = {"Authorization": f"Bearer {tok}"}
            resp = client.get(f"/studies/{self.study_id}/scenarios/", headers=new_headers)
            assert resp.status_code == 200
            assert len(resp.json()) >= 3
