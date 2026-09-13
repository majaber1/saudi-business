"""Product Hardening Sprint — deterministic trust / decision-quality gates.

Owner Cases 1–5. No silent financial corrections. No Phase 9A benchmarks.
"""
from __future__ import annotations

from ai_engine.hardening import (
    apply_decision_safety,
    assumption_requirement_explanations,
    classify_business_archetype,
    evaluate_evidence_verdict_gates,
    evaluate_financial_trust_gates,
    missing_required_assumptions,
    required_assumptions_for,
    schema_archetype_for,
    sector_pack_for_archetype,
)
from ai_engine.archetypes.classifier import classify_archetype
from ai_engine.archetypes.schemas import get_assumption_schema


def test_case1_coffee_shop_is_fnb_not_consulting():
    text = "Specialty coffee shop in Riyadh, 40 seats, ~450k SAR fit-out"
    assert classify_business_archetype(text) == "fnb"
    assert classify_archetype(text) == "fnb"
    keys = {f["key"] for f in required_assumptions_for("fnb")}
    for required in ("avg_ticket", "daily_covers", "rent_monthly", "food_cost_pct", "seats_capacity"):
        assert required in keys
    for banned in ("consultants_headcount", "billing_rate", "utilization_rate", "cac", "churn"):
        assert banned not in keys


def test_case2_recycling_plant_is_industrial():
    text = "Jeddah plastic recycling plant, 3.5M SAR machinery, feedstock contracts"
    assert classify_business_archetype(text) == "industrial"
    keys = {f["key"] for f in required_assumptions_for("industrial")}
    for required in (
        "production_capacity",
        "utilization",
        "capex_machinery",
        "selling_price",
        "raw_material_cost",
    ):
        assert required in keys


def test_case3_accounting_saas_is_saas_digital():
    text = "SME accounting SaaS with ZATCA e-invoicing, subscription pricing, churn"
    assert classify_business_archetype(text) == "saas_digital"
    keys = {f["key"] for f in get_assumption_schema("saas_digital")}
    for required in ("pricing", "cac", "churn", "arr", "target_customers"):
        assert required in keys


def test_case4_financial_inconsistency_detected_not_silently_fixed():
    gate = evaluate_financial_trust_gates(
        financial_results={
            "npv": 250_000,
            "irr": None,
            "irr_available": False,
            "payback_months": None,
            "payback_available": False,
            "currency": "SAR",
        },
        assumptions={
            "currency": "USD",
            "avg_ticket": 25,
            "daily_covers": 500,
            "seats_capacity": 20,
        },
        archetype="fnb",
        language="en",
    )
    assert gate["silent_correction_applied"] is False
    codes = set(gate["codes"])
    assert "CURRENCY_VALIDATION_REQUIRED" in codes
    assert "FINANCIAL_INCONSISTENCY" in codes
    assert "PAYBACK_VALIDATION_REQUIRED" in codes
    assert gate.get("corrected_npv") is None
    assert gate.get("corrected_irr") is None


def test_case5_missing_evidence_blocks_strong_go():
    ev = evaluate_evidence_verdict_gates(archetype="fnb", claims=[], language="en")
    assert ev["status"] == "FAIL"
    assert "pricing" in ev["missing_themes"]
    assert ev["max_allowed_verdict"] in {
        "INSUFFICIENT_EVIDENCE",
        "GO_WITH_CONDITIONS",
        "DEFER",
    }

    fin = evaluate_financial_trust_gates(
        financial_results={
            "npv": 100_000,
            "irr": 0.2,
            "irr_available": True,
            "payback_months": 18,
        },
        assumptions={},
        archetype="fnb",
    )
    safe = apply_decision_safety(
        verdict="GO",
        rationale="Strong GO from model",
        conditions=[],
        confidence=0.9,
        financial_gate=fin,
        evidence_gate=ev,
        language="en",
    )
    assert safe["verdict"] != "GO"
    assert safe["downgraded"] is True
    assert safe["false_confidence_blocked"] is True


def test_assumption_requirement_banner_for_fnb():
    exp = assumption_requirement_explanations("fnb", language="en")
    assert exp["archetype"] == "fnb"
    assert exp["banner"]
    assert "avg_ticket" in exp["critical_keys"]
    assert "daily_covers" in exp["critical_keys"]


def test_sector_packs_fnb_manufacturing_saas_are_question_only():
    for arch, pack_id in (
        ("fnb", "fnb"),
        ("industrial", "manufacturing"),
        ("saas_digital", "saas"),
    ):
        pack = sector_pack_for_archetype(arch)
        assert pack is not None
        assert pack["id"] == pack_id
        blob = str(pack).lower()
        for banned in (
            "percentile",
            "competitor score",
            "industry average",
            "benchmark range",
        ):
            assert banned not in blob
        assert pack.get("critical_assumptions") or pack.get("required_research_areas")


def test_schema_archetype_mapping_and_missing_keys():
    assert schema_archetype_for("fnb") == "fnb"
    missing = missing_required_assumptions("fnb", present_keys=["avg_ticket"])
    assert "daily_covers" in missing
    assert "avg_ticket" not in missing


def test_apply_decision_safety_currency_and_inconsistency_downgrade():
    fin = {
        "codes": ["CURRENCY_VALIDATION_REQUIRED", "FINANCIAL_INCONSISTENCY"],
        "messages": ["currency mismatch", "npv without irr"],
        "confidence_penalty": 0.24,
    }
    ev = {
        "codes": [],
        "messages": [],
        "missing_themes": [],
        "max_allowed_verdict": "GO",
        "confidence_penalty": 0.0,
    }
    safe = apply_decision_safety(verdict="GO", financial_gate=fin, evidence_gate=ev)
    assert safe["verdict"] == "GO_WITH_CONDITIONS"
    assert safe["downgraded"] is True
