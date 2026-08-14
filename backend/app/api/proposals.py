from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import UserOut, get_current_user
from app.db import DB_ENABLED, get_db
from app.models import Proposal

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ProposalCreate(BaseModel):
    title: str
    proposal_type: str = "commercial"
    locale: str = "ar"
    project_id: Optional[int] = None
    feasibility_study_id: Optional[int] = None
    payload: dict = {}


class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    payload: Optional[dict] = None
    version: Optional[str] = None


class ProposalOut(BaseModel):
    id: int
    owner_id: Optional[int]
    project_id: Optional[int]
    title: str
    proposal_type: str
    status: str
    locale: str
    payload: dict
    version: str
    feasibility_study_id: Optional[int]

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[ProposalOut])
def list_proposals(
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not DB_ENABLED:
        return []
    return db.query(Proposal).filter(Proposal.owner_id == user.id).all()


@router.post("/", response_model=ProposalOut, status_code=201)
def create_proposal(
    body: ProposalCreate,
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not DB_ENABLED:
        raise HTTPException(503, "Database unavailable")
    proposal = Proposal(
        owner_id=user.id,
        project_id=body.project_id,
        title=body.title,
        proposal_type=body.proposal_type,
        locale=body.locale,
        payload=body.payload,
        feasibility_study_id=body.feasibility_study_id,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("/{proposal_id}", response_model=ProposalOut)
def get_proposal(
    proposal_id: int,
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not DB_ENABLED:
        raise HTTPException(503, "Database unavailable")
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.owner_id != user.id:
        raise HTTPException(404, "Proposal not found")
    return proposal


@router.patch("/{proposal_id}", response_model=ProposalOut)
def update_proposal(
    proposal_id: int,
    body: ProposalUpdate,
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not DB_ENABLED:
        raise HTTPException(503, "Database unavailable")
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.owner_id != user.id:
        raise HTTPException(404, "Proposal not found")
    if body.title is not None:
        proposal.title = body.title
    if body.status is not None:
        proposal.status = body.status
    if body.payload is not None:
        merged = {**(proposal.payload or {}), **body.payload}
        proposal.payload = merged
    if body.version is not None:
        proposal.version = body.version
    db.commit()
    db.refresh(proposal)
    return proposal


@router.delete("/{proposal_id}", status_code=204)
def delete_proposal(
    proposal_id: int,
    user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not DB_ENABLED:
        raise HTTPException(503, "Database unavailable")
    proposal = db.get(Proposal, proposal_id)
    if not proposal or proposal.owner_id != user.id:
        raise HTTPException(404, "Proposal not found")
    db.delete(proposal)
    db.commit()
