"""
Tests for the Business Qualification & Readiness API (/api/qualification).

Runs against a throwaway SQLite database (no external services), exercising the
real ORM models, RBAC/ownership, scoring, and the summarized Multazim hand-off.
Follows the same bootstrap pattern as test_auth.py.
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


def setup_module(module):
    assert app_db.DB_ENABLED is True
    app_db.init_db()


def _client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def _auth_headers(client, email, role_key="entrepreneur"):
    client.post("/auth/register", json={
        "email": email, "password": "StrongPass1", "full_name": "T", "role_key": role_key,
    })
    r = client.post("/auth/login", json={"email": email, "password": "StrongPass1"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": "Bearer " + token}


def test_metadata_endpoints_public():
    client = _client()
    cats = client.get("/api/qualification/categories")
    assert cats.status_code == 200
    keys = [c["key"] for c in cats.json()]
    assert "tender" in keys and "saudization" in keys
    for c in cats.json():
        assert c["en"] and c["ar"]  # bilingual labels present

    st = client.get("/api/qualification/statuses")
    assert st.status_code == 200
    assert set(st.json()) == {"missing", "pending", "valid", "expired", "not_applicable"}


def test_requires_auth():
    client = _client()
    assert client.get("/api/qualification/").status_code == 401
    assert client.post("/api/qualification/", json={}).status_code == 401


def test_profile_and_scoring_flow():
    client = _client()
    headers = _auth_headers(client, "owner1@example.com")

    # create profile
    r = client.post("/api/qualification/", json={
        "company_name_en": "Acme", "company_name_ar": "أكمي", "sector": "tech",
    }, headers=headers)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    assert r.json()["owner_id"] is not None

    # add a valid requirement -> score should be 100 for that category
    r = client.post("/api/qualification/" + str(pid) + "/requirements", json={
        "category": "licenses", "title_en": "Commercial Registration", "title_ar": "السجل التجاري",
        "status": "valid",
    }, headers=headers)
    assert r.status_code == 201, r.text

    # add a missing mandatory requirement in another category
    r = client.post("/api/qualification/" + str(pid) + "/requirements", json={
        "category": "certificates", "title_en": "GOSI Certificate", "title_ar": "شهادة التأمينات",
        "status": "missing", "is_mandatory": True,
    }, headers=headers)
    assert r.status_code == 201, r.text

    # score
    r = client.get("/api/qualification/" + str(pid) + "/score", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["category_scores"]["licenses"] == 100.0
    assert body["category_scores"]["certificates"] == 0.0
    assert 0 <= body["overall_score"] <= 100
    # missing analysis includes the missing certificate
    assert any(m["category"] == "certificates" for m in body["missing"])

    # recommendations are bilingual and non-empty (missing mandatory item)
    r = client.get("/api/qualification/" + str(pid) + "/recommendations", headers=headers)
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    assert recs and all("en" in x and "ar" in x for x in recs)


def test_invalid_category_and_status_rejected():
    client = _client()
    headers = _auth_headers(client, "owner2@example.com")
    r = client.post("/api/qualification/", json={"company_name_en": "X"}, headers=headers)
    pid = r.json()["id"]

    bad_cat = client.post("/api/qualification/" + str(pid) + "/requirements", json={
        "category": "nope", "title_en": "A", "title_ar": "أ",
    }, headers=headers)
    assert bad_cat.status_code == 422

    bad_status = client.post("/api/qualification/" + str(pid) + "/requirements", json={
        "category": "tender", "title_en": "A", "title_ar": "أ", "status": "nope",
    }, headers=headers)
    assert bad_status.status_code == 422


def test_ownership_enforced():
    client = _client()
    owner = _auth_headers(client, "owner3@example.com")
    other = _auth_headers(client, "intruder@example.com")

    r = client.post("/api/qualification/", json={"company_name_en": "Secret"}, headers=owner)
    pid = r.json()["id"]

    # other user cannot read the profile
    assert client.get("/api/qualification/" + str(pid), headers=other).status_code == 403
    # other user does not see it in their list
    mine = client.get("/api/qualification/", headers=other).json()
    assert all(p["id"] != pid for p in mine)


def test_multazim_request_summarized_only():
    client = _client()
    headers = _auth_headers(client, "owner4@example.com")
    r = client.post("/api/qualification/", json={"company_name_en": "Grc"}, headers=headers)
    pid = r.json()["id"]

    r = client.post("/api/qualification/" + str(pid) + "/multazim-request", json={
        "scope": "iso27001",
    }, headers=headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "requested"
    assert body["scope"] == "iso27001"
    # only summarized fields exist on the response contract
    assert set(body.keys()) == {
        "id", "profile_id", "scope", "status",
        "summary_score", "summary_en", "summary_ar",
    }

    lst = client.get("/api/qualification/" + str(pid) + "/multazim-request", headers=headers)
    assert lst.status_code == 200
    assert len(lst.json()) == 1
