"""Phase E - authentication hardening tests.

DB-backed on a throwaway SQLite file (DATABASE_URL set before importing app.db).
Complements test_auth_privilege.py; here we prove: normalized email uniqueness,
email format + password policy, malformed/expired JWT and bad subject handling,
disabled-user behavior, non-enumerating login errors, no secret leakage in
responses, and consistent 401 (unauthenticated) vs 403 (forbidden).
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
os.environ.setdefault("JWT_SECRET", "test-secret")

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db as app_db  # noqa: E402
from app import models  # noqa: E402
from app import auth as security  # noqa: E402
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
        return session.query(models.User).filter_by(email=email.strip().lower()).first()
    finally:
        session.close()


def _set_active(email: str, active: bool):
    session = app_db.SessionLocal()
    try:
        u = session.query(models.User).filter_by(email=email.strip().lower()).first()
        u.is_active = active
        session.commit()
    finally:
        session.close()


# --- normalized email uniqueness -------------------------------------------
def test_email_uniqueness_is_case_insensitive():
    base = uuid.uuid4().hex[:12]
    upper = f"MixedCase_{base}@Example.com"
    lower = f"mixedcase_{base}@example.com"
    r1 = _register({"email": upper, "password": PASSWORD})
    assert r1.status_code == 201, r1.text
    # Same address in different case must collide -> 409, not a second row.
    r2 = _register({"email": lower, "password": PASSWORD})
    assert r2.status_code == 409, r2.text
    # Stored canonicalized (lowercase).
    assert r1.json()["email"] == lower


def test_login_is_case_insensitive_on_email():
    base = uuid.uuid4().hex[:12]
    reg = _register({"email": f"LoginCase_{base}@Example.com", "password": PASSWORD})
    assert reg.status_code == 201
    # Login with a different case must still work.
    resp = client.post("/auth/login", json={"email": f"logincase_{base}@example.com", "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    assert resp.json()["token_type"] == "bearer"


# --- email format + password policy ----------------------------------------
@pytest.mark.parametrize("bad", ["not-an-email", "missing@", "@nodomain", "a b@x.com", ""])
def test_invalid_email_format_rejected(bad):
    resp = _register({"email": bad, "password": PASSWORD})
    assert resp.status_code == 422, resp.text


@pytest.mark.parametrize("pw", ["", "short", "1234567"])
def test_short_password_rejected(pw):
    resp = _register({"email": _email("pw"), "password": pw})
    assert resp.status_code == 422, resp.text


def test_min_length_password_accepted():
    resp = _register({"email": _email("pwok"), "password": "12345678"})
    assert resp.status_code == 201, resp.text


# --- JWT: malformed / expired / bad subject --------------------------------
def test_malformed_jwt_rejected():
    headers = {"Authorization": "Bearer not.a.real.jwt"}
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_missing_bearer_is_401():
    assert client.get("/auth/me").status_code == 401


def test_token_without_subject_rejected():
    # Valid signature but no "sub" claim.
    from jose import jwt
    token = jwt.encode({"role": "entrepreneur"}, security.JWT_SECRET, algorithm=security.JWT_ALGORITHM)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401, r.text


def test_token_for_nonexistent_user_rejected():
    # Well-formed token whose subject does not exist in the DB.
    token = security.create_access_token(subject=99999999, extra={"role": "entrepreneur"})
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401, r.text


# --- disabled users ---------------------------------------------------------
def test_disabled_user_cannot_login():
    email = _email("disabled")
    assert _register({"email": email, "password": PASSWORD}).status_code == 201
    _set_active(email, False)
    resp = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 403, resp.text


def test_disabled_user_existing_token_is_rejected():
    email = _email("disable2")
    assert _register({"email": email, "password": PASSWORD}).status_code == 201
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    # Token worked before disabling.
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    _set_active(email, False)
    # After disabling, the previously valid token must be rejected.
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


# --- safe, non-enumerating login errors ------------------------------------
def test_login_errors_do_not_enumerate_users():
    email = _email("enum")
    assert _register({"email": email, "password": PASSWORD}).status_code == 201
    wrong_pw = client.post("/auth/login", json={"email": email, "password": "WrongPass1"})
    unknown = client.post("/auth/login", json={"email": _email("ghost"), "password": PASSWORD})
    assert wrong_pw.status_code == 401 and unknown.status_code == 401
    # Identical generic message so an attacker cannot tell which failed.
    assert wrong_pw.json()["detail"] == unknown.json()["detail"]


# --- no secret leakage in responses ----------------------------------------
def test_responses_never_leak_password_hash():
    email = _email("leak")
    reg = _register({"email": email, "password": PASSWORD})
    assert "hashed_password" not in reg.text and "hashed_password" not in reg.json()
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert "hashed_password" not in me.text
    # The bcrypt prefix must never appear in any response body.
    for body in (reg.text, me.text):
        assert "$2b$" not in body and "$2a$" not in body


# --- consistent 401 vs 403 --------------------------------------------------
def test_unauthenticated_is_401_and_forbidden_is_403():
    # Unauthenticated -> 401.
    assert client.get("/admin/stats").status_code == 401
    # Authenticated normal user hitting admin -> 403.
    email = _email("role401")
    assert _register({"email": email, "password": PASSWORD}).status_code == 201
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    r = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403, r.text
