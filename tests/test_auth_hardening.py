"""Phase E - authentication hardening tests.

DB-backed on a throwaway SQLite file (DATABASE_URL set before importing app.db).
Complements test_auth_privilege.py; here we prove: normalized email uniqueness,
email format + a MEANINGFUL password policy, malformed/expired JWT and bad
subject handling (never HTTP 500), disabled-user behavior, non-enumerating
login errors, no secret leakage in responses, consistent 401 vs 403, and
admin-only privileged-user provisioning via POST /admin/users.
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


def _make_admin_via_orm(password: str = PASSWORD):
    """Create an admin DIRECTLY via the ORM + real hasher (never via public
    registration, which forbids privileged roles). Returns the email."""
    from app.api.auth import _ensure_roles

    email = _email("admin")
    session = app_db.SessionLocal()
    try:
        _ensure_roles(session)
        session.add(
            models.User(
                email=email,
                hashed_password=security.hash_password(password),
                full_name="Root Admin",
                role_key="admin",
                locale="en",
                is_active=True,
            )
        )
        session.commit()
    finally:
        session.close()
    return email


def _token_for(email: str, password: str = PASSWORD) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# --- normalized email uniqueness -------------------------------------------
def test_email_uniqueness_is_case_insensitive():
    base = uuid.uuid4().hex[:12]
    upper = f"MixedCase_{base}@Example.com"
    lower = f"mixedcase_{base}@example.com"
    r1 = _register({"email": upper, "password": PASSWORD})
    assert r1.status_code == 201, r1.text
    r2 = _register({"email": lower, "password": PASSWORD})
    assert r2.status_code == 409, r2.text
    assert r1.json()["email"] == lower


def test_login_is_case_insensitive_on_email():
    base = uuid.uuid4().hex[:12]
    reg = _register({"email": f"LoginCase_{base}@Example.com", "password": PASSWORD})
    assert reg.status_code == 201
    resp = client.post("/auth/login", json={"email": f"logincase_{base}@example.com", "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    assert resp.json()["token_type"] == "bearer"


# --- email format + password policy ----------------------------------------
@pytest.mark.parametrize("bad", ["not-an-email", "missing@", "@nodomain", "a b@x.com", ""])
def test_invalid_email_format_rejected(bad):
    resp = _register({"email": bad, "password": PASSWORD})
    assert resp.status_code == 422, resp.text


@pytest.mark.parametrize("pw", ["", "short", "1234567", "abcdefg"])
def test_too_short_password_rejected(pw):
    resp = _register({"email": _email("pw"), "password": pw})
    assert resp.status_code == 422, resp.text


@pytest.mark.parametrize("pw", ["12345678", "123456789", "password", "password123", "qwerty123", "abcdefgh"])
def test_weak_or_common_password_rejected(pw):
    """Length 8 alone is NOT proof of strength: all-digits, all-letters, and
    common passwords must be rejected even though they are >= 8 chars."""
    resp = _register({"email": _email("weak"), "password": pw})
    assert resp.status_code == 422, f"{pw!r} should be rejected: {resp.text}"
    # The response must never echo the submitted password.
    assert pw not in resp.text


@pytest.mark.parametrize("pw", ["Sup3rSecret!", "correct horse7", "Abcd1234", "myDog2020"])
def test_reasonable_password_accepted(pw):
    resp = _register({"email": _email("good"), "password": pw})
    assert resp.status_code == 201, f"{pw!r} should pass: {resp.text}"


# --- JWT: malformed / expired / bad subject (never 500) --------------------
def test_malformed_jwt_rejected():
    headers = {"Authorization": "Bearer not.a.real.jwt"}
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_missing_bearer_is_401():
    assert client.get("/auth/me").status_code == 401


def test_token_without_subject_rejected():
    import jwt
    token = jwt.encode({"role": "entrepreneur"}, security.JWT_SECRET, algorithm=security.JWT_ALGORITHM)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401, r.text


@pytest.mark.parametrize("sub", [None, "", "  ", "abc", "-1", "0", "1.5", "not-a-number", True])
def test_malformed_subject_returns_401_not_500(sub):
    """A signed token with a bad subject must yield 401, never a 500 from an
    unguarded int() conversion."""
    import jwt
    from datetime import datetime, timedelta, timezone

    claims = {
        "sub": sub,
        "role": "entrepreneur",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(claims, security.JWT_SECRET, algorithm=security.JWT_ALGORITHM)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401, f"sub={sub!r} -> {r.status_code}: {r.text}"


def test_expired_token_rejected():
    """A genuinely expired (not malformed) token must be rejected."""
    import jwt
    from datetime import datetime, timedelta, timezone

    claims = {
        "sub": "1",
        "role": "entrepreneur",
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jwt.encode(claims, security.JWT_SECRET, algorithm=security.JWT_ALGORITHM)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401, r.text


def test_token_for_nonexistent_user_rejected():
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
    token = _token_for(email)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    _set_active(email, False)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


# --- safe, non-enumerating login errors ------------------------------------
def test_login_errors_do_not_enumerate_users():
    email = _email("enum")
    assert _register({"email": email, "password": PASSWORD}).status_code == 201
    wrong_pw = client.post("/auth/login", json={"email": email, "password": "WrongPass1"})
    unknown = client.post("/auth/login", json={"email": _email("ghost"), "password": PASSWORD})
    assert wrong_pw.status_code == 401 and unknown.status_code == 401
    assert wrong_pw.json()["detail"] == unknown.json()["detail"]


# --- no secret leakage in responses ----------------------------------------
def test_responses_never_leak_password_hash():
    email = _email("leak")
    reg = _register({"email": email, "password": PASSWORD})
    assert "hashed_password" not in reg.text and "hashed_password" not in reg.json()
    token = _token_for(email)
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert "hashed_password" not in me.text
    for body in (reg.text, me.text):
        assert "$2b$" not in body and "$2a$" not in body


# --- consistent 401 vs 403 --------------------------------------------------
def test_unauthenticated_is_401_and_forbidden_is_403():
    assert client.get("/admin/stats").status_code == 401
    email = _email("role401")
    assert _register({"email": email, "password": PASSWORD}).status_code == 201
    token = _token_for(email)
    r = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403, r.text


# --- admin-only privileged-user provisioning (POST /admin/users) -----------
def test_admin_users_requires_authentication():
    r = client.post("/admin/users", json={"email": _email("x"), "password": PASSWORD, "role_key": "consultant"})
    assert r.status_code == 401, r.text


def test_admin_users_forbidden_for_normal_user():
    email = _email("normal")
    assert _register({"email": email, "password": PASSWORD}).status_code == 201
    token = _token_for(email)
    r = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": _email("v"), "password": PASSWORD, "role_key": "consultant"},
    )
    assert r.status_code == 403, r.text


def test_admin_can_create_privileged_user():
    admin_email = _make_admin_via_orm()
    token = _token_for(admin_email)
    new_email = _email("gov")
    r = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": new_email, "password": PASSWORD, "role_key": "gov_reviewer", "full_name": "Reviewer"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["role_key"] == "gov_reviewer"
    assert body["email"] == new_email.lower()
    # Never leak the hash.
    assert "hashed_password" not in r.text and "$2b$" not in r.text
    # An audit row for the creation exists.
    session = app_db.SessionLocal()
    try:
        n = (
            session.query(models.AuditLog)
            .filter_by(action="admin.user.create")
            .count()
        )
    finally:
        session.close()
    assert n >= 1


def test_admin_users_duplicate_email_conflict():
    admin_email = _make_admin_via_orm()
    token = _token_for(admin_email)
    dup = _email("dup")
    first = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": dup, "password": PASSWORD, "role_key": "consultant"},
    )
    assert first.status_code == 201, first.text
    second = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": dup.upper(), "password": PASSWORD, "role_key": "consultant"},
    )
    assert second.status_code == 409, second.text


def test_admin_users_rejects_extra_fields():
    admin_email = _make_admin_via_orm()
    token = _token_for(admin_email)
    r = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": _email("extra"),
            "password": PASSWORD,
            "role_key": "consultant",
            "is_active": True,
            "is_admin": True,
        },
    )
    assert r.status_code == 422, r.text


def test_admin_users_enforces_password_policy():
    admin_email = _make_admin_via_orm()
    token = _token_for(admin_email)
    r = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": _email("weakadmin"), "password": "12345678", "role_key": "consultant"},
    )
    assert r.status_code == 422, r.text


def test_admin_users_rejects_unknown_role():
    admin_email = _make_admin_via_orm()
    token = _token_for(admin_email)
    r = client.post(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": _email("badrole"), "password": PASSWORD, "role_key": "superuser"},
    )
    assert r.status_code == 422, r.text
