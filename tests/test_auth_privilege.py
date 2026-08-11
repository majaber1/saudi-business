"""
Targeted privilege-escalation tests for public /auth/register plus an expired-JWT
test. Runs DB-backed on a throwaway SQLite database (DATABASE_URL set before
importing app.db) so DB_ENABLED is True.

Security intent proven here:
- A member of the public can register only as a non-privileged (public) role.
- admin / gov_reviewer can NEVER be obtained through public registration.
- Unknown roles, unsupported locales, and privilege-related payload fields are
  rejected (extra="forbid") rather than silently accepted.
- Rejected requests create neither a User row nor an audit record.
- Admins exist only when provisioned directly via the ORM; such an admin can log
  in and reach an admin-only endpoint, while a normal user cannot.
- A genuinely expired JWT (valid signature, past exp) is rejected with 401.

Standalone run (kept first in CI to isolate order effects):
    pytest tests/test_auth_privilege.py -v
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
# Fix the JWT secret so the expired-token test signs with the same key the app
# verifies with.
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters-long")

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

import pytest  # noqa: E402
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


def _email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.com"


def _register(payload: dict):
    return client.post("/auth/register", json=payload)


def _user_row(email: str):
    session = app_db.SessionLocal()
    try:
        return session.query(models.User).filter_by(email=email).first()
    finally:
        session.close()


def _audit_count() -> int:
    session = app_db.SessionLocal()
    try:
        return session.query(models.AuditLog).count()
    finally:
        session.close()


def _make_admin(email: str, password: str = PASSWORD):
    """Create an admin the only legitimate way: directly via the ORM with the
    real password hasher. Never through /auth/register."""
    session = app_db.SessionLocal()
    try:
        existing = {r.key for r in session.query(models.Role).all()}
        for key, (en, ar) in auth_api.ROLES.items():
            if key not in existing:
                session.add(models.Role(key=key, name_en=en, name_ar=ar, permissions={}))
        session.commit()
        session.add(models.User(
            email=email,
            hashed_password=security.hash_password(password),
            full_name="Admin",
            role_key="admin",
        ))
        session.commit()
    finally:
        session.close()


def _login(email: str, password: str = PASSWORD) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# 1-5: public roles (and the safe default) are accepted
# ---------------------------------------------------------------------------
def test_register_without_role_defaults_to_entrepreneur():
    email = _email("default")
    resp = _register({"email": email, "password": PASSWORD})
    assert resp.status_code == 201, resp.text
    assert resp.json()["role_key"] == "entrepreneur"


@pytest.mark.parametrize("role", ["entrepreneur", "consultant", "investor", "franchise_owner"])
def test_public_role_registration_succeeds(role):
    email = _email(role)
    resp = _register({"email": email, "password": PASSWORD, "role_key": role})
    assert resp.status_code == 201, resp.text
    assert resp.json()["role_key"] == role


# ---------------------------------------------------------------------------
# 6-9: privileged / unknown roles and bad locale are rejected
# ---------------------------------------------------------------------------
def test_admin_public_registration_rejected():
    email = _email("wantadmin")
    resp = _register({"email": email, "password": PASSWORD, "role_key": "admin"})
    assert resp.status_code in (403, 422), resp.text
    assert resp.status_code == 403
    assert _user_row(email) is None


def test_gov_reviewer_public_registration_rejected():
    email = _email("wantgov")
    resp = _register({"email": email, "password": PASSWORD, "role_key": "gov_reviewer"})
    assert resp.status_code in (403, 422), resp.text
    assert resp.status_code == 403
    assert _user_row(email) is None


def test_unknown_role_rejected():
    email = _email("wizard")
    resp = _register({"email": email, "password": PASSWORD, "role_key": "wizard"})
    assert resp.status_code == 422, resp.text
    assert _user_row(email) is None


def test_unsupported_locale_rejected():
    email = _email("locale")
    resp = _register({"email": email, "password": PASSWORD, "locale": "fr"})
    assert resp.status_code == 422, resp.text
    assert _user_row(email) is None


# ---------------------------------------------------------------------------
# 10-15: privilege-related payload fields are rejected (extra="forbid")
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("field,value", [
    ("is_admin", True),
    ("is_staff", True),
    ("is_superuser", True),
    ("permissions", {"projects": ["*"]}),
    ("is_active", True),
    ("organization_id", 1),
    ("owner_id", 1),
])
def test_privilege_field_injection_rejected(field, value):
    email = _email("inject")
    payload = {"email": email, "password": PASSWORD, field: value}
    resp = _register(payload)
    assert resp.status_code == 422, resp.text
    assert _user_row(email) is None


# ---------------------------------------------------------------------------
# 16-17: rejected requests create no User and no audit record
# ---------------------------------------------------------------------------
def test_rejected_privileged_registration_creates_no_user():
    email = _email("norow")
    resp = _register({"email": email, "password": PASSWORD, "role_key": "admin"})
    assert resp.status_code == 403
    assert _user_row(email) is None


def test_rejected_privileged_registration_creates_no_audit():
    before = _audit_count()
    email = _email("noaudit")
    resp = _register({"email": email, "password": PASSWORD, "role_key": "gov_reviewer"})
    assert resp.status_code == 403
    assert _audit_count() == before, "a rejected privileged registration must not write an audit row"


# ---------------------------------------------------------------------------
# 18-20: controlled ORM admin can log in and reach admin endpoint; normal cannot
# ---------------------------------------------------------------------------
def test_orm_admin_can_login():
    email = _email("ormadmin")
    _make_admin(email)
    token = _login(email)
    assert token
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role_key"] == "admin"


def test_orm_admin_can_access_admin_endpoint():
    email = _email("ormadmin2")
    _make_admin(email)
    token = _login(email)
    resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text


def test_normal_user_cannot_access_admin_endpoint():
    email = _email("normal")
    reg = _register({"email": email, "password": PASSWORD})
    assert reg.status_code == 201
    token = _login(email)
    resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Expired JWT: a valid-signature token whose exp is in the past -> 401
# ---------------------------------------------------------------------------
def test_expired_jwt_rejected():
    email = _email("expired")
    reg = _register({"email": email, "password": PASSWORD})
    assert reg.status_code == 201
    uid = reg.json()["id"]

    # Genuinely expired: valid signature, exp 5 minutes in the past.
    expired = security.create_access_token(subject=uid, extra={"role": "entrepreneur"}, expires_minutes=-5)
    # Sanity: it decodes to None (expired), not just malformed.
    assert security.decode_token(expired) is None

    headers = {"Authorization": f"Bearer {expired}"}
    before = _audit_count()

    r1 = client.get("/auth/me", headers=headers)
    assert r1.status_code == 401
    r2 = client.get("/projects/", headers=headers)
    assert r2.status_code == 401
    # Response must not echo token contents and must not mutate the DB.
    assert expired not in r1.text
    assert _audit_count() == before
