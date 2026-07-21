from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["projects"])

# In-memory store for V1 (replace with a real DB session in production —
# see database/schema.sql for the intended Postgres schema).
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


@router.post("/", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate):
    global _NEXT_ID
    project = {
        "id": _NEXT_ID,
        "created_at": datetime.utcnow(),
        "workflow_status": "created",
        **data.model_dump(),
    }
    _PROJECTS[_NEXT_ID] = project
    _NEXT_ID += 1
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int):
    project = _PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/analyze")
def analyze_project(project_id: int):
    project = _PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["workflow_status"] = "analyzed"
    return {
        "project_id": project_id,
        "workflow": ["AI CEO", "Market Research", "Financial", "Risk", "Funding", "Document"],
        "note": "Agent orchestration is a workflow stub in V1 — see ai-engine/workflows/feasibility_flow.md. "
                "Use /financial/evaluate and /funding/match directly for real calculations.",
    }
