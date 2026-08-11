"""
Coverage for the two new modules: Investment Opportunities (investor-facing
catalog, filterable by budget) and Sales Leads (public Pricing-page contact
capture, admin-only read). DB-backed on a throwaway SQLite file, mirroring
tests/test_router_authz.py's pattern.
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
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters-long")

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app import db as app_db  # noqa: E402
from app import models  # noqa: E402
from app import auth as security  # noqa: E402
from app.api import auth as auth_api  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
PASSWORD = "Sup3rSecret!"


def setup_module(module):
    assert app_db.DB_ENABLED is True
    app_db.init_db()


def _email(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.com"


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _register_login(prefix, role_key=None):
    email = _email(prefix)
    payload = {"email": email, "password": PASSWORD}
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201, r.text
    if role_key and role_key != "entrepreneur":
        session = app_db.SessionLocal()
        try:
            existing = {r_.key for r_ in session.query(models.Role).all()}
            for key, (en, ar) in auth_api.ROLES.items():
                if key not in existing:
                    session.add(models.Role(key=key, name_en=en, name_ar=ar, permissions={}))
            session.commit()
            user = session.query(models.User).filter_by(email=email).one()
            user.role_key = role_key
            session.commit()
        finally:
            session.close()
    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return email, tok


def _unique_opportunity(**overrides):
    marker = uuid.uuid4().hex[:8]
    payload = {
        "title_en": f"Test Opportunity {marker}",
        "title_ar": f"فرصة اختبار {marker}",
        "industry": "technology",
        "stage": "mvp",
        "risk_level": "medium",
        "investment_min": 50000,
        "investment_max": 150000,
        "expected_return_percent": 15,
    }
    payload.update(overrides)
    return payload


def test_list_opportunities_is_public_and_starts_reachable():
    r = client.get("/opportunities/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_opportunity_requires_admin_or_consultant_role():
    _, entrepreneur_tok = _register_login("entre")
    r = client.post("/opportunities/", json=_unique_opportunity(), headers=_auth(entrepreneur_tok))
    assert r.status_code == 403

    _, admin_tok = _register_login("admin", role_key="admin")
    r = client.post("/opportunities/", json=_unique_opportunity(), headers=_auth(admin_tok))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["verification_status"] == "demo"
    assert body["is_active"] is True


def test_opportunity_budget_filter_excludes_out_of_range():
    _, admin_tok = _register_login("admin2", role_key="admin")
    cheap = client.post(
        "/opportunities/", json=_unique_opportunity(investment_min=10000, investment_max=20000), headers=_auth(admin_tok)
    ).json()
    expensive = client.post(
        "/opportunities/", json=_unique_opportunity(investment_min=2000000, investment_max=5000000), headers=_auth(admin_tok)
    ).json()

    r = client.get("/opportunities/", params={"max_amount": 25000})
    ids = {o["id"] for o in r.json()}
    assert cheap["id"] in ids
    assert expensive["id"] not in ids


def test_opportunity_industry_filter():
    _, admin_tok = _register_login("admin3", role_key="admin")
    created = client.post(
        "/opportunities/", json=_unique_opportunity(industry="healthcare"), headers=_auth(admin_tok)
    ).json()

    r = client.get("/opportunities/", params={"industry": "healthcare"})
    ids = {o["id"] for o in r.json()}
    assert created["id"] in ids
    for o in r.json():
        assert o["industry"] == "healthcare"


def test_get_missing_opportunity_returns_404():
    r = client.get("/opportunities/999999")
    assert r.status_code == 404


def test_submit_lead_is_public_and_persists():
    r = client.post(
        "/leads/",
        json={
            "full_name": "Test Investor",
            "email": f"lead_{uuid.uuid4().hex[:8]}@example.com",
            "company": "Test Capital",
            "plan": "enterprise",
            "intent": "enterprise",
            "message": "Interested",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["received"] is True
    assert body["persisted"] is True


def test_submit_lead_rejects_invalid_email():
    r = client.post("/leads/", json={"full_name": "Bad Email", "email": "not-an-email"})
    assert r.status_code == 422


def test_list_leads_requires_admin():
    _, entrepreneur_tok = _register_login("entre2")
    r = client.get("/leads/", headers=_auth(entrepreneur_tok))
    assert r.status_code == 403

    client.post(
        "/leads/",
        json={"full_name": "Visible To Admin", "email": f"lead_{uuid.uuid4().hex[:8]}@example.com"},
    )
    _, admin_tok = _register_login("admin4", role_key="admin")
    r = client.get("/leads/", headers=_auth(admin_tok))
    assert r.status_code == 200
    assert any(lead["full_name"] == "Visible To Admin" for lead in r.json())
