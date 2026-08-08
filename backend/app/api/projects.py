"""
Projects API (owner-scoped full lifecycle).

When DATABASE_URL is configured the router persists to PostgreSQL via
SQLAlchemy. When it is not (demo mode), it falls back to an in-memory store so
preview deployments stay functional -- but /health and this module both report
persistence=False so nobody mistakes demo data for durable storage. Demo mode
enforces the SAME ownership and archive rules as the DB path; it is not faked.

Every endpoint requires authentication and enforces resource ownership on the
server: a user only ever sees or mutates their own projects, and an admin may
act on any project. Ownership is never trusted from the client, and owner_id /
id / archive flags can never be set through a request body.

Endpoints:
  POST   /                      create
  GET    /                      list (excludes archived unless include_archived)
  GET    /{id}                  read
  PATCH  /{id}                  update mutable fields
  POST   /{id}/archive          soft-archive (hide from default list)
  POST   /{id}/unarchive        restore
  DELETE /{id}                  SOFT delete == archive (dependent studies/
                                reports are never orphaned)
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.auth import UserOut, get_current_user
from app.db import DB_ENABLED, SessionLocal

router = APIRouter(prefix="/projects", tags=["projects"])


def _utc_now_naive() -> datetime:
    """UTC now for the existing timezone-naive database columns.

    Derive the value from an aware UTC clock while preserving compatibility
    with the current PostgreSQL/SQLite migration schema.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

# In-memory fallback used only when DB_ENABLED is False. Keyed by project id;
# each record carries its owner_id so demo mode enforces the same ownership rules.
_PROJECTS: dict[int, dict] = {}
_NEXT_ID = 1


class ProjectCreate(BaseModel):
    # NOTE: create intentionally does NOT forbid extra fields; a client-supplied
    # owner_id (or similar) is silently ignored -- the server always assigns the
    # authenticated caller as owner. ProjectUpdate below IS strict (extra=forbid).
    name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    investment: float = Field(..., gt=0)
    stage: str = Field(default="idea", max_length=30)


class ProjectUpdate(BaseModel):
    """Strict partial update. ``extra="forbid"`` blocks owner_id, id,
    is_archived, archived_at, workflow_status, persisted, organization_id and
    any other privilege/internal field from being changed via the body."""

    model_config = {"extra": "forbid"}

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    industry: Optional[str] = Field(default=None, min_length=1, max_length=100)
    investment: Optional[float] = Field(default=None, gt=0)
    stage: Optional[str] = Field(default=None, max_length=30)


class ProjectOut(ProjectCreate):
    id: int
    owner_id: Optional[int] = None
    created_at: datetime
    workflow_status: str = "created"
    is_archived: bool = False
    persisted: bool = DB_ENABLED

    model_config = {"from_attributes": True}


def _can_read(user: UserOut, owner_id: Optional[int]) -> bool:
    """Admins read anything; everyone else only their own resources."""
    return user.role_key == "admin" or owner_id == user.id


def _can_write(user: UserOut, owner_id: Optional[int]) -> bool:
    """Mutation is allowed for the owner or an admin (admin override)."""
    return user.role_key == "admin" or owner_id == user.id


def _audit(db, actor_id: Optional[int], action: str, entity_id: Optional[int]) -> None:
    """Best-effort audit row for a project mutation (DB mode only)."""
    from app import models

    db.add(models.AuditLog(actor_id=actor_id, action=action, entity="project",
                           entity_id=entity_id, meta={}))


def _row_out(r, persisted: bool) -> "ProjectOut":
    return ProjectOut(
        id=r.id,
        owner_id=r.owner_id,
        name=r.name,
        industry=r.industry,
        investment=r.investment,
        stage=r.stage,
        created_at=r.created_at,
        workflow_status=r.workflow_status,
        is_archived=bool(getattr(r, "is_archived", False)),
        persisted=persisted,
    )


def _demo_out(p: dict) -> "ProjectOut":
    data = {k: p[k] for k in ("id", "owner_id", "name", "industry", "investment",
                              "stage", "created_at", "workflow_status")}
    return ProjectOut(**data, is_archived=bool(p.get("is_archived", False)),
                      persisted=False)


@router.post("/", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, user: UserOut = Depends(get_current_user)):
    if DB_ENABLED:
        from app import models

        db = SessionLocal()
        try:
            obj = models.Project(
                name=data.name,
                industry=data.industry,
                investment=data.investment,
                stage=data.stage,
                owner_id=user.id,
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)
            _audit(db, user.id, "project.create", obj.id)
            db.commit()
            return _row_out(obj, True)
        finally:
            db.close()

    global _NEXT_ID
    project = {
        "id": _NEXT_ID,
        "owner_id": user.id,
        "created_at": _utc_now_naive(),
        "workflow_status": "created",
        "is_archived": False,
        **data.model_dump(),
    }
    _PROJECTS[_NEXT_ID] = project
    _NEXT_ID += 1
    return _demo_out(project)


@router.get("/", response_model=list[ProjectOut])
def list_projects(
    user: UserOut = Depends(get_current_user),
    include_archived: bool = Query(False, description="Include archived projects"),
):
    if DB_ENABLED:
        from app import models

        db = SessionLocal()
        try:
            q = db.query(models.Project)
            if user.role_key != "admin":
                q = q.filter(models.Project.owner_id == user.id)
            if not include_archived:
                q = q.filter(models.Project.is_archived.is_(False))
            rows = q.order_by(models.Project.id).all()
            return [_row_out(r, True) for r in rows]
        finally:
            db.close()

    return [
        _demo_out(p)
        for p in _PROJECTS.values()
        if _can_read(user, p.get("owner_id"))
        and (include_archived or not p.get("is_archived", False))
    ]


def _get_writable_demo(project_id: int, user: UserOut) -> dict:
    project = _PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not _can_write(user, project.get("owner_id")):
        raise HTTPException(status_code=403, detail="Not authorized for this project")
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, user: UserOut = Depends(get_current_user)):
    if DB_ENABLED:
        from app import models

        db = SessionLocal()
        try:
            r = db.get(models.Project, project_id)
            if r is None:
                raise HTTPException(status_code=404, detail="Project not found")
            if not _can_read(user, r.owner_id):
                raise HTTPException(status_code=403, detail="Not authorized for this project")
            return _row_out(r, True)
        finally:
            db.close()

    project = _PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not _can_read(user, project.get("owner_id")):
        raise HTTPException(status_code=403, detail="Not authorized for this project")
    return _demo_out(project)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, data: ProjectUpdate,
                   user: UserOut = Depends(get_current_user)):
    changes = data.model_dump(exclude_unset=True)
    if DB_ENABLED:
        from app import models

        db = SessionLocal()
        try:
            r = db.get(models.Project, project_id)
            if r is None:
                raise HTTPException(status_code=404, detail="Project not found")
            if not _can_write(user, r.owner_id):
                raise HTTPException(status_code=403, detail="Not authorized for this project")
            for field, value in changes.items():
                setattr(r, field, value)
            _audit(db, user.id, "project.update", r.id)
            db.commit()
            db.refresh(r)
            return _row_out(r, True)
        finally:
            db.close()

    project = _get_writable_demo(project_id, user)
    project.update(changes)
    return _demo_out(project)


def _set_archived_db(project_id: int, user: UserOut, archived: bool) -> "ProjectOut":
    from app import models

    db = SessionLocal()
    try:
        r = db.get(models.Project, project_id)
        if r is None:
            raise HTTPException(status_code=404, detail="Project not found")
        if not _can_write(user, r.owner_id):
            raise HTTPException(status_code=403, detail="Not authorized for this project")
        r.is_archived = archived
        r.archived_at = _utc_now_naive() if archived else None
        _audit(db, user.id, "project.archive" if archived else "project.unarchive", r.id)
        db.commit()
        db.refresh(r)
        return _row_out(r, True)
    finally:
        db.close()


@router.post("/{project_id}/archive", response_model=ProjectOut)
def archive_project(project_id: int, user: UserOut = Depends(get_current_user)):
    if DB_ENABLED:
        return _set_archived_db(project_id, user, True)
    project = _get_writable_demo(project_id, user)
    project["is_archived"] = True
    project["archived_at"] = _utc_now_naive()
    return _demo_out(project)


@router.post("/{project_id}/unarchive", response_model=ProjectOut)
def unarchive_project(project_id: int, user: UserOut = Depends(get_current_user)):
    if DB_ENABLED:
        return _set_archived_db(project_id, user, False)
    project = _get_writable_demo(project_id, user)
    project["is_archived"] = False
    project["archived_at"] = None
    return _demo_out(project)


@router.delete("/{project_id}", response_model=ProjectOut)
def delete_project(project_id: int, user: UserOut = Depends(get_current_user)):
    """SOFT delete: archives the project instead of hard-deleting so dependent
    feasibility studies and reports are never orphaned. Returns the archived
    project so clients can confirm the resulting state."""
    if DB_ENABLED:
        return _set_archived_db(project_id, user, True)
    project = _get_writable_demo(project_id, user)
    project["is_archived"] = True
    project["archived_at"] = _utc_now_naive()
    return _demo_out(project)
