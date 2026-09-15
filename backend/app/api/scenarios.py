"""
Scenario Engine API: deterministic what-if scenarios built from explicit
assumption overrides on top of a study's current assumptions.

POST computes a scenario by taking the study's current active assumptions
(the same canonical keys used by app.services.financial_projection),
layering the caller's explicit overrides on top, and running them through
the exact same deterministic engine as
POST /feasibility/{id}/compute-from-assumptions. The study's
actual assumptions are never modified -- overrides exist only for the
scenario computation. The result is stored as an immutable snapshot
(financial_result_snapshot) alongside exactly which values (base assumption
or override) produced it (source_assumption_values) and which calculation
engine version computed it (calculation_version), so a scenario stays
interpretable even after the study's assumptions later change.

Phase 10 additions: Decision Simulator endpoints that return deltas,
decision impact, risk impact, and trust classification alongside the
financial snapshot.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, get_current_user
from app.services.study_access import owned_study_or_error
from app.services.financial_projection import (
    ALL_ASSUMPTION_KEYS,
    CALCULATION_VERSION,
    OPTIONAL_ASSUMPTION_DEFAULTS,
    missing_required_keys,
    project_cash_flows,
    soft_input_warnings,
)
from app.services.decision_engine import evaluate_decision

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "financial-engine"))
from calculator import evaluate_feasibility, sensitivity_analysis  # noqa: E402

router = APIRouter(prefix="/studies/{study_id}/scenarios", tags=["scenarios"])

SCENARIO_TYPES = ("CONSERVATIVE", "BASE", "OPTIMISTIC", "CUSTOM")

ARCHETYPE_VARIABLES: Dict[str, List[Dict[str, str]]] = {
    "saas_digital": [
        {"key": "revenue_year1", "en": "Subscription Revenue (Year 1)", "ar": "إيراد الاشتراكات (السنة الأولى)", "unit": "SAR"},
        {"key": "capex", "en": "Initial Investment (CAPEX)", "ar": "الاستثمار الأولي (CAPEX)", "unit": "SAR"},
        {"key": "opex_annual", "en": "Annual Operating Costs", "ar": "تكاليف التشغيل السنوية", "unit": "SAR"},
        {"key": "growth_rate", "en": "Annual Growth Rate", "ar": "معدل النمو السنوي", "unit": "%"},
        {"key": "discount_rate", "en": "Discount Rate", "ar": "معدل الخصم", "unit": "%"},
        {"key": "horizon_years", "en": "Projection Horizon", "ar": "أفق التحليل", "unit": "years"},
    ],
    "fnb": [
        {"key": "revenue_year1", "en": "Annual Revenue (Year 1)", "ar": "الإيراد السنوي (السنة الأولى)", "unit": "SAR"},
        {"key": "capex", "en": "Initial Investment (CAPEX)", "ar": "الاستثمار الأولي (CAPEX)", "unit": "SAR"},
        {"key": "opex_annual", "en": "Annual Operating Costs (Rent, Payroll, COGS)", "ar": "تكاليف التشغيل السنوية (إيجار، رواتب، تكلفة البضائع)", "unit": "SAR"},
        {"key": "growth_rate", "en": "Annual Growth Rate", "ar": "معدل النمو السنوي", "unit": "%"},
        {"key": "discount_rate", "en": "Discount Rate", "ar": "معدل الخصم", "unit": "%"},
        {"key": "horizon_years", "en": "Projection Horizon", "ar": "أفق التحليل", "unit": "years"},
    ],
    "retail": [
        {"key": "revenue_year1", "en": "Annual Revenue (Year 1)", "ar": "الإيراد السنوي (السنة الأولى)", "unit": "SAR"},
        {"key": "capex", "en": "Initial Investment (CAPEX)", "ar": "الاستثمار الأولي (CAPEX)", "unit": "SAR"},
        {"key": "opex_annual", "en": "Annual Operating Costs", "ar": "تكاليف التشغيل السنوية", "unit": "SAR"},
        {"key": "growth_rate", "en": "Annual Growth Rate", "ar": "معدل النمو السنوي", "unit": "%"},
        {"key": "discount_rate", "en": "Discount Rate", "ar": "معدل الخصم", "unit": "%"},
        {"key": "horizon_years", "en": "Projection Horizon", "ar": "أفق التحليل", "unit": "years"},
    ],
    "industrial": [
        {"key": "revenue_year1", "en": "Annual Revenue (Year 1)", "ar": "الإيراد السنوي (السنة الأولى)", "unit": "SAR"},
        {"key": "capex", "en": "Initial Investment (CAPEX)", "ar": "الاستثمار الأولي (CAPEX)", "unit": "SAR"},
        {"key": "opex_annual", "en": "Annual Operating Costs (Materials, Labor, Energy)", "ar": "تكاليف التشغيل السنوية (مواد، عمالة، طاقة)", "unit": "SAR"},
        {"key": "growth_rate", "en": "Annual Growth Rate", "ar": "معدل النمو السنوي", "unit": "%"},
        {"key": "discount_rate", "en": "Discount Rate", "ar": "معدل الخصم", "unit": "%"},
        {"key": "horizon_years", "en": "Projection Horizon", "ar": "أفق التحليل", "unit": "years"},
    ],
}
DEFAULT_VARIABLES = ARCHETYPE_VARIABLES["saas_digital"]


def _require_db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Scenarios require persistence (database not configured).")
    return SessionLocal()


class ScenarioCreate(BaseModel):
    scenario_type: str = Field(default="CUSTOM")
    scenario_name: Optional[str] = Field(default=None, max_length=200)
    assumption_overrides: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate(self):
        if self.scenario_type not in SCENARIO_TYPES:
            raise ValueError(f"scenario_type must be one of {SCENARIO_TYPES}")
        unknown = set(self.assumption_overrides) - set(ALL_ASSUMPTION_KEYS)
        if unknown:
            raise ValueError(f"Unknown assumption override keys: {sorted(unknown)}. Allowed: {ALL_ASSUMPTION_KEYS}")
        return self


class ScenarioOut(BaseModel):
    id: int
    study_id: int
    scenario_type: str
    scenario_name: str
    assumption_overrides: Dict[str, float]
    source_assumption_values: Dict[str, dict]
    financial_result_snapshot: dict
    calculation_version: str

    model_config = {"from_attributes": True}


def _base_assumption_values(db, models, study_id: int) -> dict[str, dict]:
    """Active StudyAssumption rows for the canonical keys, as {key: {id, version, value}}."""
    rows = (
        db.query(models.StudyAssumption)
        .filter(
            models.StudyAssumption.study_id == study_id,
            models.StudyAssumption.is_active.is_(True),
            models.StudyAssumption.key.in_(ALL_ASSUMPTION_KEYS),
        )
        .all()
    )
    return {row.key: {"id": row.id, "version": row.version, "value": row.value_number} for row in rows}


def _compute_scenario(values: dict[str, float]) -> dict:
    """Run deterministic financial engine on a set of assumption values."""
    investment, cash_flows, discount_rate = project_cash_flows(values)
    res = evaluate_feasibility(investment, cash_flows, discount_rate)
    sens = sensitivity_analysis(investment, cash_flows, discount_rate)
    annual_revenue = values.get("revenue_year1", 0)
    annual_opex = values.get("opex_annual", 0)
    return {
        "investment": investment,
        "annual_cash_flows": cash_flows,
        "discount_rate": discount_rate,
        "roi_percent": res.roi_percent,
        "npv": res.npv_value,
        "irr": res.irr_value,
        "payback_years": res.payback_years,
        "verdict": res.verdict,
        "sensitivity": sens,
        "annual_revenue": annual_revenue,
        "annual_opex": annual_opex,
        "operating_result": annual_revenue - annual_opex,
    }


def _compute_delta(baseline: dict, scenario: dict) -> dict:
    """Compute deltas between baseline and scenario financial results."""
    delta = {}
    for key in ("investment", "npv", "annual_revenue", "annual_opex", "operating_result"):
        bv = baseline.get(key, 0) or 0
        sv = scenario.get(key, 0) or 0
        delta[key] = {"baseline": bv, "scenario": sv, "absolute": sv - bv, "percent": ((sv - bv) / bv * 100) if bv != 0 else None}
    for key in ("roi_percent", "irr"):
        bv = baseline.get(key) or 0
        sv = scenario.get(key) or 0
        delta[key] = {"baseline": bv, "scenario": sv, "absolute": sv - bv}
    bpy = baseline.get("payback_years")
    spy = scenario.get("payback_years")
    delta["payback_years"] = {"baseline": bpy, "scenario": spy, "absolute": (spy - bpy) if bpy and spy else None}
    return delta


def _compute_risk_impact(baseline: dict, scenario: dict, overrides: dict) -> list[dict]:
    """Assess risk changes between baseline and scenario."""
    risks = []
    bv = baseline.get("verdict", "")
    sv = scenario.get("verdict", "")
    if bv != sv:
        risk_dir = "worsened" if sv in ("not_feasible", "borderline") and bv == "feasible" else "improved" if sv == "feasible" and bv != "feasible" else "changed"
        risks.append({"category": "feasibility_verdict", "direction": risk_dir, "baseline": bv, "scenario": sv})
    bnpv = baseline.get("npv", 0) or 0
    snpv = scenario.get("npv", 0) or 0
    if bnpv != 0 and abs(snpv - bnpv) / abs(bnpv) > 0.1:
        risks.append({"category": "npv_sensitivity", "direction": "worsened" if snpv < bnpv else "improved", "baseline": bnpv, "scenario": snpv, "change_pct": round((snpv - bnpv) / abs(bnpv) * 100, 1)})
    for key, label in [("revenue_year1", "revenue"), ("opex_annual", "operating_costs"), ("capex", "investment")]:
        if key in overrides:
            risks.append({"category": f"{label}_override", "direction": "scenario_assumption", "variable": key, "override_value": overrides[key]})
    return risks


def _compute_decision_impact(baseline_result: dict, scenario_result: dict, evidence_count: int) -> dict:
    """Compare deterministic decision gates between baseline and scenario."""
    baseline_decision = evaluate_decision(
        evidence_count=evidence_count,
        base_scenario={"financial_result_snapshot": baseline_result, "source_assumption_values": {}},
        conservative_scenario=None,
    )
    scenario_decision = evaluate_decision(
        evidence_count=evidence_count,
        base_scenario={"financial_result_snapshot": scenario_result, "source_assumption_values": {}},
        conservative_scenario=None,
    )
    changed_gates = []
    if baseline_decision["decision"] != scenario_decision["decision"]:
        changed_gates.append({"gate": "decision", "baseline": baseline_decision["decision"], "scenario": scenario_decision["decision"]})
    return {
        "baseline_decision": baseline_decision["decision"],
        "baseline_reason": baseline_decision["reason"],
        "scenario_decision": scenario_decision["decision"],
        "scenario_reason": scenario_decision["reason"],
        "changed": baseline_decision["decision"] != scenario_decision["decision"],
        "changed_gates": changed_gates,
        "scenario_conditions": scenario_decision.get("conditions", []),
        "scenario_risks": scenario_decision.get("key_risks", []),
    }


def _evidence_trust_summary(db, models, study_id: int) -> dict:
    """Summarize evidence trust classifications for a study."""
    evidence_rows = db.query(models.EvidenceItem).filter(models.EvidenceItem.study_id == study_id).all()
    counts: Dict[str, int] = {"VERIFIED_FACT": 0, "SYSTEM_ESTIMATE": 0, "USER_ASSUMPTION": 0, "UNKNOWN": 0}
    for row in evidence_rows:
        cls = getattr(row, "classification", "UNKNOWN") or "UNKNOWN"
        if cls in counts:
            counts[cls] += 1
        else:
            counts["UNKNOWN"] += 1
    total = sum(counts.values())
    verified_pct = (counts["VERIFIED_FACT"] / total * 100) if total > 0 else 0
    grade = "INVESTMENT_GRADE" if verified_pct >= 60 else "MODERATE_TRUST" if verified_pct >= 30 else "NOT_INVESTMENT_GRADE"
    return {"counts": counts, "total": total, "verified_pct": round(verified_pct, 1), "grade": grade, "note": "Evidence trust is determined by the study's recorded evidence, not by scenario overrides. Scenario assumptions do not change evidence quality."}


@router.post("/", response_model=ScenarioOut, status_code=201)
def create_scenario(study_id: int, data: ScenarioCreate, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        owned_study_or_error(db, models, study_id, user)

        base = _base_assumption_values(db, models, study_id)
        values = {key: entry["value"] for key, entry in base.items()}
        values.update(data.assumption_overrides)

        missing = missing_required_keys(values)
        if missing:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "missing_assumptions",
                    "message": "Record or override these before running a scenario: " + ", ".join(missing),
                    "missing": missing,
                },
            )

        snapshot = _compute_scenario(values)

        source_values = {
            key: (
                {"origin": "override", "value": values[key]}
                if key in data.assumption_overrides
                else {"origin": "assumption", "value": values[key], **base[key]}
            )
            for key in values
        }

        row = models.ScenarioRun(
            study_id=study_id,
            created_by=user.id,
            scenario_type=data.scenario_type,
            scenario_name=data.scenario_name or data.scenario_type.title(),
            assumption_overrides=data.assumption_overrides,
            source_assumption_values=source_values,
            financial_result_snapshot=snapshot,
            calculation_version=CALCULATION_VERSION,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


@router.get("/", response_model=List[ScenarioOut])
def list_scenarios(study_id: int, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        owned_study_or_error(db, models, study_id, user)
        rows = (
            db.query(models.ScenarioRun)
            .filter(models.ScenarioRun.study_id == study_id)
            .order_by(models.ScenarioRun.id.desc())
            .all()
        )
        return rows
    finally:
        db.close()


@router.get("/compare", response_model=Dict[str, Optional[ScenarioOut]])
def compare_scenarios(study_id: int, user: UserOut = Depends(get_current_user)):
    """The latest run per scenario_type, for a side-by-side comparison."""
    from app import models

    db = _require_db()
    try:
        owned_study_or_error(db, models, study_id, user)
        result: Dict[str, Optional[ScenarioOut]] = {}
        for scenario_type in SCENARIO_TYPES:
            row = (
                db.query(models.ScenarioRun)
                .filter(models.ScenarioRun.study_id == study_id, models.ScenarioRun.scenario_type == scenario_type)
                .order_by(models.ScenarioRun.id.desc())
                .first()
            )
            result[scenario_type] = row
        return result
    finally:
        db.close()


@router.post("/simulate", status_code=200)
def simulate_scenario(study_id: int, data: ScenarioCreate, user: UserOut = Depends(get_current_user)):
    """Full Decision Simulator: compute scenario with deltas, decision impact, risk impact, and trust."""
    from app import models

    db = _require_db()
    try:
        owned_study_or_error(db, models, study_id, user)
        base = _base_assumption_values(db, models, study_id)

        baseline_values = {key: entry["value"] for key, entry in base.items()}
        for key, default in OPTIONAL_ASSUMPTION_DEFAULTS.items():
            if key not in baseline_values:
                baseline_values[key] = default

        scenario_values = {**baseline_values}
        scenario_values.update(data.assumption_overrides)

        baseline_missing = missing_required_keys(baseline_values)
        scenario_missing = missing_required_keys(scenario_values)
        if scenario_missing:
            raise HTTPException(status_code=422, detail={"code": "missing_assumptions", "message": f"Missing: {', '.join(scenario_missing)}", "missing": scenario_missing})

        if baseline_missing:
            baseline_result: Dict[str, Any] = {"investment": 0, "npv": None, "irr": None, "roi_percent": None, "payback_years": None, "verdict": "not_feasible", "annual_revenue": 0, "annual_opex": 0, "operating_result": 0}
        else:
            baseline_result = _compute_scenario(baseline_values)

        scenario_result = _compute_scenario(scenario_values)
        delta = _compute_delta(baseline_result, scenario_result)

        evidence_count = db.query(models.EvidenceItem).filter(models.EvidenceItem.study_id == study_id).count()
        decision_impact = _compute_decision_impact(baseline_result, scenario_result, evidence_count)
        risk_impact = _compute_risk_impact(baseline_result, scenario_result, data.assumption_overrides)
        trust = _evidence_trust_summary(db, models, study_id)
        warnings = soft_input_warnings(scenario_values)

        source_values = {
            key: (
                {"origin": "SCENARIO_ASSUMPTION", "value": scenario_values[key]}
                if key in data.assumption_overrides
                else {"origin": "BASELINE", "value": scenario_values[key]}
            )
            for key in scenario_values
        }

        row = models.ScenarioRun(
            study_id=study_id,
            created_by=user.id,
            scenario_type=data.scenario_type,
            scenario_name=data.scenario_name or "Simulation",
            assumption_overrides=data.assumption_overrides,
            source_assumption_values=source_values,
            financial_result_snapshot=scenario_result,
            calculation_version=CALCULATION_VERSION,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return {
            "scenario": ScenarioOut.model_validate(row).model_dump(),
            "baseline": baseline_result,
            "delta": delta,
            "decision_impact": decision_impact,
            "risk_impact": risk_impact,
            "trust": trust,
            "warnings": warnings,
            "is_hypothetical": True,
        }
    finally:
        db.close()


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(study_id: int, scenario_id: int, user: UserOut = Depends(get_current_user)):
    from app import models

    db = _require_db()
    try:
        owned_study_or_error(db, models, study_id, user)
        row = db.query(models.ScenarioRun).filter(models.ScenarioRun.id == scenario_id, models.ScenarioRun.study_id == study_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Scenario not found.")
        return row
    finally:
        db.close()


@router.get("/variables/meta")
def get_scenario_variables(study_id: int, user: UserOut = Depends(get_current_user)):
    """Return archetype-aware variable metadata for the simulator UI."""
    from app import models

    db = _require_db()
    try:
        study_row = owned_study_or_error(db, models, study_id, user)
        feasibility = db.query(models.FeasibilityStudy).filter(models.FeasibilityStudy.id == study_row.id).first()
        project = db.query(models.Project).filter(models.Project.id == study_row.project_id).first()

        archetype = None
        if feasibility and feasibility.payload:
            profile = feasibility.payload.get("profile") or {}
            archetype = profile.get("archetype")
        if not archetype and project:
            archetype = getattr(project, "industry", None)

        archetype_key = None
        if archetype:
            normalized = archetype.lower().replace("-", "_").replace(" ", "_")
            for key in ARCHETYPE_VARIABLES:
                if key in normalized or normalized in key:
                    archetype_key = key
                    break

        variables = ARCHETYPE_VARIABLES.get(archetype_key or "", DEFAULT_VARIABLES)
        base = _base_assumption_values(db, models, study_id)
        current_values = {key: entry["value"] for key, entry in base.items()}
        for key, default in OPTIONAL_ASSUMPTION_DEFAULTS.items():
            if key not in current_values:
                current_values[key] = default

        return {
            "archetype": archetype,
            "archetype_key": archetype_key,
            "variables": variables,
            "current_values": current_values,
        }
    finally:
        db.close()
