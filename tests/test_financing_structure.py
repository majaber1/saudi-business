"""
Tests for Phase 20: Financing Structure (Wave 2 — Funding Intelligence Capstone).

Validates deterministic Sources & Uses synthesis, capital structure metrics,
warnings, and next actions.
"""
import pytest
from app.services.financing_structure import (
    compute_financing_structure,
    DISCLAIMER_AR,
    DISCLAIMER_EN,
    RECOMMENDED_MIN_EQUITY_RATIO,
)


class _FakeProject:
    def __init__(self, name="مشروع تجريبي", industry="technology", investment=3_000_000, stage="idea"):
        self.id = 1
        self.name = name
        self.industry = industry
        self.investment = investment
        self.stage = stage


class _FakeStudy:
    def __init__(self, id=1, project_id=1):
        self.id = id
        self.project_id = project_id


class _MockQuery:
    def __init__(self, items):
        self._items = items

    def options(self, *a, **kw):
        return self

    def filter(self, *a, **kw):
        return self

    def order_by(self, *a, **kw):
        return self

    def all(self):
        return self._items


class _MockSession:
    def __init__(self, programs=None):
        self.programs = programs or []

    def query(self, model):
        return _MockQuery(self.programs)


class TestFinancingStructure:

    def test_sources_and_uses_reconciliation(self):
        """Test that Sources & Uses properly balance and reconcile against project requirement."""
        db = _MockSession([])
        project = _FakeProject(investment=3_000_000)
        study = _FakeStudy()

        res = compute_financing_structure(
            db,
            study=study,
            project=project,
            owner_contribution=750_000,
            capex_assumption=3_000_000,
            existing_facilities=0,
        )

        assert res["total_project_requirement"] == 3_000_000.0
        assert res["owner_equity"] == 750_000.0
        assert res["equity_percentage"] == 0.25
        assert res["residual_gap"] == 2_250_000.0

        # Sum of sources amounts must match total project requirement
        sources_total = sum(s["amount"] for s in res["sources"])
        assert sources_total == 3_000_000.0

        # Uses amount must equal total project requirement
        uses_total = sum(u["amount"] for u in res["uses"])
        assert uses_total == 3_000_000.0

    def test_low_owner_equity_warning(self):
        """When equity is below 20%, a warning should be triggered."""
        db = _MockSession([])
        project = _FakeProject(investment=3_000_000)
        study = _FakeStudy()

        res = compute_financing_structure(
            db,
            study=study,
            project=project,
            owner_contribution=300_000,  # 10% < 20%
            capex_assumption=3_000_000,
        )

        warning_codes = [w["code"] for w in res["warnings"]]
        assert "LOW_OWNER_EQUITY" in warning_codes
        assert "RESIDUAL_GAP_EXISTS" in warning_codes

        low_eq = [w for w in res["warnings"] if w["code"] == "LOW_OWNER_EQUITY"][0]
        assert "300,000" not in low_eq["message_ar"] or "10.0%" in low_eq["message_ar"]

    def test_exceeds_safe_debt_capacity_warning(self):
        """When debt exceeds assessed safe debt capacity, an alert should be raised."""
        db = _MockSession([])
        project = _FakeProject(investment=5_000_000)
        study = _FakeStudy()

        # Financial period with limited EBITDA yielding modest debt capacity
        financial_period = {
            "revenue": 1_000_000,
            "ebitda": 100_000,
            "total_debt": 0,
            "debt_service": 20_000,
        }

        res = compute_financing_structure(
            db,
            study=study,
            project=project,
            owner_contribution=1_000_000,
            capex_assumption=5_000_000,
            existing_facilities=1_500_000,  # Debt of 1.5M > safe capacity
            financial_period_dict=financial_period,
        )

        warning_codes = [w["code"] for w in res["warnings"]]
        assert "EXCEEDS_SAFE_DEBT_CAPACITY" in warning_codes

    def test_collateral_shortfall_warning(self):
        """When debt is unsecured or collateral is partial, advisory warning is generated."""
        db = _MockSession([])
        project = _FakeProject(investment=3_000_000)
        study = _FakeStudy()

        res = compute_financing_structure(
            db,
            study=study,
            project=project,
            owner_contribution=1_000_000,
            capex_assumption=3_000_000,
            existing_facilities=1_000_000,
            collateral_dicts=[{
                "id": 1,
                "collateral_type": "PROPERTY",
                "reported_value": 400_000,
                "verified_value": 400_000,
                "encumbrance_status": "UNENCUMBERED",
                "encumbrance_amount": 0,
                "verification_status": "VERIFIED",
            }],
        )

        warning_codes = [w["code"] for w in res["warnings"]]
        assert "COLLATERAL_SHORTFALL" in warning_codes
        assert res["collateral_coverage_ratio"] == 0.4

    def test_next_actions_generation(self):
        """Verify sequential next actions roadmap is generated."""
        db = _MockSession([])
        project = _FakeProject(investment=3_000_000)
        study = _FakeStudy()

        res = compute_financing_structure(
            db,
            study=study,
            project=project,
            owner_contribution=750_000,
            capex_assumption=3_000_000,
        )

        actions = res["next_actions"]
        assert len(actions) == 4
        assert actions[0]["step_number"] == 1
        assert "السجل التجاري" in actions[0]["title_ar"]

    def test_mandatory_disclaimers(self):
        """Verify regulatory disclaimers are present in both languages."""
        db = _MockSession([])
        project = _FakeProject(investment=2_000_000)
        study = _FakeStudy()

        res = compute_financing_structure(
            db,
            study=study,
            project=project,
            owner_contribution=500_000,
            capex_assumption=2_000_000,
        )

        assert res["disclaimer_ar"] == DISCLAIMER_AR
        assert res["disclaimer_en"] == DISCLAIMER_EN
        assert "استرشادي" in res["disclaimer_ar"]
        assert "advisory" in res["disclaimer_en"].lower()
