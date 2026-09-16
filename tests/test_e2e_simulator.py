"""E2E Decision Simulator journey: register → create Tabea AI SaaS business →
set assumptions → simulate scenarios A/B/C → verify persistence → verify trust
immutability → compare.

Tabea AI baseline: saas_digital, CAPEX=350K, Revenue=240K, OPEX=180K.
No Coffee, no F&B, no restaurant variables.
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


class TestTabeaAISimulatorE2E:
    """Full simulator journey using Tabea AI SaaS baseline."""

    headers = None
    study_id = None
    scenario_ids = []

    @classmethod
    def setup_class(cls):
        email = f"tabea_ai_{_uid()}@example.com"
        assert client.post("/auth/register", json={"email": email, "password": PASSWORD}).status_code == 201
        tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {tok}"}
        cls.email = email

        project = client.post(
            "/projects/", headers=cls.headers,
            json={"name": "تابع AI / Tabea AI", "industry": "saas_digital", "investment": 350000},
        ).json()

        study = client.post(
            "/feasibility/", headers=cls.headers,
            json={"project_id": project["id"], "title": "Tabea AI SaaS Baseline", "industry": "saas_digital", "investment": 350000},
        ).json()
        cls.study_id = study["id"]

        for key, val in [("capex", 350000), ("revenue_year1", 240000), ("opex_annual", 180000), ("growth_rate", 0.15), ("discount_rate", 0.10), ("horizon_years", 5)]:
            r = client.post(
                f"/studies/{cls.study_id}/assumptions/", headers=cls.headers,
                json={"key": key, "label_en": key, "label_ar": key, "value_number": val, "origin": "USER"},
            )
            assert r.status_code == 201

    def test_01_variables_meta_saas(self):
        resp = client.get(f"/studies/{self.study_id}/scenarios/variables/meta", headers=self.headers)
        assert resp.status_code == 200
        body = resp.json()
        keys = [v["key"] for v in body["variables"]]
        assert "revenue_year1" in keys
        assert "capex" in keys
        assert body["current_values"]["capex"] == 350000
        assert body["current_values"]["revenue_year1"] == 240000

    def test_02_scenario_a_subscription_price_increase(self):
        resp = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"scenario_name": "Scenario A: Subscription Price +10%", "assumption_overrides": {"revenue_year1": 264000}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_hypothetical"] is True
        assert body["delta"]["annual_revenue"]["baseline"] == 240000
        assert body["delta"]["annual_revenue"]["scenario"] == 264000
        assert body["delta"]["npv"]["scenario"] > body["delta"]["npv"]["baseline"]
        sv = body["scenario"]["source_assumption_values"]
        assert sv["revenue_year1"]["origin"] == "SCENARIO_ASSUMPTION"
        assert sv["capex"]["origin"] == "BASELINE"
        self.__class__.scenario_ids.append(body["scenario"]["id"])

    def test_03_scenario_b_customer_volume_decrease(self):
        resp = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={
                "scenario_name": "Scenario B: Customer Volume -20%",
                "assumption_overrides": {"revenue_year1": 192000, "growth_rate": 0.0},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["delta"]["npv"]["scenario"] < body["delta"]["npv"]["baseline"]
        sv = body["scenario"]["source_assumption_values"]
        assert sv["revenue_year1"]["origin"] == "SCENARIO_ASSUMPTION"
        assert sv["growth_rate"]["origin"] == "SCENARIO_ASSUMPTION"
        di = body["decision_impact"]
        assert di["scenario_decision"] in ("GO", "CONDITIONAL_GO", "NO_GO", "INSUFFICIENT_EVIDENCE")
        self.__class__.scenario_ids.append(body["scenario"]["id"])

    def test_04_scenario_c_cac_churn_deterioration(self):
        resp = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={
                "scenario_name": "Scenario C: CAC +25% + Churn",
                "assumption_overrides": {"opex_annual": 225000, "growth_rate": 0.0},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["delta"]["operating_result"]["scenario"] < body["delta"]["operating_result"]["baseline"]
        sv = body["scenario"]["source_assumption_values"]
        assert sv["opex_annual"]["origin"] == "SCENARIO_ASSUMPTION"
        assert sv["growth_rate"]["origin"] == "SCENARIO_ASSUMPTION"
        self.__class__.scenario_ids.append(body["scenario"]["id"])

    def test_05_no_coffee_leakage(self):
        scenarios = client.get(f"/studies/{self.study_id}/scenarios/", headers=self.headers).json()
        for s in scenarios:
            name = s["scenario_name"].lower()
            assert "coffee" not in name
            assert "fnb" not in s["scenario_type"].lower()
            overrides = s["assumption_overrides"]
            for key in overrides:
                assert key in ("capex", "revenue_year1", "opex_annual", "growth_rate", "discount_rate", "horizon_years")

    def test_06_persistence_all_scenarios_saved(self):
        resp = client.get(f"/studies/{self.study_id}/scenarios/", headers=self.headers)
        assert resp.status_code == 200
        scenarios = resp.json()
        saved_ids = {s["id"] for s in scenarios}
        for sid in self.scenario_ids:
            assert sid in saved_ids, f"Scenario {sid} not persisted"

    def test_07_persistence_individual_retrieval(self):
        for sid in self.scenario_ids:
            resp = client.get(f"/studies/{self.study_id}/scenarios/{sid}", headers=self.headers)
            assert resp.status_code == 200
            assert resp.json()["id"] == sid
            assert resp.json()["financial_result_snapshot"]["npv"] is not None

    def test_08_baseline_untouched_after_all_scenarios(self):
        active = client.get(f"/studies/{self.study_id}/assumptions/", headers=self.headers).json()
        vals = {a["key"]: a["value_number"] for a in active}
        assert vals["capex"] == 350000
        assert vals["revenue_year1"] == 240000
        assert vals["opex_annual"] == 180000
        assert vals["growth_rate"] == 0.15

    def test_09_trust_grade_stable_across_all_scenarios(self):
        grades = set()
        for _ in range(3):
            resp = client.post(
                f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
                json={"assumption_overrides": {}},
            ).json()
            grades.add(resp["trust"]["grade"])
        assert len(grades) == 1, f"Trust grade changed: {grades}"

    def test_10_compare_endpoint(self):
        resp = client.get(f"/studies/{self.study_id}/scenarios/compare", headers=self.headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "CUSTOM" in body
        assert body["CUSTOM"] is not None

    def test_11_deterministic_reproducibility(self):
        r1 = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"assumption_overrides": {"revenue_year1": 264000}},
        ).json()
        r2 = client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=self.headers,
            json={"assumption_overrides": {"revenue_year1": 264000}},
        ).json()
        assert r1["baseline"]["npv"] == r2["baseline"]["npv"]
        assert r1["scenario"]["financial_result_snapshot"]["npv"] == r2["scenario"]["financial_result_snapshot"]["npv"]

    def test_12_ownership_isolation(self):
        other_email = f"other_{_uid()}@example.com"
        client.post("/auth/register", json={"email": other_email, "password": PASSWORD})
        tok = client.post("/auth/login", json={"email": other_email, "password": PASSWORD}).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {tok}"}

        assert client.post(
            f"/studies/{self.study_id}/scenarios/simulate", headers=other_headers,
            json={"assumption_overrides": {"revenue_year1": 100000}},
        ).status_code == 403
        assert client.get(f"/studies/{self.study_id}/scenarios/", headers=other_headers).status_code == 403

    def test_13_login_persistence(self):
        tok = client.post("/auth/login", json={"email": self.email, "password": PASSWORD}).json()["access_token"]
        new_headers = {"Authorization": f"Bearer {tok}"}
        resp = client.get(f"/studies/{self.study_id}/scenarios/", headers=new_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 3
