"""FastAPI Router for Wave 5 Launch Execution, Actuals & Reforecasting OS.

Endpoints for managing launch execution milestones, actual revenue/costs,
forecast vs actual variance tracking, and dynamic reforecasting.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import db, models
from app.api.auth import get_current_user
from app.services.launch import (
    get_or_create_launch_workspace,
    add_launch_milestone,
    update_launch_milestone,
    record_actual_period,
    evaluate_workspace_variances,
    generate_reforecast,
)

router = APIRouter(prefix="/api/v1/launch", tags=["Launch OS (Wave 5)"])


# Schemas
class MilestoneCreateIn(BaseModel):
    category: str = Field(..., description="REGULATORY, LOCATION, EQUIPMENT, TEAM, MARKETING, OPERATIONS")
    title: str = Field(..., min_length=3)
    description: Optional[str] = None
    due_date: Optional[str] = None
    budget_allocated: Optional[float] = None


class MilestoneUpdateIn(BaseModel):
    status: Optional[str] = None
    actual_cost: Optional[float] = None
    completed_date: Optional[str] = None


class ActualPeriodIn(BaseModel):
    period_label: str = Field(..., min_length=2, description="e.g. M01, 2026-M01")
    period_order: int = Field(..., ge=1)
    actual_revenue: float = Field(default=0.0, ge=0.0)
    transactions_count: Optional[int] = None
    average_ticket_size: Optional[float] = None
    actual_capex: float = Field(default=0.0, ge=0.0)
    actual_opex_salaries: float = Field(default=0.0, ge=0.0)
    actual_opex_rent: float = Field(default=0.0, ge=0.0)
    actual_opex_utilities: float = Field(default=0.0, ge=0.0)
    actual_opex_marketing: float = Field(default=0.0, ge=0.0)
    actual_opex_cogs: float = Field(default=0.0, ge=0.0)
    actual_opex_other: float = Field(default=0.0, ge=0.0)
    closing_cash_balance: Optional[float] = None
    notes: Optional[str] = None


class ReforecastIn(BaseModel):
    reforecast_title: str = Field(..., min_length=3)
    adjustment_rationale: str = Field(..., min_length=5)
    growth_rate_adjustment_pct: float = Field(default=0.0)
    opex_adjustment_pct: float = Field(default=0.0)


def _serialize_workspace(ws: models.LaunchWorkspace, db_session: Optional[Session] = None) -> Dict[str, Any]:
    variances = evaluate_workspace_variances(ws)

    gate_decision = "GO"
    gate_allowed = True
    gate_reason = "بوابة الإطلاق مفتوحة بناءً على قرار التحقق الميداني (GO)."
    if db_session:
        val_ws = db_session.query(models.ValidationWorkspace).filter_by(study_id=ws.study_id).first()
        if val_ws and val_ws.decisions:
            latest_dec = val_ws.decisions[0]
            gate_decision = latest_dec.decision
            gate_allowed = latest_dec.decision in ("GO", "GO_WITH_CONDITIONS")
            gate_reason = latest_dec.decision_reason or ("بوابة الإطلاق مفتوحة" if gate_allowed else "بوابة الإطلاق مقفلة")

    baseline_list = [
        {
            "id": s.id,
            "version": s.snapshot_version,
            "snapshot_version": s.snapshot_version,
            "is_frozen": True,
            "total_investment": s.total_investment,
            "monthly_projections": s.monthly_projections,
            "frozen_at": s.frozen_at.isoformat() if s.frozen_at else None,
            "notes": s.notes,
        }
        for s in ws.baseline_snapshots
    ]

    reforecast_list = [
        {
            "id": r.id,
            "version": f"v{r.version_number}",
            "version_number": r.version_number,
            "trigger_reason": r.reforecast_title or r.adjustment_rationale,
            "reforecast_title": r.reforecast_title,
            "adjustment_rationale": r.adjustment_rationale,
            "base_period_number": 1,
            "growth_rate_adjustment_pct": r.growth_rate_adjustment_pct,
            "revenue_growth_rate_adj": r.growth_rate_adjustment_pct,
            "cost_inflation_adj": r.opex_adjustment_pct,
            "opex_adjustment_pct": r.opex_adjustment_pct,
            "remaining_cash_balance": (r.reforecast_payload or {}).get("remaining_cash", 0.0),
            "monthly_burn_rate": r.monthly_burn_rate,
            "runway_months": r.remaining_runway_months,
            "remaining_runway_months": r.remaining_runway_months,
            "scenario_projections": (r.reforecast_payload or {}).get("projections", []),
            "reforecast_payload": r.reforecast_payload,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in ws.reforecasts
    ]

    return {
        "workspace": {
            "id": ws.id,
            "study_id": ws.study_id,
            "project_id": ws.project_id,
            "status": ws.status,
            "created_at": ws.created_at.isoformat() if ws.created_at else None,
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        },
        "id": ws.id,
        "study_id": ws.study_id,
        "project_id": ws.project_id,
        "status": ws.status,
        "decision_gate": {
            "decision": gate_decision,
            "is_allowed": gate_allowed,
            "reason": gate_reason,
        },
        "active_baseline": baseline_list[0] if baseline_list else None,
        "baseline_snapshots": baseline_list,
        "target_launch_date": ws.target_launch_date,
        "actual_launch_date": ws.actual_launch_date,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "variances_summary": variances,
        "variance_summary": variances,
        "milestones": [
            {
                "id": m.id,
                "category": m.category,
                "title": m.title,
                "description": m.description,
                "due_date": m.due_date,
                "completed_date": m.completed_date,
                "status": m.status,
                "budget_allocated": m.budget_allocated,
                "actual_cost": m.actual_cost,
            }
            for m in ws.milestones
        ],
        "actual_periods": [
            {
                "id": a.id,
                "period_number": a.period_order,
                "period_label": a.period_label,
                "period_order": a.period_order,
                "actual_revenue": a.actual_revenue,
                "actual_volume": a.transactions_count,
                "transactions_count": a.transactions_count,
                "average_ticket_size": a.average_ticket_size,
                "actual_capex": a.actual_capex,
                "actual_opex": a.total_actual_opex,
                "opex_breakdown": {
                    "salaries": a.actual_opex_salaries,
                    "rent": a.actual_opex_rent,
                    "utilities_gov": a.actual_opex_utilities,
                    "marketing": a.actual_opex_marketing,
                    "inventory": a.actual_opex_cogs,
                    "other": a.actual_opex_other,
                },
                "total_actual_opex": a.total_actual_opex,
                "net_cashflow": a.net_cashflow,
                "closing_cash_balance": a.closing_cash_balance,
                "variance_notes": a.notes,
                "notes": a.notes,
                "recorded_at": a.recorded_at.isoformat() if a.recorded_at else None,
            }
            for a in ws.actual_periods
        ],
        "latest_reforecast": reforecast_list[0] if reforecast_list else None,
        "reforecasts": reforecast_list,
    }


@router.get("/study/{study_id}", status_code=status.HTTP_200_OK)
@router.get("/workspaces/study/{study_id}", status_code=status.HTTP_200_OK)
def get_or_create_workspace(
    study_id: int,
    user: models.User = Depends(get_current_user),
    db_session: Session = Depends(db.get_db),
):
    """Fetches or initializes the launch execution workspace for a study."""
    try:
        ws = get_or_create_launch_workspace(db=db_session, user=user, study_id=study_id)
        return _serialize_workspace(ws, db_session=db_session)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/workspaces/{workspace_id}", status_code=status.HTTP_200_OK)
def get_workspace(
    workspace_id: int,
    user: models.User = Depends(get_current_user),
    db_session: Session = Depends(db.get_db),
):
    """Retrieves a launch workspace by its ID."""
    ws = db_session.query(models.LaunchWorkspace).filter_by(id=workspace_id).first()
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Launch workspace not found")
    if ws.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _serialize_workspace(ws)


@router.post("/workspaces/{workspace_id}/milestones", status_code=status.HTTP_201_CREATED)
def create_milestone(
    workspace_id: int,
    payload: MilestoneCreateIn,
    user: models.User = Depends(get_current_user),
    db_session: Session = Depends(db.get_db),
):
    """Adds a new milestone to the launch workspace."""
    try:
        m = add_launch_milestone(
            db=db_session,
            workspace_id=workspace_id,
            user=user,
            category=payload.category,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            budget_allocated=payload.budget_allocated,
        )
        return {
            "id": m.id,
            "category": m.category,
            "title": m.title,
            "description": m.description,
            "due_date": m.due_date,
            "completed_date": m.completed_date,
            "status": m.status,
            "budget_allocated": m.budget_allocated,
            "actual_cost": m.actual_cost,
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/milestones/{milestone_id}", status_code=status.HTTP_200_OK)
def update_milestone(
    milestone_id: int,
    payload: MilestoneUpdateIn,
    user: models.User = Depends(get_current_user),
    db_session: Session = Depends(db.get_db),
):
    """Updates status or cost of a launch milestone."""
    try:
        m = update_launch_milestone(
            db=db_session,
            milestone_id=milestone_id,
            user=user,
            status=payload.status,
            actual_cost=payload.actual_cost,
            completed_date=payload.completed_date,
        )
        return {
            "id": m.id,
            "category": m.category,
            "title": m.title,
            "description": m.description,
            "due_date": m.due_date,
            "completed_date": m.completed_date,
            "status": m.status,
            "budget_allocated": m.budget_allocated,
            "actual_cost": m.actual_cost,
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/workspaces/{workspace_id}/actuals", status_code=status.HTTP_201_CREATED)
def record_actuals(
    workspace_id: int,
    payload: ActualPeriodIn,
    user: models.User = Depends(get_current_user),
    db_session: Session = Depends(db.get_db),
):
    """Records operational actual revenue, capex, and opex for a period."""
    try:
        p = record_actual_period(
            db=db_session,
            workspace_id=workspace_id,
            user=user,
            period_label=payload.period_label,
            period_order=payload.period_order,
            actual_revenue=payload.actual_revenue,
            transactions_count=payload.transactions_count,
            average_ticket_size=payload.average_ticket_size,
            actual_capex=payload.actual_capex,
            actual_opex_salaries=payload.actual_opex_salaries,
            actual_opex_rent=payload.actual_opex_rent,
            actual_opex_utilities=payload.actual_opex_utilities,
            actual_opex_marketing=payload.actual_opex_marketing,
            actual_opex_cogs=payload.actual_opex_cogs,
            actual_opex_other=payload.actual_opex_other,
            closing_cash_balance=payload.closing_cash_balance,
            notes=payload.notes,
        )
        return {
            "id": p.id,
            "period_label": p.period_label,
            "period_order": p.period_order,
            "actual_revenue": p.actual_revenue,
            "transactions_count": p.transactions_count,
            "average_ticket_size": p.average_ticket_size,
            "actual_capex": p.actual_capex,
            "total_actual_opex": p.total_actual_opex,
            "net_cashflow": p.net_cashflow,
            "closing_cash_balance": p.closing_cash_balance,
            "notes": p.notes,
            "recorded_at": p.recorded_at.isoformat() if p.recorded_at else None,
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/workspaces/{workspace_id}/variances", status_code=status.HTTP_200_OK)
def get_variances(
    workspace_id: int,
    user: models.User = Depends(get_current_user),
    db_session: Session = Depends(db.get_db),
):
    """Retrieves full forecast vs actual variance analysis with alerts."""
    ws = db_session.query(models.LaunchWorkspace).filter_by(id=workspace_id).first()
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Launch workspace not found")
    if ws.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return evaluate_workspace_variances(ws)


@router.post("/workspaces/{workspace_id}/reforecast", status_code=status.HTTP_201_CREATED)
def create_reforecast(
    workspace_id: int,
    payload: ReforecastIn,
    user: models.User = Depends(get_current_user),
    db_session: Session = Depends(db.get_db),
):
    """Creates a new forward-looking reforecast scenario."""
    try:
        r = generate_reforecast(
            db=db_session,
            workspace_id=workspace_id,
            user=user,
            reforecast_title=payload.reforecast_title,
            adjustment_rationale=payload.adjustment_rationale,
            growth_rate_adjustment_pct=payload.growth_rate_adjustment_pct,
            opex_adjustment_pct=payload.opex_adjustment_pct,
        )
        return {
            "id": r.id,
            "version_number": r.version_number,
            "reforecast_title": r.reforecast_title,
            "adjustment_rationale": r.adjustment_rationale,
            "growth_rate_adjustment_pct": r.growth_rate_adjustment_pct,
            "opex_adjustment_pct": r.opex_adjustment_pct,
            "monthly_burn_rate": r.monthly_burn_rate,
            "remaining_runway_months": r.remaining_runway_months,
            "revised_break_even_month": r.revised_break_even_month,
            "reforecast_payload": r.reforecast_payload,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
