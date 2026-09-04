"""Wave 3 — First Vertical Slice Tests: Verified Opportunity & Franchise Registry.

Validates:
1. Persistent verified registry for business and franchise opportunities.
2. Complete provenance and official source metadata (.gov.sa / official brand disclosures).
3. Zero fabrication rule: unknown fields stay null, no fake scores or invented financials.
4. Facts breakdown: published vs normalized vs unknown vs user assumptions.
5. Filtering by type, sector, budget fit, geography, and keyword search.
6. Factual side-by-side comparison without weighted scoring.
7. Create Study from Opportunity integration:
   - Creates persistent Project, FeasibilityStudy, and BusinessProfile.
   - Preserves source opportunity ID, version, and provenance lineage.
   - Survives database re-queries.
8. Admin updates retain immutable version history.
"""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
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
from app.api import auth as auth_api
from app.services.opportunities import seed_verified_opportunities

client = TestClient(app)
PASSWORD = "Sup3rSecretPassword123!"


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    assert app_db.DB_ENABLED is True
    app_db.init_db()
    # Seed verified registry
    db = app_db.SessionLocal()
    try:
        seed_verified_opportunities(db)
    finally:
        db.close()


def _email(prefix="test_opp"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(prefix="user", role_key="entrepreneur"):
    email = _email(prefix)
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text

    if role_key != "entrepreneur":
        session = app_db.SessionLocal()
        try:
            existing_roles = {r_.key for r_ in session.query(models.Role).all()}
            for k, (en, ar) in auth_api.ROLES.items():
                if k not in existing_roles:
                    session.add(models.Role(key=k, name_en=en, name_ar=ar, permissions={}))
            session.commit()
            user = session.query(models.User).filter_by(email=email).one()
            user.role_key = role_key
            session.commit()
        finally:
            session.close()

    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return email, tok


# ==============================================================================
# TESTS
# ==============================================================================

def test_catalog_seeded_and_persisted():
    """Verify that verified opportunities and franchises exist in persistent store."""
    r = client.get("/api/v1/opportunities/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 11

    # Check distribution between business opportunities and franchises
    biz_opps = [i for i in items if i["opportunity_type"] == "BUSINESS_OPPORTUNITY"]
    franchises = [i for i in items if i["opportunity_type"] == "FRANCHISE"]
    assert len(biz_opps) >= 5
    assert len(franchises) >= 6


def test_business_opportunity_fields_and_provenance():
    """Verify business opportunity fields, provenance, and lack of fabricated values."""
    r = client.get("/api/v1/opportunities/?type=BUSINESS_OPPORTUNITY")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 5

    sample = next(i for i in items if i["slug"] == "monshaat-food-processing-hub")
    assert sample["title_ar"] == "مركز تعبئة وتجهيز المنتجات الغذائية والتمور المحلية"
    assert sample["sector"] == "manufacturing"
    assert sample["geography"] == "QASSIM"
    assert sample["city"] == "بريدة"
    assert sample["investment_min"] == 650000.0
    assert sample["investment_max"] == 1800000.0
    assert sample["franchise_fee"] is None  # not a franchise
    assert sample["source_owner"] == "الهيئة العامة للمنشآت الصغيرة والمتوسطة (منشآت)"
    assert sample["source_type"] == "OFFICIAL_GOVERNMENT"
    assert sample["verification_status"] == "VERIFIED_CURRENT"
    assert sample["official_source_url"].startswith("https://")
    assert sample["data_version"] == "1.0.0"

    # Verify no fake ROI, IRR, or success rate fields exist in the model
    assert "expected_return" not in sample
    assert "roi" not in sample
    assert "opportunity_score" not in sample


def test_franchise_opportunity_fields_and_provenance():
    """Verify franchise opportunity fields, franchise fees, space requirements, and official source."""
    r = client.get("/api/v1/opportunities/?type=FRANCHISE")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 6

    barns = next(i for i in items if i["slug"] == "franchise-barns-cafe")
    assert barns["brand_name"] == "Barn's (بارنز)"
    assert barns["sector"] == "food_beverage"
    assert barns["franchise_fee"] == 60000.0
    assert barns["investment_min"] == 350000.0
    assert barns["investment_max"] == 800000.0
    assert barns["required_space"] == "30-120 م² (كشك أو سيارات أو صالة)"
    assert barns["source_type"] == "OFFICIAL_BRAND"
    assert barns["source_owner"] == "شركة الأمجاد للأغذية والمشروبات (بارنز)"
    assert barns["verification_status"] == "VERIFIED_CURRENT"
    assert barns["official_source_url"] == "https://barns.com.sa/franchise"


def test_detail_endpoint_facts_breakdown_and_version_history():
    """Verify get detail endpoint separates published facts, normalized facts, and unknowns."""
    # Fetch list first to get an ID
    items = client.get("/api/v1/opportunities/").json()
    target = items[0]

    r = client.get(f"/api/v1/opportunities/{target['id']}")
    assert r.status_code == 200
    detail = r.json()

    assert detail["id"] == target["id"]
    assert "facts_breakdown" in detail
    breakdown = detail["facts_breakdown"]
    assert "published_facts" in breakdown
    assert len(breakdown["published_facts"]) >= 1
    assert "platform_normalized_facts" in breakdown
    assert "unknowns" in breakdown
    assert len(breakdown["unknowns"]) >= 1
    assert "user_assumptions_needed" in breakdown

    # Version history loaded
    assert "version_history" in detail
    assert len(detail["version_history"]) >= 1
    assert detail["version_history"][0]["data_version"] == target["data_version"]


def test_filtering_capabilities():
    """Verify filtering by sector, budget fit, geography, and search term."""
    # 1. Filter by sector
    r = client.get("/api/v1/opportunities/?sector=logistics")
    assert r.status_code == 200
    logistics_items = r.json()
    assert len(logistics_items) >= 1
    assert all(i["sector"] == "logistics" for i in logistics_items)

    # 2. Filter by max budget (affordability: min investment <= budget)
    r = client.get("/api/v1/opportunities/?max_budget=400000")
    assert r.status_code == 200
    budget_items = r.json()
    assert len(budget_items) >= 1
    for item in budget_items:
        if item["investment_min"] is not None:
            assert item["investment_min"] <= 400000

    # 3. Filter by geography
    r = client.get("/api/v1/opportunities/?geography=QASSIM")
    assert r.status_code == 200
    qassim_items = r.json()
    assert len(qassim_items) >= 1
    assert any(i["geography"] == "QASSIM" for i in qassim_items)

    # 4. Search query
    r = client.get("/api/v1/opportunities/?search=شاورمر")
    assert r.status_code == 200
    search_items = r.json()
    assert len(search_items) >= 1
    assert search_items[0]["slug"] == "franchise-shawarmer"


def test_side_by_side_comparison():
    """Verify factual side-by-side comparison without synthetic weighting."""
    items = client.get("/api/v1/opportunities/?type=FRANCHISE").json()
    id1 = items[0]["id"]
    id2 = items[1]["id"]

    r = client.get(f"/api/v1/opportunities/compare?ids={id1},{id2}")
    assert r.status_code == 200
    comparison = r.json()
    assert len(comparison) == 2

    c1 = next(c for c in comparison if c["id"] == id1)
    c2 = next(c for c in comparison if c["id"] == id2)

    assert "sector" in c1 and "sector" in c2
    assert "investment_min" in c1 and "investment_min" in c2
    assert "franchise_fee" in c1 and "franchise_fee" in c2
    assert "source_owner" in c1 and "source_owner" in c2
    assert "verification_status" in c1 and "verification_status" in c2

    # Reject invalid comparison requests
    r_bad = client.get("/api/v1/opportunities/compare?ids=abc,xyz")
    assert r_bad.status_code == 400


def test_create_study_from_opportunity_end_to_end():
    """Verify mandatory Create Study integration carries verified facts, persists lineage, and enforces auth."""
    # 1. Unauthenticated call must fail with 401
    items = client.get("/api/v1/opportunities/?type=FRANCHISE").json()
    barns = next(i for i in items if i["slug"] == "franchise-barns-cafe")

    r_unauth = client.post(f"/api/v1/opportunities/{barns['id']}/create-study", json={})
    assert r_unauth.status_code == 401

    # 2. Authenticated user creates study from opportunity
    email, token = _register_and_login("founder_study")
    r_create = client.post(
        f"/api/v1/opportunities/{barns['id']}/create-study",
        json={"study_title": "دراسة جدوى فرع بارنز - الرياض"},
        headers=_auth(token),
    )
    assert r_create.status_code == 201, r_create.text
    created = r_create.json()

    assert "project_id" in created
    assert "study_id" in created
    assert created["opportunity_id"] == barns["id"]
    lineage = created["lineage"]

    # Verify transferred lineage facts
    assert lineage["source_opportunity_id"] == barns["id"]
    assert lineage["source_opportunity_slug"] == barns["slug"]
    assert lineage["source_owner"] == barns["source_owner"]
    assert lineage["official_source_url"] == barns["official_source_url"]
    assert lineage["verification_status"] == barns["verification_status"]
    assert lineage["data_version"] == barns["data_version"]
    assert lineage["transferred_facts"]["franchise_fee"] == 60000.0

    # 3. Verify Project and Study persistence in DB
    db = app_db.SessionLocal()
    try:
        project = db.get(models.Project, created["project_id"])
        assert project is not None
        assert project.industry == barns["sector"]
        assert project.investment == barns["investment_min"]
        assert project.workflow_status == "from_opportunity"

        study = db.get(models.FeasibilityStudy, created["study_id"])
        assert study is not None
        assert study.source_opportunity_id == barns["id"]
        assert study.source_opportunity_version == barns["data_version"]
        assert study.source_opportunity_lineage["source_opportunity_slug"] == barns["slug"]
        assert study.study_type == "franchise_feasibility"

        # Verify BusinessProfile was populated with verified facts
        profile = db.query(models.BusinessProfile).filter_by(study_id=study.id).first()
        assert profile is not None
        assert profile.business_activity == barns["title_ar"]
        assert profile.customer_segment == barns["target_customer"]
        assert profile.is_existing_business is False
    finally:
        db.close()


def test_opportunity_version_history_on_update():
    """Verify admin updates increment semantic version and retain audit trail without silent overwrite."""
    _, admin_token = _register_and_login("admin_user", role_key="admin")

    items = client.get("/api/v1/opportunities/?type=BUSINESS_OPPORTUNITY").json()
    target = items[0]
    initial_version = target["data_version"]

    patch_payload = {
        "investment_max": 2500000.0,
        "change_reason": "تحديث سقف الاستثمار التقديري بناءً على نشرة منشآت الربعية المحدثة",
    }
    r = client.patch(
        f"/api/v1/opportunities/{target['id']}",
        json=patch_payload,
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    updated = r.json()

    assert updated["investment_max"] == 2500000.0
    assert updated["data_version"] != initial_version
    # Version history has at least 2 entries (initial + update)
    assert len(updated["version_history"]) >= 2
    latest_hist = updated["version_history"][0]
    assert latest_hist["change_reason"] == patch_payload["change_reason"]
    assert latest_hist["data_version"] == updated["data_version"]
