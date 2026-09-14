"""P1-A: Evidence ↔ assumption numeric contradiction safety gates."""
from __future__ import annotations

from ai_engine.hardening import (
    apply_decision_safety,
    evaluate_evidence_verdict_gates,
    evaluate_numeric_evidence_assumption_consistency,
)


def _fnb_theme_claims():
    return [
        {"statement": "Competitor cafes price near 18 SAR ticket", "category": "pricing"},
        {"statement": "Several competing coffee shops nearby", "category": "competitors"},
        {"statement": "High footfall location in Riyadh district", "category": "location_economics"},
        {"statement": "Strong local demand for specialty coffee", "category": "demand"},
    ]


def test_p1a_transactions_day_vs_month_blocks_strong_go():
    claims = _fnb_theme_claims() + [
        {
            "statement": "Market evidence: 5,000 transactions per day at comparable cafes",
            "category": "demand",
        }
    ]
    assumptions = [
        {"key": "monthly_transactions", "value": 1000, "unit": "count"},
        {"key": "avg_ticket", "value": 22, "unit": "SAR"},
    ]
    numeric = evaluate_numeric_evidence_assumption_consistency(
        claims=claims, assumptions=assumptions, language="en"
    )
    assert numeric["status"] == "FAIL"
    assert "EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION" in numeric["codes"]
    assert numeric["findings"]
    finding = numeric["findings"][0]
    assert finding["evidence_value"] == 5000
    assert finding["evidence_period"] == "day"
    assert finding["assumption_value"] == 1000
    assert finding["assumption_period"] == "month"
    assert finding["normalized_period"] == "month"
    assert finding["ratio"] >= 3.0

    ev = evaluate_evidence_verdict_gates(
        archetype="fnb",
        claims=claims,
        assumptions=assumptions,
        language="en",
    )
    assert "EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION" in ev["codes"]
    assert ev["max_allowed_verdict"] != "GO"
    assert ev["numeric_contradictions"]

    safe = apply_decision_safety(
        verdict="GO",
        rationale="Looks profitable",
        confidence=0.95,
        evidence_gate=ev,
        financial_gate={"codes": [], "messages": [], "confidence_penalty": 0},
        language="en",
    )
    assert safe["verdict"] != "GO"
    assert safe["downgraded"] is True
    assert "EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION" in safe["gate_codes"]
    assert any("contradiction" in c.lower() or "5000" in c for c in safe["conditions"])


def test_p1a_compatible_transaction_volume_no_contradiction():
    claims = _fnb_theme_claims() + [
        {"statement": "Peer cafes see about 120 transactions per day", "category": "demand"},
    ]
    assumptions = [{"key": "daily_covers", "value": 110}]
    numeric = evaluate_numeric_evidence_assumption_consistency(
        claims=claims, assumptions=assumptions, language="en"
    )
    assert numeric["status"] == "PASS"
    assert numeric["findings"] == []
    ev = evaluate_evidence_verdict_gates(
        archetype="fnb", claims=claims, assumptions=assumptions, language="en"
    )
    assert "EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION" not in ev["codes"]
    safe = apply_decision_safety(
        verdict="GO",
        evidence_gate=ev,
        financial_gate={"codes": [], "messages": [], "confidence_penalty": 0},
    )
    assert safe["verdict"] == "GO"


def test_p1a_different_metrics_not_compared():
    claims = [
        {"statement": "Market size is about 5,000,000 SAR annually", "category": "demand"},
    ]
    assumptions = [{"key": "daily_covers", "value": 100}]
    numeric = evaluate_numeric_evidence_assumption_consistency(
        claims=claims, assumptions=assumptions, language="en"
    )
    assert numeric["findings"] == []


def test_p1a_incompatible_units_not_compared():
    # Ticket in USD must not be compared against SAR allowlisted ticket assumption via free text.
    claims = [{"statement": "Average ticket is 25 USD per order", "category": "pricing"}]
    assumptions = [{"key": "avg_ticket", "value": 25, "unit": "SAR", "currency": "SAR"}]
    numeric = evaluate_numeric_evidence_assumption_consistency(
        claims=claims, assumptions=assumptions, language="en"
    )
    # Free-text ticket extraction intentionally not compared across currency families.
    assert numeric["findings"] == []


def test_p1a_missing_numeric_value_safe():
    claims = [{"statement": "Transactions per day are unknown", "category": "demand"}]
    assumptions = [{"key": "daily_covers", "value": ""}]
    numeric = evaluate_numeric_evidence_assumption_consistency(
        claims=claims, assumptions=assumptions, language="en"
    )
    assert numeric["status"] == "PASS"
    assert numeric["findings"] == []


def test_p1a_theme_only_gates_unchanged_without_numeric_assumptions():
    claims = []
    ev = evaluate_evidence_verdict_gates(archetype="fnb", claims=claims, language="en")
    assert ev["status"] == "FAIL"
    assert "pricing" in ev["missing_themes"]
    assert "EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION" not in ev["codes"]

    claims_ok = _fnb_theme_claims()
    ev_ok = evaluate_evidence_verdict_gates(
        archetype="fnb", claims=claims_ok, assumptions=None, language="en"
    )
    assert ev_ok["missing_themes"] == []
    assert ev_ok["max_allowed_verdict"] == "GO"
