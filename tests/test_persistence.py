"""
Persistence tests. Runs against a throwaway SQLite database so CI needs no
external services, while exercising the exact ORM models and the projects
router's DB code path (DB_ENABLED=True).
"""
import os
import sys
import tempfile
from pathlib import Path

# Configure a file-based SQLite DB BEFORE importing app.db so DB_ENABLED is True
# and all connections share the same database file.
_TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _TMP.name

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from app import db as app_db  # noqa: E402
from app import models  # noqa: E402


def setup_module(module):
    assert app_db.DB_ENABLED is True
    app_db.init_db()


def test_project_round_trip():
    session = app_db.SessionLocal()
    try:
        p = models.Project(name="مصنع تمور", industry="agriculture", investment=750000, stage="mvp")
        session.add(p)
        session.commit()
        pid = p.id
    finally:
        session.close()

    session = app_db.SessionLocal()
    try:
        fetched = session.get(models.Project, pid)
        assert fetched is not None
        assert fetched.name == "مصنع تمور"
        assert fetched.investment == 750000
        assert fetched.created_at is not None
    finally:
        session.close()


def test_core_entities_persist():
    session = app_db.SessionLocal()
    try:
        org = models.Organization(name="Acme", name_ar="أكمي", sector="tech")
        session.add(org)
        session.flush()
        role = models.Role(key="entrepreneur", name_en="Entrepreneur", name_ar="رائد أعمال", permissions={"projects": ["create"]})
        session.add(role)
        session.flush()
        user = models.User(email="founder@example.com", hashed_password="x", full_name="Founder", role_key="entrepreneur", organization_id=org.id)
        session.add(user)
        prog = models.FundingProgram(key="ntdp", name_en="NTDP", name_ar="المنشآت التقنية", verification_status="requires_verification")
        session.add(prog)
        idea = models.IdeaBankEntry(title_en="Cold chain SaaS", title_ar="سلسلة تبريد", industry="logistics")
        session.add(idea)
        session.commit()
        assert user.id is not None
    finally:
        session.close()

    session = app_db.SessionLocal()
    try:
        assert session.query(models.User).count() == 1
        assert session.query(models.FundingProgram).filter_by(key="ntdp").one().name_ar == "المنشآت التقنية"
    finally:
        session.close()


def test_projects_router_persists_via_api():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post("/projects/", json={"name": "Solar farm", "industry": "energy", "investment": 1000000, "stage": "growth"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["persisted"] is True
    new_id = body["id"]

    got = client.get(f"/projects/{new_id}")
    assert got.status_code == 200
    assert got.json()["name"] == "Solar farm"

    listing = client.get("/projects/")
    assert any(p["id"] == new_id for p in listing.json())
