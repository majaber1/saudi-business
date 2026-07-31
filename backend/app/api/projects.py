"""
Projects API.

When DATABASE_URL is configured the router persists to PostgreSQL via
SQLAlchemy. When it is not (demo mode), it falls back to an in-memory store so
preview deployments stay functional — but /health and this module both report
persistence=False so nobody mistakes demo data for durable storage.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import DB_ENABLED, SessionLocal

router = APIRouter(prefix="/projects", tags=["projects"])

# In-memory fallback used only when DB_ENABLED is False.
_PROJECTS: dict[int, dict] = {}
_NEXT_ID = 1


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    investment: float = Field(..., gt=0)
    stage: str = Field(default="idea", description="idea | mvp | early_revenue | growth")


class ProjectOut(ProjectCreate):
    id: int
    created_at: datetime
    workflow_status: str = "created"
    persisted: bool = DB_ENABLED

    model_config = {"from_attributes": True}


def _db_session():
    """Yield a DB session (only reached when DB_ENABLED)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate):
    if DB_ENABLED:
        from app import models

        db = SessionLocal()
        try:
            obj = models.Project(
                name=data.name,
                industry=data.industry,
                investment=data.investment,
                stage=data.stage,
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return ProjectOut(
                id=obj.id,
                name=obj.name,
                industry=obj.industry,
                investment=obj.investment,
                stage=obj.stage,
                created_at=obj.created_at,
                workflow_status=obj.workflow_status,
                persisted=True,
            )
        finally:
            db.close()

    global _NEXT_ID
    project = {
        "id": _NEXT_ID,
        "created_at": datetime.utcnow(),
        "workflow_status": "created",
        **data.model_dump(),
    }
    _PROJECTS[_NEXT_ID] = project
    _NEXT_ID += 1
    return ProjectOut(**project, persisted=False)


@router.get("/", response_model=list[ProjectOut])
def list_projects():
    if DB_ENABLED:
        from app import models

        db = SessionLocal()
        try:
            rows = db.query(models.Project).order_by(models.Project.id).all()
            return [
                ProjectOut(
                    id=r.id,
                    name=r.name,
                    industry=r.industry,
                    investment=r.investment,
                    stage=r.stage,
                    created_at=r.created_at,
                    workflow_status=r.workflow_status,
                    persisted=True,
                )
                for r in rows
            ]
        finally:
            db.close()

    return [ProjectOut(**p, persisted=False) for p in _PROJECTS.values()]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int):
    if DB_ENABLED:
        from app import models

        db = SessionLocal()
        try:
            r = db.get(models.Project, project_id)
            if r is None:
                raise HTTPException(status_code=404, detail="Project not found")
            return ProjectOut(
                id=r.id,
                name=r.name,
                industry=r.industry,
                investment=r.investment,
                stage=r.stage,
                created_at=r.created_at,
                workflow_status=r.workflow_status,
                persisted=True,
            )
        finally:
            db.close()

    project = _PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**project, persisted=False)
