"""
Targeted ownership & RBAC tests for the Projects API.

These run against a throwaway SQLite database (DATABASE_URL set before importing
app.db) so DB_ENABLED is True and the DB-backed code path is exercised — the same
mode used in production, just on SQLite. Auth requires persistence, so every test
here implicitly proves the DB-backed ownership behavior (task requirement 13).

Isolation notes:
- app.db resolves DATABASE_URL once at import time and caches the engine, so this
  module cooperates with whatever set DATABASE_URL first (guarded assignment) and
  uses unique emails/names + filtered assertions instead of global row counts.
- Run standalone first to catch order-dependent failures:
      pytest tests/test_projects_auth.py -v
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path

# Configure a file-based SQLite DB BEFORE importing app.db so DB_ENABLED is True
# and every connection shares the same database file.
if not os.environ.get("DATABASE_URL"):
    _TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _TMP.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _TMP.name

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db as app_db  # noqa: E402
from app import models  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def setup_module(module):
    # Tables must exist before the API touches them.
    assert app_db.DB_ENABLED is True
    app_db.init_db()


def _email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.com"


def _register(email: str, password: str = "Sup3rSecret!", role_key: str = "entrepreneur"):
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "T", "role_key": role_key},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _token(email: str, password: str = "Sup3rSecret!") -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(email: str, password: str = "Sup3rSecret!", role_key: str = "entrepreneur"):
    """Register (idempotent-ish via unique email) + login, return Authorization headers."""
    _register(email, password=password, role_key=role_key)
    return {"Authorization": f"Bearer {_token(email, password)}"}


def _make_admin_and_login(email: str, password: str = "Sup3rSecret!"):
    """Create an admin directly via the ORM (public registration can never mint
    admins) using the real password hasher, then authenticate through the normal
    login endpoint and return Authorization headers."""
    from app import auth as security

    session = app_db.SessionLocal()
    try:
        # Ensure the canonical roles (incl. admin) exist for the FK.
        existing = {r.key for r in session.query(models.Role).all()}
        if "admin" not in existing:
            session.add(models.Role(key="admin", name_en="Administrator", name_ar="مدير النظام", permissions={}))
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

    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}

_PROJECT = {"name": "Solar farm", "industry": "energy", "investment": 1000000, "stage": "growth"}


# ---------------------------------------------------------------------------
# 1-3: anonymous access is rejected with 401 on every endpoint
# ---------------------------------------------------------------------------
def test_anonymous_post_projects_401():
    resp = client.post("/projects/", json=_PROJECT)
    assert resp.status_code == 401, resp.text


def test_anonymous_list_projects_401():
    resp = client.get("/projects/")
    assert resp.status_code == 401, resp.text


def test_anonymous_get_project_401():
    resp = client.get("/projects/1")
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# 4-5: authenticated creation returns 201 and owner_id is the caller's id
# ---------------------------------------------------------------------------
def test_authenticated_create_returns_201_and_owner():
    email = _email("creator")
    headers = _auth(email)
    me = client.get("/auth/me", headers=headers).json()

    resp = client.post("/projects/", json=_PROJECT, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["owner_id"] == me["id"]
    assert body["persisted"] is True


# ---------------------------------------------------------------------------
# 6: a client-supplied owner_id must never override the server assignment
# ---------------------------------------------------------------------------
def test_client_supplied_owner_id_is_ignored():
    victim = _register(_email("victim"))
    email = _email("attacker")
    headers = _auth(email)
    me = client.get("/auth/me", headers=headers).json()

    payload = dict(_PROJECT, owner_id=victim["id"])  # attempt to plant someone else's id
    resp = client.post("/projects/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # Server assigns the authenticated caller, never the injected value.
    assert body["owner_id"] == me["id"]
    assert body["owner_id"] != victim["id"]


# ---------------------------------------------------------------------------
# 7: a user lists only their own projects
# ---------------------------------------------------------------------------
def test_user_lists_only_own_projects():
    a_headers = _auth(_email("lister_a"))
    b_headers = _auth(_email("lister_b"))
    a_id = client.get("/auth/me", headers=a_headers).json()["id"]

    pa = client.post("/projects/", json=dict(_PROJECT, name="A-owned"), headers=a_headers).json()
    client.post("/projects/", json=dict(_PROJECT, name="B-owned"), headers=b_headers)

    listing = client.get("/projects/", headers=a_headers)
    assert listing.status_code == 200
    rows = listing.json()
    assert any(p["id"] == pa["id"] for p in rows)
    assert all(p["owner_id"] == a_id for p in rows)


# ---------------------------------------------------------------------------
# 8: another user cannot read the owner's project -> 403
# ---------------------------------------------------------------------------
def test_other_user_cannot_read_project_403():
    owner_headers = _auth(_email("owner8"))
    other_headers = _auth(_email("other8"))
    pid = client.post("/projects/", json=_PROJECT, headers=owner_headers).json()["id"]

    resp = client.get(f"/projects/{pid}", headers=other_headers)
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 9: admin can read another user's project
# ---------------------------------------------------------------------------
def test_admin_can_read_others_project():
    owner_headers = _auth(_email("owner9"))
    admin_headers = _make_admin_and_login(_email("admin9"))
    pid = client.post("/projects/", json=_PROJECT, headers=owner_headers).json()["id"]

    resp = client.get(f"/projects/{pid}", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == pid


# ---------------------------------------------------------------------------
# 10: unknown project -> 404 (owner authenticated, id does not exist)
# ---------------------------------------------------------------------------
def test_unknown_project_returns_404():
    headers = _auth(_email("finder10"))
    resp = client.get("/projects/99999999", headers=headers)
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# 11: an invalid/garbage token -> 401
# ---------------------------------------------------------------------------
def test_invalid_token_returns_401():
    headers = {"Authorization": "Bearer not-a-real-jwt"}
    assert client.get("/projects/", headers=headers).status_code == 401
    assert client.post("/projects/", json=_PROJECT, headers=headers).status_code == 401


# ---------------------------------------------------------------------------
# 12: a disabled user cannot access projects even with a previously valid token
# ---------------------------------------------------------------------------
def test_disabled_user_cannot_access_projects():
    email = _email("disabled12")
    headers = _auth(email)
    # Sanity: works while active.
    assert client.get("/projects/", headers=headers).status_code == 200

    # Disable the account directly in the DB.
    session = app_db.SessionLocal()
    try:
        user = session.query(models.User).filter_by(email=email).one()
        user.is_active = False
        session.commit()
    finally:
        session.close()

    # get_current_user rejects inactive users.
    assert client.get("/projects/", headers=headers).status_code == 401
    # And login is refused too (403 Account disabled).
    assert client.post("/auth/login", json={"email": email, "password": "Sup3rSecret!"}).status_code == 403


# ---------------------------------------------------------------------------
# 13: the same ownership behavior is enforced in database-backed mode.
# Every test above already runs DB-backed; this asserts the row is truly
# persisted with the server-assigned owner_id (not just an in-memory echo).
# ---------------------------------------------------------------------------
def test_ownership_enforced_in_database_backed_mode():
    assert app_db.DB_ENABLED is True
    email = _email("dbmode13")
    headers = _auth(email)
    me = client.get("/auth/me", headers=headers).json()
    pid = client.post("/projects/", json=_PROJECT, headers=headers).json()["id"]

    session = app_db.SessionLocal()
    try:
        row = session.get(models.Project, pid)
        assert row is not None
        assert row.owner_id == me["id"]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 14: demo/in-memory persistence must never be silently enabled in production.
# app.db._resolve_url reads the environment live, so we can verify the policy
# without mutating the cached engine: in production with no DB env vars it must
# refuse to fall back to SQLite (returns None, disabled) rather than pretend.
# ---------------------------------------------------------------------------
def test_no_demo_fallback_in_production(monkeypatch):
    for var in ("DATABASE_URL", "POSTGRES_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    url, from_env = app_db._resolve_url()
    assert url is None, "production must not fabricate a SQLite demo database"
    assert from_env is False

    # Outside production, an explicit demo fallback is allowed (and clearly not from_env).
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev_url, dev_from_env = app_db._resolve_url()
    assert dev_url is not None and dev_url.startswith("sqlite")
    assert dev_from_env is False
