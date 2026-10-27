"""Deterministic investment-recommendation ceiling.

The language model may explain a result. It cannot issue GO or
GO_WITH_CONDITIONS when material costs are missing, estimated and
unconfirmed, or the discount rate is unit-ambiguous.
"""
from __future__ import annotations

FAVORABLE_VERDICTS = {"GO", "GO_WITH_CONDITIONS", "CONDITIONAL_GO"}

ESTIMATED_COST_NOTES = frozenset(
    {
        "services_opex_defaulted_from_55pct_cost_ratio",
        "opex_defaulted_from_45pct_of_revenue_missing_cost_inputs",
        "opex_defaulted_from_45pct_of_revenue_zero_cost_vector",
        "llm_costs_unconfirmed_estimate",
    }
)


def trust_override(financial_results: dict | None) -> str | None:
    results = financial_results or {}
    if results.get("discount_rate_status") == "AMBIGUOUS":
        return "INSUFFICIENT_EVIDENCE"
    notes = set(results.get("extract_notes") or [])
    if results.get("cost_verification") == "UNVERIFIED_ESTIMATE" or notes & ESTIMATED_COST_NOTES:
        return "DEFER"
    if results.get("investment_grade") is False and results.get("gate_status") == "BLOCKED":
        override = results.get("verdict_override")
        if override in {"DEFER", "INSUFFICIENT_EVIDENCE", "NO_GO"}:
            return override
        return "DEFER"
    return None


def apply_investment_trust(state):
    """Downgrade a favorable verdict. Leave NO_GO and DEFER in place."""
    results = dict(state.financial_results or {})
    override = trust_override(results)
    if override is None:
        return state
    if override == "INSUFFICIENT_EVIDENCE" or state.verdict in FAVORABLE_VERDICTS or not state.verdict:
        state.verdict = override
        note = (
            "Deterministic financial safety withheld an investment-ready recommendation. "
            f"Required outcome: {override}."
        )
        state.decision_rationale = f"{(state.decision_rationale or '').strip()} {note}".strip()
    results["investment_grade"] = False
    results["verdict_override"] = override
    state.financial_results = results
    return state
