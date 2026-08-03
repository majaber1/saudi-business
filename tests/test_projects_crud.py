"""Projects full-lifecycle tests (Phase F): update / archive / unarchive /
soft-delete, with ownership, admin override, strict payloads, archived-list
filtering, audit records, and DB-backed persistence.

DB-backed on a throwaway SQLite file (DATABASE_URL set before importing app.db).
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
_PROJECT = {"name": "Solar farm", "industry": "energy", "investment": 1000000, "stage": "growth"}


def setup_module(module):
    assert app_db.DB_ENABLED is True
    app_db.init_db()


def _email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}@example.com"


def _auth(prefix: str):
    email = _email(prefix)
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text
    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _admin_auth(prefix: str):
    email = _email(prefix)
    session = app_db.SessionLocal()
    try:
        existing = {r.key for r in session.query(models.Role).all()}
        if "admin" not in existing:
            session.add(models.Role(key="admin", name_en="Administrator", name_ar="مدير", permissions={}))
            session.commit()
        session.add(models.User(email=email, hashed_password=security.hash_password(PASSWORD),
                                full_name="Admin", role_key="admin"))
        session.commit()
    finally:
        session.close()
    tok = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _create(headers, **overrides):
    r = client.post("/projects/", json=dict(_PROJECT, **overrides), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _audit_count(action: str, entity_id: int) -> int:
    session = app_db.SessionLocal()
    try:
        return (
            session.query(models.AuditLog)
            .filter_by(action=action, entity="project", entity_id=entity_id)
            .count()
        )
    finally:
        session.close()


# --- anonymous is rejected on every lifecycle route -------------------------
@pytest.mark.parametrize("method,path", [
    ("patch", "/projects/1"),
    ("post", "/projects/1/archive"),
    ("post", "/projects/1/unarchive"),
    ("delete", "/projects/1"),
])
def test_anonymous_lifecycle_is_401(method, path):
    resp = getattr(client, method)(path, json={})
    assert resp.status_code == 401, resp.text


# --- update -----------------------------------------------------------------
def test_owner_can_update_project():
    headers = _auth("upd_owner")
    pid = _create(headers)["id"]
    r = client.patch(f"/projects/{pid}", json={"name": "Renamed", "investment": 2500000}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Renamed"
    assert body["investment"] == 2500000
    assert _audit_count("project.update", pid) >= 1


def test_non_owner_cannot_update_403():
    owner = _auth("upd_o")
    other = _auth("upd_x")
    pid = _create(owner)["id"]
    r = client.patch(f"/projects/{pid}", json={"name": "Hacked"}, headers=other)
    assert r.status_code == 403, r.text


def test_update_unknown_id_404():
    headers = _auth("upd_404")
    r = client.patch("/projects/99999999", json={"name": "X"}, headers=headers)
    assert r.status_code == 404, r.text


def test_admin_can_update_any_project():
    owner = _auth("upd_ownadm")
    admin = _admin_auth("upd_admin")
    pid = _create(owner)["id"]
    r = client.patch(f"/projects/{pid}", json={"stage": "scale"}, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["stage"] == "scale"


def test_update_cannot_change_owner_or_internal_fields():
    owner = _auth("upd_immut")
    victim = _auth("upd_victim")
    victim_id = client.get("/auth/me", headers=victim).json()["id"]
    pid = _create(owner)["id"]
    # owner_id / is_archived / id are internal -> strict schema rejects them (422).
    for payload in ({"owner_id": victim_id}, {"is_archived": True}, {"id": 123456}, {"persisted": False}):
        r = client.patch(f"/projects/{pid}", json=payload, headers=owner)
        assert r.status_code == 422, f"{payload} -> {r.status_code}: {r.text}"
    # Ownership is unchanged.
    me = client.get("/auth/me", headers=owner).json()
    assert client.get(f"/projects/{pid}", headers=owner).json()["owner_id"] == me["id"]


# --- archive / unarchive ----------------------------------------------------
def test_archive_hides_from_default_list_and_unarchive_restores():
    headers = _auth("arch")
    pid = _create(headers, name="ToArchive")["id"]

    # Visible by default.
    ids = [p["id"] for p in client.get("/projects/", headers=headers).json()]
    assert pid in ids

    a = client.post(f"/projects/{pid}/archive", headers=headers)
    assert a.status_code == 200, a.text
    assert a.json()["is_archived"] is True
    assert _audit_count("project.archive", pid) >= 1

    # Excluded from the default list.
    default_ids = [p["id"] for p in client.get("/projects/", headers=headers).json()]
    assert pid not in default_ids
    # Shown when explicitly requested.
    incl_ids = [p["id"] for p in client.get("/projects/?include_archived=true", headers=headers).json()]
    assert pid in incl_ids

    u = client.post(f"/projects/{pid}/unarchive", headers=headers)
    assert u.status_code == 200, u.text
    assert u.json()["is_archived"] is False
    assert _audit_count("project.unarchive", pid) >= 1
    restored_ids = [p["id"] for p in client.get("/projects/", headers=headers).json()]
    assert pid in restored_ids


def test_non_owner_cannot_archive_403():
    owner = _auth("arch_o")
    other = _auth("arch_x")
    pid = _create(owner)["id"]
    assert client.post(f"/projects/{pid}/archive", headers=other).status_code == 403


def test_admin_can_archive_any_project():
    owner = _auth("arch_ownadm")
    admin = _admin_auth("arch_admin")
    pid = _create(owner)["id"]
    r = client.post(f"/projects/{pid}/archive", headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["is_archived"] is True


def test_archive_unknown_id_404():
    headers = _auth("arch_404")
    assert client.post("/projects/99999999/archive", headers=headers).status_code == 404


# --- soft delete ------------------------------------------------------------
def test_delete_is_soft_and_preserves_dependent_studies():
    headers = _auth("del_owner")
    pid = _create(headers, name="ToDelete")["id"]

    # Attach a dependent feasibility study directly (must survive a soft delete).
    session = app_db.SessionLocal()
    try:
        study = models.FeasibilityStudy(project_id=pid, title="Study")
        session.add(study)
        session.commit()
        study_id = study.id
    finally:
        session.close()

    d = client.delete(f"/projects/{pid}", headers=headers)
    assert d.status_code == 200, d.text
    assert d.json()["is_archived"] is True

    # The project ROW still exists (soft delete), and the study is not orphaned.
    session = app_db.SessionLocal()
    try:
        assert session.get(models.Project, pid) is not None
        assert session.get(models.FeasibilityStudy, study_id) is not None
    finally:
        session.close()

    # Hidden from the default list, visible with include_archived.
    default_ids = [p["id"] for p in client.get("/projects/", headers=headers).json()]
    assert pid not in default_ids


def test_non_owner_cannot_delete_403():
    owner = _auth("del_o")
    other = _auth("del_x")
    pid = _create(owner)["id"]
    assert client.delete(f"/projects/{pid}", headers=other).status_code == 403


def test_delete_unknown_id_404():
    headers = _auth("del_404")
    assert client.delete("/projects/99999999", headers=headers).status_code == 404


# --- DB-backed persistence of archive state ---------------------------------
def test_archive_state_is_persisted_in_db():
    headers = _auth("persist")
    pid = _create(headers)["id"]
    client.post(f"/projects/{pid}/archive", headers=headers)
    session = app_db.SessionLocal()
    try:
        row = session.get(models.Project, pid)
        assert row is not None
        assert row.is_archived is True
        assert row.archived_at is not None
    finally:
        session.close()
