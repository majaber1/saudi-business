"""
End-to-end auth tests on a throwaway SQLite DB: register -> login -> /auth/me,
plus password hashing/JWT round-trips and negative cases. No external services.
"""
import os
import sys
import tempfile
from pathlib import Path

if not os.environ.get("DATABASE_URL"):
    _tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _tmp.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters-long")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app import db as app_db  # noqa: E402
from app import auth as security  # noqa: E402


def setup_module(module):
    app_db.init_db()


def test_password_hash_round_trip():
    h = security.hash_password("Sup3rSecret!")
    assert h != "Sup3rSecret!"
    assert security.verify_password("Sup3rSecret!", h) is True
    assert security.verify_password("wrong", h) is False


def test_token_round_trip():
    tok = security.create_access_token(subject="42", extra={"role": "admin"})
    payload = security.decode_token(tok)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert security.decode_token("not-a-token") is None


def _client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def test_register_login_me_flow():
    client = _client()
    email = "founder2@example.com"

    r = client.post("/auth/register", json={
        "email": email, "password": "StrongPass1", "full_name": "Sara", "role_key": "consultant",
    })
    assert r.status_code == 201, r.text
    assert r.json()["role_key"] == "consultant"

    # duplicate registration rejected
    dup = client.post("/auth/register", json={"email": email, "password": "StrongPass1"})
    assert dup.status_code == 409

    # wrong password rejected
    bad = client.post("/auth/login", json={"email": email, "password": "nope"})
    assert bad.status_code == 401

    ok = client.post("/auth/login", json={"email": email, "password": "StrongPass1"})
    assert ok.status_code == 200
    token = ok.json()["access_token"]

    # protected route requires token
    assert client.get("/auth/me").status_code == 401
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_unknown_role_rejected():
    client = _client()
    r = client.post("/auth/register", json={
        "email": "x@example.com", "password": "StrongPass1", "role_key": "wizard",
    })
    assert r.status_code == 422
