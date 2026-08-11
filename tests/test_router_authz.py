"""Cross-router object-level authorization (IDOR) tests.

Proves the ownership fixes for the feasibility and reports routers: an
authenticated user can never read, mutate, compute, or download another
user's feasibility study; the owner and an admin can; and list endpoints are
owner-scoped. DB-backed on a throwaway SQLite file.
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


def _register_login(prefix):
    email = _email(prefix)
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text
    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return email, tok


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _make_admin_login():
    email = _email("admin")
    session = app_db.SessionLocal()
    try:
        existing = {r.key for r in session.query(models.Role).all()}
        for key, (en, ar) in auth_api.ROLES.items():
            if key not in existing:
                session.add(models.Role(key=key, name_en=en, name_ar=ar, permissions={}))
        session.commit()
        session.add(models.User(email=email, hashed_password=security.hash_password(PASSWORD),
                                full_name="Admin", role_key="admin"))
        session.commit()
    finally:
        session.close()
    return client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]


def _create_study(tok, title="Study"):
    r = client.post("/feasibility/", json={
        "title": title, "industry": "tech", "investment": 100000.0,
    }, headers=_auth(tok))
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- feasibility IDOR -------------------------------------------------------
def test_other_user_cannot_read_study():
    _, owner = _register_login("owner")
    _, attacker = _register_login("attacker")
    sid = _create_study(owner)
    r = client.get(f"/feasibility/{sid}", headers=_auth(attacker))
    assert r.status_code == 403, r.text


def test_owner_can_read_own_study():
    _, owner = _register_login("owner2")
    sid = _create_study(owner)
    r = client.get(f"/feasibility/{sid}", headers=_auth(owner))
    assert r.status_code == 200, r.text
    assert r.json()["id"] == sid


def test_admin_can_read_any_study():
    _, owner = _register_login("owner3")
    sid = _create_study(owner)
    admin = _make_admin_login()
    r = client.get(f"/feasibility/{sid}", headers=_auth(admin))
    assert r.status_code == 200, r.text


def test_other_user_cannot_save_step():
    _, owner = _register_login("owner4")
    _, attacker = _register_login("attacker4")
    sid = _create_study(owner)
    r = client.patch(f"/feasibility/{sid}/step", json={"step": 1, "data": {"x": 1}},
                     headers=_auth(attacker))
    assert r.status_code == 403, r.text


def test_other_user_cannot_compute():
    _, owner = _register_login("owner5")
    _, attacker = _register_login("attacker5")
    sid = _create_study(owner)
    r = client.post(f"/feasibility/{sid}/compute",
                    json={"annual_cash_flows": [1000, 2000], "discount_rate": 0.1},
                    headers=_auth(attacker))
    assert r.status_code == 403, r.text


def test_list_studies_is_owner_scoped():
    _, a = _register_login("lista")
    _, b = _register_login("listb")
    sid_a = _create_study(a, "A-study")
    sid_b = _create_study(b, "B-study")
    ids_a = {s["id"] for s in client.get("/feasibility/", headers=_auth(a)).json()}
    ids_b = {s["id"] for s in client.get("/feasibility/", headers=_auth(b)).json()}
    assert sid_a in ids_a and sid_b not in ids_a
    assert sid_b in ids_b and sid_a not in ids_b


def test_create_study_on_foreign_project_forbidden():
    _, owner = _register_login("powner")
    _, attacker = _register_login("pattacker")
    # owner makes a project (via a study auto-creating one)
    sid = _create_study(owner)
    proj_id = client.get(f"/feasibility/{sid}", headers=_auth(owner)).json()["project_id"]
    # attacker tries to attach a study to the owner's project
    r = client.post("/feasibility/", json={
        "title": "hijack", "industry": "tech", "investment": 5000.0, "project_id": proj_id,
    }, headers=_auth(attacker))
    assert r.status_code == 403, r.text


def test_missing_study_returns_404():
    _, owner = _register_login("owner404")
    r = client.get("/feasibility/99999999", headers=_auth(owner))
    assert r.status_code == 404, r.text


# --- reports IDOR (403 gate checked before any generation) -----------------
def test_other_user_cannot_download_report():
    _, owner = _register_login("rowner")
    _, attacker = _register_login("rattacker")
    sid = _create_study(owner)
    r = client.get(f"/reports/study/{sid}", headers=_auth(attacker))
    assert r.status_code == 403, r.text


def test_report_missing_study_returns_404():
    _, owner = _register_login("r404")
    r = client.get("/reports/study/99999999", headers=_auth(owner))
    assert r.status_code == 404, r.text


def test_report_requires_auth():
    r = client.get("/reports/study/1")
    assert r.status_code == 401, r.text
