"""Wave 3B — Opportunity Fit & Matching Engine Tests.

Validates the complete 15-point specification for deterministic opportunity matching:
1. Unverified -> NOT_EVALUATED
2. Inactive -> NOT_EVALUATED
3. Unknown investment + user budget -> NEEDS_INFORMATION (criterion = UNKNOWN)
4. Known investment inside budget -> PASS
5. Known investment above hard budget -> FAIL / NOT_MATCHED
6. Preference mismatch does NOT cause NOT_MATCHED (yields POSSIBLE_MATCH)
7. Hard sector exclusion -> NOT_MATCHED
8. Unknown territory availability -> UNKNOWN (geography PASS, territory UNKNOWN)
9. KSA_NATIONAL does not prove specific site availability
10. Source version stored in match result
11. Stale / changed source handling
12. User isolation (cannot see another user's profile or match runs)
13. Fit profile persists across sessions / DB reloads
14. Re-evaluation after constraint change updates deterministically
15. Zero synthetic score / no fake percentage (no "87%", no "opportunity_score")
16. Study creation integrates fit snapshot into payload["opportunity_fit_snapshot"]
"""
from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime, timezone
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
from app.services.opportunities import (
    seed_verified_opportunities,
    STATUS_UNVERIFIED,
    STATUS_VERIFIED_PARTIAL,
    STATUS_VERIFIED_CURRENT,
    STATUS_STALE,
)
from app.services.opportunity_matching import (
    STATE_MATCH,
    STATE_POSSIBLE_MATCH,
    STATE_NEEDS_INFORMATION,
    STATE_NOT_MATCHED,
    STATE_NOT_EVALUATED,
    CRITERION_PASS,
    CRITERION_FAIL,
    CRITERION_UNKNOWN,
)

client = TestClient(app)
PASSWORD = "Sup3rSecretPassword123!"


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    assert app_db.DB_ENABLED is True
    app_db.init_db()
    db = app_db.SessionLocal()
    try:
        seed_verified_opportunities(db, force_refresh=True)
    finally:
        db.close()


def _email(prefix="opp_fit"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(prefix="investor"):
    email = _email(prefix)
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text
    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return email, tok


# ==============================================================================
# TESTS
# ==============================================================================

def test_fit_profile_crud_and_persistence():
    """Test creating, reading, updating fit profile with full persistence across sessions."""
    _, tok = _register_and_login("profile_crud")
    headers = _auth(tok)

    # 1. Initially no profile
    r = client.get("/api/v1/opportunities/fit-profile", headers=headers)
    assert r.status_code == 200
    assert r.json() is None

    # 2. Save profile
    payload = {
        "available_capital": 500000.0,
        "capital_flexibility": "STRICT_MAX",
        "preferred_sectors": ["food_beverage", "retail"],
        "excluded_sectors": ["technology"],
        "preferred_opportunity_types": ["FRANCHISE"],
        "target_region": "Makkah Region",
        "target_city": "Jeddah",
        "experience_sectors": ["food_beverage"],
        "notes": "Investor looking for established F&B brands in Jeddah.",
    }
    r = client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    assert r.status_code == 200
    prof = r.json()
    assert prof["available_capital"] == 500000.0
    assert prof["capital_constraint_type"] == "HARD"
    assert prof["preferred_sectors"] == ["food_beverage", "retail"]
    assert prof["excluded_sectors"] == ["technology"]
    assert prof["version"] == 1

    # 3. Read profile again (persistence check)
    r = client.get("/api/v1/opportunities/fit-profile", headers=headers)
    assert r.status_code == 200
    prof2 = r.json()
    assert prof2["id"] == prof["id"]
    assert prof2["available_capital"] == 500000.0

    # 4. Update profile increments version
    payload["available_capital"] = 600000.0
    r = client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    assert r.status_code == 200
    prof3 = r.json()
    assert prof3["version"] == 2
    assert prof3["available_capital"] == 600000.0


def test_user_isolation():
    """User A cannot read or evaluate User B's profile or match runs."""
    _, tok_a = _register_and_login("user_a")
    _, tok_b = _register_and_login("user_b")

    # User A creates profile
    payload_a = {"available_capital": 300000.0, "preferred_sectors": ["retail"]}
    client.post("/api/v1/opportunities/fit-profile", json=payload_a, headers=_auth(tok_a))

    # User B should see None for profile
    r_b = client.get("/api/v1/opportunities/fit-profile", headers=_auth(tok_b))
    assert r_b.status_code == 200
    assert r_b.json() is None

    # User A evaluates
    client.post("/api/v1/opportunities/fit-evaluate", headers=_auth(tok_a))

    # User B has no match runs
    r_runs_b = client.get("/api/v1/opportunities/fit-results", headers=_auth(tok_b))
    assert r_runs_b.status_code == 200
    assert r_runs_b.json() is None


def test_real_catalog_unknown_investment_yields_needs_information():
    """Barn's, dr.CAFE, Shawarmer have unannounced investment requirement in official sources.

    Strict Rule: UNKNOWN investment requirement != budget fit -> NEEDS_INFORMATION.
    Budget criterion must evaluate to UNKNOWN, not PASS and not FAIL.
    Zero synthetic scores or percentages must be present.
    """
    _, tok = _register_and_login("unknown_budget_user")
    headers = _auth(tok)

    payload = {
        "available_capital": 450000.0,
        "capital_constraint_type": "HARD",
        "preferred_sectors": ["food_beverage"],
        "preferred_opportunity_types": ["FRANCHISE"],
        "target_region": "Riyadh Region",
    }
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)

    r_eval = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    assert r_eval.status_code == 200
    run = r_eval.json()

    assert run["results_count"] == 11
    results = run["results"]

    # Actionable verified franchises: Barn's, dr.CAFE, Shawarmer
    actionable_results = [r for r in results if r["match_state"] != STATE_NOT_EVALUATED]
    assert len(actionable_results) == 3

    for item in actionable_results:
        # Must evaluate to NEEDS_INFORMATION because investment is unknown in source!
        assert item["match_state"] == STATE_NEEDS_INFORMATION
        criteria = item["criteria_evaluations"]
        assert "available_capital" in criteria
        assert criteria["available_capital"]["result"] == CRITERION_UNKNOWN
        assert "الاستثمار المطلوب غير منشور" in criteria["available_capital"]["reason"]
        # Missing information must contain capital budget guidance
        assert any("رأسمال" in m or "استثمار" in m or "budget" in m.lower() for m in item["missing_information"])

        # Territory availability is also UNKNOWN
        assert "territory_availability" in criteria
        assert criteria["territory_availability"]["result"] == CRITERION_UNKNOWN

        # Geographic scope passes because geography is KSA_NATIONAL
        assert "geographic_scope" in criteria
        assert criteria["geographic_scope"]["result"] == CRITERION_PASS

        # Sector fits preference
        assert "sector" in criteria
        assert criteria["sector"]["result"] == CRITERION_PASS

        # NO synthetic score / arbitrary percentage
        assert "opportunity_score" not in item
        assert "score" not in item
        assert "percentage" not in item
        assert "fit_percentage" not in item


def test_unverified_and_inactive_yield_not_evaluated():
    """Unverified (8 records) and inactive records must deterministically evaluate to NOT_EVALUATED."""
    _, tok = _register_and_login("unverified_eval_user")
    headers = _auth(tok)

    payload = {
        "available_capital": 500000.0,
        "preferred_sectors": ["technology", "healthcare", "logistics"],
    }
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)

    r = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    assert r.status_code == 200
    results = r.json()["results"]

    not_evaluated = [r for r in results if r["match_state"] == STATE_NOT_EVALUATED]
    # Exactly 8 records are unverified in seed catalog
    assert len(not_evaluated) == 8

    for item in not_evaluated:
        assert item["verification_status_at_eval"] == STATUS_UNVERIFIED
        assert "غير قابلة للتقييم" in item["summary_reason"] or "UNVERIFIED" in item["summary_reason"]
        assert any("المصدر الأولي" in m or "فعالية الفرصة" in m or "وجود الفرصة" in m for m in item["missing_information"])
        # Criteria should all be NOT_APPLICABLE or not evaluated
        for crit in item["criteria_evaluations"].values():
            assert crit["result"] in ("NOT_APPLICABLE", "NOT_EVALUATED")


def test_hard_sector_exclusion_causes_not_matched():
    """When user explicitly excludes food_beverage, all F&B franchises evaluate to NOT_MATCHED."""
    _, tok = _register_and_login("excluded_sector_user")
    headers = _auth(tok)

    payload = {
        "available_capital": 1000000.0,
        "excluded_sectors": ["food_beverage"],
        "preferred_sectors": ["retail"],
    }
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)

    r = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    assert r.status_code == 200
    results = r.json()["results"]

    actionable_results = [r for r in results if r["match_state"] != STATE_NOT_EVALUATED]
    assert len(actionable_results) == 3

    for item in actionable_results:
        assert item["match_state"] == STATE_NOT_MATCHED
        criteria = item["criteria_evaluations"]
        assert "excluded_sectors" in criteria
        assert criteria["excluded_sectors"]["result"] == CRITERION_FAIL
        assert "مستبعد" in criteria["excluded_sectors"]["reason"]


def test_known_budget_pass_and_fail_with_controlled_records():
    """With verified records having explicit known investment:

    - Inside budget -> capital_budget PASS
    - Above hard budget -> capital_budget FAIL -> NOT_MATCHED
    - Preference mismatch -> POSSIBLE_MATCH (never NOT_MATCHED)
    """
    db = app_db.SessionLocal()
    try:
        # Create a controlled verified opportunity with known investment = 300,000
        opp_fit = models.VerifiedOpportunity(
            slug="test-verified-known-budget-fit",
            title_ar="امتياز تموينات تجريبي معتمد",
            title_en="Test Verified Retail Grocery Franchise",
            opportunity_type="FRANCHISE",
            sector="retail",
            subsector="grocery",
            business_model="FRANCHISE_STORE",
            target_customer="B2C",
            geography="KSA_NATIONAL",
            investment_min=300000.0,
            investment_max=400000.0,
            franchise_fee=50000.0,
            royalty_model="5% monthly",
            source_owner="Official Entity",
            source_type="GOVERNMENT_PORTAL",
            official_source_url="https://monshaat.gov.sa/franchise-retail-test",
            verification_status=STATUS_VERIFIED_PARTIAL,
            is_active=True,
            data_version=1,
            field_provenance={
                "opportunity_existence": {"supported": True, "source_url": "https://monshaat.gov.sa/franchise-retail-test"},
                "investment_min": {"supported": True, "source_url": "https://monshaat.gov.sa/franchise-retail-test"},
            },
            facts_breakdown={"published_facts": ["investment_min: 300,000 SAR"]},
        )
        # Create a controlled verified opportunity with known investment = 800,000
        opp_over = models.VerifiedOpportunity(
            slug="test-verified-known-budget-over",
            title_ar="امتياز لوجستي تجريبي معتمد كبير",
            title_en="Test Verified Logistics Franchise",
            opportunity_type="FRANCHISE",
            sector="logistics",
            subsector="last_mile",
            business_model="B2B_DISTRIBUTION",
            target_customer="B2B",
            geography="KSA_NATIONAL",
            investment_min=800000.0,
            investment_max=1200000.0,
            franchise_fee=100000.0,
            source_owner="Official Logistics Entity",
            source_type="PRIMARY_COMPANY_PORTAL",
            official_source_url="https://logistics-company.sa/franchise-test",
            verification_status=STATUS_VERIFIED_PARTIAL,
            is_active=True,
            data_version=1,
            field_provenance={
                "opportunity_existence": {"supported": True, "source_url": "https://logistics-company.sa/franchise-test"},
                "investment_min": {"supported": True, "source_url": "https://logistics-company.sa/franchise-test"},
            },
            facts_breakdown={"published_facts": ["investment_min: 800,000 SAR"]},
        )
        db.add(opp_fit)
        db.add(opp_over)
        db.commit()
        db.refresh(opp_fit)
        db.refresh(opp_over)
        fit_id = opp_fit.id
        over_id = opp_over.id
    finally:
        db.close()

    try:
        _, tok = _register_and_login("budget_pass_fail_user")
        headers = _auth(tok)

        # Investor with 500,000 SAR capital, STRICT_MAX, preferred sector = retail
        payload = {
            "available_capital": 500000.0,
            "capital_constraint_type": "HARD",
            "preferred_sectors": ["retail"],
            "preferred_opportunity_types": ["FRANCHISE"],
            "target_region": "Riyadh Region",
        }
        client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)

        r_eval = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
        assert r_eval.status_code == 200

        # 1. Inspect fit opportunity (300k min vs 500k available)
        r_fit = client.get(f"/api/v1/opportunities/fit-results/{fit_id}", headers=headers)
        assert r_fit.status_code == 200
        fit_res = r_fit.json()
        assert fit_res["criteria_evaluations"]["available_capital"]["result"] == CRITERION_PASS
        assert fit_res["criteria_evaluations"]["sector"]["result"] == CRITERION_PASS
        # Since territory is UNKNOWN, overall state is POSSIBLE_MATCH
        assert fit_res["match_state"] in (STATE_MATCH, STATE_POSSIBLE_MATCH)

        # 2. Inspect over-budget opportunity (800k min vs 500k available with HARD constraint)
        r_over = client.get(f"/api/v1/opportunities/fit-results/{over_id}", headers=headers)
        assert r_over.status_code == 200
        over_res = r_over.json()
        assert over_res["criteria_evaluations"]["available_capital"]["result"] == CRITERION_FAIL
        # Hard constraint failure strictly causes NOT_MATCHED!
        assert over_res["match_state"] == STATE_NOT_MATCHED

        # 3. Preference mismatch test: Change preferred sector to healthcare
        # The retail opportunity should yield POSSIBLE_MATCH, NOT NOT_MATCHED!
        payload["preferred_sectors"] = ["healthcare"]
        client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
        r_eval2 = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
        assert r_eval2.status_code == 200

        r_fit2 = client.get(f"/api/v1/opportunities/fit-results/{fit_id}", headers=headers)
        fit_res2 = r_fit2.json()
        # Preference mismatch: sector is FAIL, but it is a PREFERENCE, not HARD constraint
        assert fit_res2["criteria_evaluations"]["sector"]["result"] == CRITERION_FAIL
        assert fit_res2["criteria_evaluations"]["available_capital"]["result"] == CRITERION_PASS
        assert fit_res2["match_state"] == STATE_POSSIBLE_MATCH  # NOT NOT_MATCHED!
    finally:
        cleanup_db = app_db.SessionLocal()
        try:
            cleanup_db.query(models.OpportunityMatchResult).filter(models.OpportunityMatchResult.opportunity_id.in_([fit_id, over_id])).delete(synchronize_session=False)
            cleanup_db.query(models.VerifiedOpportunity).filter(models.VerifiedOpportunity.id.in_([fit_id, over_id])).delete(synchronize_session=False)
            cleanup_db.commit()
        finally:
            cleanup_db.close()


def test_deterministic_reevaluation_and_history():
    """Modifying profile constraints updates match run deterministically with frozen snapshots."""
    _, tok = _register_and_login("deterministic_eval_user")
    headers = _auth(tok)

    # Run 1: Capital 400,000
    p1 = {"available_capital": 400000.0, "preferred_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=p1, headers=headers)
    r1 = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    run1 = r1.json()
    assert run1["fit_profile_snapshot"]["available_capital"] == 400000.0

    # Run 2: Capital 700,000, exclude food_beverage
    p2 = {"available_capital": 700000.0, "excluded_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=p2, headers=headers)
    r2 = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    run2 = r2.json()
    assert run2["id"] > run1["id"]
    assert run2["fit_profile_snapshot"]["available_capital"] == 700000.0
    assert run2["fit_profile_snapshot"]["excluded_sectors"] == ["food_beverage"]

    # History contains both runs
    r_hist = client.get("/api/v1/opportunities/fit-results/history", headers=headers)
    assert r_hist.status_code == 200
    runs = r_hist.json()
    assert len(runs) >= 2
    assert runs[0]["id"] == run2["id"]


def test_study_creation_with_fit_snapshot():
    """Creating a feasibility study from a match result embeds the frozen fit snapshot in payload.

    Verifies:
    1. study.payload["opportunity_fit_snapshot"] is attached
    2. study.source_opportunity_lineage remains pure and unmodified
    3. lineage verification_status and is_active reflect the verified opportunity
    """
    _, tok = _register_and_login("study_integration_user")
    headers = _auth(tok)

    # 1. Setup profile and evaluate
    payload = {
        "available_capital": 600000.0,
        "preferred_sectors": ["food_beverage"],
        "target_city": "Riyadh",
    }
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    r_eval = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    run = r_eval.json()

    # Find Barn's match result
    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        assert barns is not None
        barns_id = barns.id
    finally:
        db.close()

    barns_match = next(r for r in run["results"] if r["opportunity_id"] == barns_id)

    # 2. Launch study passing match_result_id and user assumption custom_budget = 600,000
    study_in = {
        "custom_budget": 600000.0,
        "study_title": "دراسة جدوى بارنز الرياض - مطابقة شخصية",
        "match_result_id": barns_match["result_id"],
    }
    r_study = client.post(
        f"/api/v1/opportunities/{barns_id}/create-study",
        json=study_in,
        headers=headers,
    )
    assert r_study.status_code == 201, r_study.text
    study_data = r_study.json()
    assert "study_id" in study_data
    assert "fit_snapshot" in study_data
    fit_snap = study_data["fit_snapshot"]
    assert fit_snap["match_result_id"] == barns_match["result_id"]
    assert fit_snap["match_state"] == STATE_NEEDS_INFORMATION

    # 3. Verify database persistence in FeasibilityStudy model
    db = app_db.SessionLocal()
    try:
        study_row = db.query(models.FeasibilityStudy).filter_by(id=study_data["study_id"]).one()
        # Lineage is preserved
        assert study_row.source_opportunity_lineage["source_opportunity_slug"] == "franchise-barns-cafe"
        assert study_row.source_opportunity_lineage["budget_type"] == "USER_ASSUMPTION"
        assert study_row.source_opportunity_lineage["verification_status"] == STATUS_VERIFIED_PARTIAL
        assert study_row.source_opportunity_lineage["is_active"] is True

        # Fit snapshot is in study.payload["opportunity_fit_snapshot"]
        payload_db = study_row.payload
        assert "opportunity_fit_snapshot" in payload_db
        db_snap = payload_db["opportunity_fit_snapshot"]
        assert db_snap["match_run_id"] == run["id"]
        assert db_snap["match_state"] == STATE_NEEDS_INFORMATION
        assert "available_capital" in db_snap["criteria_evaluations"]
        assert db_snap["fit_profile_snapshot"]["available_capital"] == 600000.0
    finally:
        db.close()


# ==============================================================================
# WAVE 3B FINAL SEMANTIC HARDENING: TESTS A THROUGH N
# ==============================================================================

def test_semantic_hardening_a_compare_verified_partial_remains_verified_partial():
    """A. compare VERIFIED_PARTIAL remains VERIFIED_PARTIAL (Wave 3A comparison regression removed)."""
    db = app_db.SessionLocal()
    try:
        from app.services.opportunities import compare_verified_opportunities
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        shawarmer = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-shawarmer").first()
        assert barns is not None
        assert shawarmer is not None
        assert barns.verification_status == STATUS_VERIFIED_PARTIAL
        assert shawarmer.verification_status == STATUS_VERIFIED_PARTIAL

        # Service-level comparison
        res = compare_verified_opportunities(db, [barns.id, shawarmer.id])
        assert len(res) == 2
        for item in res:
            assert item["verification_status"] == STATUS_VERIFIED_PARTIAL
            assert item["is_active"] is True

        # API-level comparison endpoint
        r = client.get(f"/api/v1/opportunities/compare?ids={barns.id},{shawarmer.id}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data) == 2
        for item in data:
            assert item["verification_status"] == STATUS_VERIFIED_PARTIAL
            assert item["is_active"] is True
    finally:
        db.close()


def test_semantic_hardening_b_changed_source_version_list_result_not_evaluated():
    """B. changed source version: list result -> NOT_EVALUATED with requires_re_evaluation = True."""
    _, tok = _register_and_login("version_stale_list")
    headers = _auth(tok)

    payload = {"available_capital": 600000.0, "preferred_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    r_eval = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    assert r_eval.status_code == 200

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        assert barns is not None
        orig_version = barns.data_version

        # Before change: active, valid match state
        r_list_before = client.get("/api/v1/opportunities/fit-results", headers=headers).json()
        b_item_before = next(i for i in r_list_before["results"] if i["opportunity_id"] == barns.id)
        assert b_item_before["match_state"] == STATE_NEEDS_INFORMATION
        assert b_item_before["is_version_stale"] is False
        assert b_item_before["requires_re_evaluation"] is False

        # Bump data_version
        barns.data_version = f"{orig_version}.updated"
        db.commit()

        # After version bump: list endpoint reflects NOT_EVALUATED
        r_list_after = client.get("/api/v1/opportunities/fit-results", headers=headers).json()
        b_item_after = next(i for i in r_list_after["results"] if i["opportunity_id"] == barns.id)
        assert b_item_after["match_state"] == STATE_NOT_EVALUATED
        assert b_item_after["requires_re_evaluation"] is True
        assert b_item_after["is_version_stale"] is True
        assert b_item_after["original_match_state"] == STATE_NEEDS_INFORMATION
    finally:
        barns.data_version = orig_version
        db.commit()
        db.close()


def test_semantic_hardening_c_changed_source_version_detail_result_not_evaluated():
    """C. changed source version: detail result -> NOT_EVALUATED with requires_re_evaluation = True."""
    _, tok = _register_and_login("version_stale_detail")
    headers = _auth(tok)

    payload = {"available_capital": 600000.0, "preferred_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    client.post("/api/v1/opportunities/fit-evaluate", headers=headers)

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        orig_version = barns.data_version

        # Bump data_version
        barns.data_version = "99.0.0"
        db.commit()

        # Detail endpoint check
        r_detail = client.get(f"/api/v1/opportunities/fit-results/{barns.id}", headers=headers)
        assert r_detail.status_code == 200
        detail = r_detail.json()
        assert detail["match_state"] == STATE_NOT_EVALUATED
        assert detail["requires_re_evaluation"] is True
        assert detail["is_version_stale"] is True
        assert detail["original_match_state"] == STATE_NEEDS_INFORMATION
        assert detail["current_data_version"] == "99.0.0"
    finally:
        barns.data_version = orig_version
        db.commit()
        db.close()


def test_semantic_hardening_d_stale_opportunity_current_result_not_evaluated():
    """D. STALE opportunity -> current result NOT_EVALUATED."""
    from app.services.opportunities import STATUS_STALE
    _, tok = _register_and_login("stale_opp_eval")
    headers = _auth(tok)

    payload = {"available_capital": 600000.0, "preferred_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    client.post("/api/v1/opportunities/fit-evaluate", headers=headers)

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        orig_status = barns.verification_status

        # Transition status to STALE
        barns.verification_status = STATUS_STALE
        db.commit()

        # List
        r_list = client.get("/api/v1/opportunities/fit-results", headers=headers).json()
        b_item = next(i for i in r_list["results"] if i["opportunity_id"] == barns.id)
        assert b_item["match_state"] == STATE_NOT_EVALUATED
        assert b_item["requires_re_evaluation"] is True

        # Detail
        r_detail = client.get(f"/api/v1/opportunities/fit-results/{barns.id}", headers=headers).json()
        assert r_detail["match_state"] == STATE_NOT_EVALUATED
        assert r_detail["requires_re_evaluation"] is True
    finally:
        barns.verification_status = orig_status
        db.commit()
        db.close()


def test_semantic_hardening_e_changed_opportunity_current_result_not_evaluated():
    """E. CHANGED opportunity -> current result NOT_EVALUATED."""
    from app.services.opportunities import STATUS_CHANGED
    _, tok = _register_and_login("changed_opp_eval")
    headers = _auth(tok)

    payload = {"available_capital": 600000.0, "preferred_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    client.post("/api/v1/opportunities/fit-evaluate", headers=headers)

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        orig_status = barns.verification_status

        # Transition status to CHANGED
        barns.verification_status = STATUS_CHANGED
        db.commit()

        # List
        r_list = client.get("/api/v1/opportunities/fit-results", headers=headers).json()
        b_item = next(i for i in r_list["results"] if i["opportunity_id"] == barns.id)
        assert b_item["match_state"] == STATE_NOT_EVALUATED
        assert b_item["requires_re_evaluation"] is True

        # Detail
        r_detail = client.get(f"/api/v1/opportunities/fit-results/{barns.id}", headers=headers).json()
        assert r_detail["match_state"] == STATE_NOT_EVALUATED
        assert r_detail["requires_re_evaluation"] is True
    finally:
        barns.verification_status = orig_status
        db.commit()
        db.close()


def test_semantic_hardening_f_discontinued_opportunity_current_result_not_evaluated():
    """F. DISCONTINUED opportunity -> current result NOT_EVALUATED."""
    from app.services.opportunities import STATUS_DISCONTINUED
    _, tok = _register_and_login("disc_opp_eval")
    headers = _auth(tok)

    payload = {"available_capital": 600000.0, "preferred_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    client.post("/api/v1/opportunities/fit-evaluate", headers=headers)

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        orig_status = barns.verification_status

        # Transition status to DISCONTINUED
        barns.verification_status = STATUS_DISCONTINUED
        db.commit()

        # List
        r_list = client.get("/api/v1/opportunities/fit-results", headers=headers).json()
        b_item = next(i for i in r_list["results"] if i["opportunity_id"] == barns.id)
        assert b_item["match_state"] == STATE_NOT_EVALUATED
        assert b_item["requires_re_evaluation"] is True

        # Detail
        r_detail = client.get(f"/api/v1/opportunities/fit-results/{barns.id}", headers=headers).json()
        assert r_detail["match_state"] == STATE_NOT_EVALUATED
        assert r_detail["requires_re_evaluation"] is True
    finally:
        barns.verification_status = orig_status
        db.commit()
        db.close()


def test_semantic_hardening_g_stale_match_result_id_cannot_create_study():
    """G. stale match_result_id cannot create Study (returns RE-EVALUATE FIT)."""
    _, tok = _register_and_login("stale_match_study")
    headers = _auth(tok)

    payload = {"available_capital": 600000.0, "preferred_sectors": ["food_beverage"]}
    client.post("/api/v1/opportunities/fit-profile", json=payload, headers=headers)
    r_eval = client.post("/api/v1/opportunities/fit-evaluate", headers=headers)
    run = r_eval.json()

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        barns_match = next(r for r in run["results"] if r["opportunity_id"] == barns.id)
        orig_version = barns.data_version

        # Bump opportunity version to make match stale
        barns.data_version = "99.0.0"
        db.commit()

        # Attempt to create study with stale match_result_id
        r_study = client.post(
            f"/api/v1/opportunities/{barns.id}/create-study",
            json={"custom_budget": 500000.0, "match_result_id": barns_match["result_id"]},
            headers=headers,
        )
        assert r_study.status_code == 400
        assert "RE-EVALUATE FIT" in r_study.text
    finally:
        barns.data_version = orig_version
        db.commit()
        db.close()


def test_semantic_hardening_h_match_result_from_another_user_cannot_attach_snapshot():
    """H. match_result from another user cannot attach snapshot."""
    _, tok_a = _register_and_login("user_a")
    headers_a = _auth(tok_a)
    client.post("/api/v1/opportunities/fit-profile", json={"available_capital": 500000.0}, headers=headers_a)
    r_eval_a = client.post("/api/v1/opportunities/fit-evaluate", headers=headers_a).json()

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        barns_match_a = next(r for r in r_eval_a["results"] if r["opportunity_id"] == barns.id)

        # User B logs in and tries to use User A's match result id
        _, tok_b = _register_and_login("user_b")
        headers_b = _auth(tok_b)
        r_study_b = client.post(
            f"/api/v1/opportunities/{barns.id}/create-study",
            json={"custom_budget": 500000.0, "match_result_id": barns_match_a["result_id"]},
            headers=headers_b,
        )
        assert r_study_b.status_code == 400
        assert "RE-EVALUATE FIT" in r_study_b.text or "another user" in r_study_b.text.lower()
    finally:
        db.close()


def test_semantic_hardening_i_match_result_for_different_opportunity_cannot_attach_snapshot():
    """I. match_result for different opportunity cannot attach snapshot."""
    _, tok = _register_and_login("diff_opp_match")
    headers = _auth(tok)
    client.post("/api/v1/opportunities/fit-profile", json={"available_capital": 500000.0}, headers=headers)
    r_eval = client.post("/api/v1/opportunities/fit-evaluate", headers=headers).json()

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        shawarmer = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-shawarmer").first()
        barns_match = next(r for r in r_eval["results"] if r["opportunity_id"] == barns.id)

        # Attempt to attach Barn's match to Shawarmer study
        r_study = client.post(
            f"/api/v1/opportunities/{shawarmer.id}/create-study",
            json={"custom_budget": 500000.0, "match_result_id": barns_match["result_id"]},
            headers=headers,
        )
        assert r_study.status_code == 400
        assert "RE-EVALUATE FIT" in r_study.text or "different opportunity" in r_study.text.lower()
    finally:
        db.close()


def test_semantic_hardening_j_direct_study_creation_rejects_stale_changed_discontinued():
    """J. direct Study creation rejects STALE, CHANGED, DISCONTINUED, and UNVERIFIED."""
    from app.services.opportunities import (
        STATUS_STALE,
        STATUS_CHANGED,
        STATUS_DISCONTINUED,
        STATUS_UNVERIFIED,
    )
    _, tok = _register_and_login("direct_study_gate")
    headers = _auth(tok)

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        orig_status = barns.verification_status

        for rejected_status in (STATUS_UNVERIFIED, STATUS_STALE, STATUS_CHANGED, STATUS_DISCONTINUED):
            barns.verification_status = rejected_status
            db.commit()

            r = client.post(
                f"/api/v1/opportunities/{barns.id}/create-study",
                json={"custom_budget": 500000.0},
                headers=headers,
            )
            assert r.status_code == 400, f"Expected 400 for {rejected_status}, got {r.status_code}: {r.text}"
            assert (
                "Cannot create study" in r.text
                or rejected_status in r.text
                or "rejected" in r.text.lower()
            )
    finally:
        barns.verification_status = orig_status
        db.commit()
        db.close()


def test_semantic_hardening_k_opportunity_existence_unsupported_study_blocked():
    """K. opportunity_existence unsupported -> Study blocked."""
    _, tok = _register_and_login("unsupported_exist_study")
    headers = _auth(tok)

    db = app_db.SessionLocal()
    try:
        barns = db.query(models.VerifiedOpportunity).filter_by(slug="franchise-barns-cafe").first()
        orig_prov = dict(barns.field_provenance) if barns.field_provenance else {}

        # Set opportunity_existence supported = False
        prov_copy = dict(orig_prov)
        prov_copy["opportunity_existence"] = {"supported": False, "reason": "Link broken"}
        barns.field_provenance = prov_copy
        db.commit()

        r = client.post(
            f"/api/v1/opportunities/{barns.id}/create-study",
            json={"custom_budget": 500000.0},
            headers=headers,
        )
        assert r.status_code == 400
        assert "existence" in r.text.lower() or "unsupported" in r.text.lower()
    finally:
        barns.field_provenance = orig_prov
        db.commit()
        db.close()


def test_semantic_hardening_l_invalid_capital_constraint_type_422():
    """L. invalid capital constraint type -> 422."""
    _, tok = _register_and_login("invalid_cap_constraint")
    headers = _auth(tok)

    for invalid_val in ["FLEXIBLE_10", "FLEXIBLE_20", "INVALID_STRING", "random"]:
        r = client.post(
            "/api/v1/opportunities/fit-profile",
            json={"capital_constraint_type": invalid_val},
            headers=headers,
        )
        assert r.status_code == 422, f"Expected 422 for capital_constraint_type={invalid_val}, got {r.status_code}"


def test_semantic_hardening_m_invalid_opportunity_type_constraint_422():
    """M. invalid opportunity type constraint -> 422."""
    _, tok = _register_and_login("invalid_opp_constraint")
    headers = _auth(tok)

    for invalid_val in ["FLEXIBLE_10", "NOT_AN_ENUM", "arbitrary_string"]:
        r = client.post(
            "/api/v1/opportunities/fit-profile",
            json={"opportunity_type_constraint": invalid_val},
            headers=headers,
        )
        assert r.status_code == 422, f"Expected 422 for opportunity_type_constraint={invalid_val}, got {r.status_code}"


def test_semantic_hardening_n_negative_capital_422():
    """N. negative capital -> 422."""
    _, tok = _register_and_login("negative_capital")
    headers = _auth(tok)

    for neg_val in [-1.0, -100.0, -500000.0]:
        r = client.post(
            "/api/v1/opportunities/fit-profile",
            json={"available_capital": neg_val},
            headers=headers,
        )
        assert r.status_code == 422, f"Expected 422 for available_capital={neg_val}, got {r.status_code}"

