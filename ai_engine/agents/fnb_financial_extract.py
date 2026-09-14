"""F&B / café deterministic financial extract (no Claude numbers)."""
from __future__ import annotations

from typing import Any


def extract_fnb_financials(
    *,
    vals: dict[str, float],
    assumptions: list[Any] | None = None,
) -> dict[str, Any] | None:
    """Derive café P&L + CAPEX + WC + budget gap from structured assumptions."""

    def exact(*keys: str) -> float | None:
        for k in keys:
            if k in vals:
                return vals[k]
        return None

    extract_notes: list[str] = []
    avg_ticket = exact("avg_ticket", "average_ticket", "ticket_size")
    daily = exact("daily_covers", "daily_transactions", "transactions_per_day")
    days = exact("operating_days_year", "operating_days") or 330.0
    food_pct = exact("food_cost_pct", "cogs_pct", "beverage_cost_pct")
    rent_m = exact("rent_monthly", "monthly_rent")
    labor_m = exact("labor_monthly", "monthly_labor")
    util_m = exact("utilities_monthly") or 0.0
    mkt_m = exact("marketing_monthly") or 0.0
    fitout = exact("fitout_capex", "fit_out_capex", "opening_capex") or 0.0
    equipment = exact("equipment_capex", "coffee_equipment_capex") or 0.0
    other_capex = exact("other_capex", "furniture_capex", "pos_capex") or 0.0
    wc = exact("working_capital", "opening_working_capital")
    owner_budget = exact("owner_budget", "available_budget", "budget")

    unknown_keys = []
    for a in assumptions or []:
        val = getattr(a, "value", None) if not isinstance(a, dict) else a.get("value")
        key = getattr(a, "key", None) if not isinstance(a, dict) else a.get("key")
        if key and str(val).strip().upper() == "UNKNOWN":
            unknown_keys.append(str(key))

    cogs_y1 = None
    if avg_ticket is None or daily is None or avg_ticket <= 0 or daily <= 0:
        extract_notes.append("fnb_revenue_blocked_missing_or_unknown_ticket_or_covers")
        annual_revenues = None
        annual_costs = None
    else:
        y1 = daily * avg_ticket * days
        annual_revenues = [y1, y1 * 1.08, y1 * 1.08 * 1.08]
        extract_notes.append("fnb_revenue_daily_covers_x_ticket_x_days")
        pct = (food_pct / 100.0) if food_pct is not None and food_pct > 1 else (food_pct if food_pct is not None else 0.32)
        if food_pct is None:
            extract_notes.append("fnb_cogs_defaulted_32pct_missing_food_cost")
            pct = 0.32
        cogs_y1 = annual_revenues[0] * pct
        fixed_annual = ((rent_m or 0.0) + (labor_m or 0.0) + util_m + mkt_m) * 12.0
        if rent_m is None:
            extract_notes.append("fnb_rent_missing")
        if labor_m is None:
            extract_notes.append("fnb_labor_missing")
        annual_costs = [
            cogs_y1 + fixed_annual,
            annual_revenues[1] * pct + fixed_annual * 1.03,
            annual_revenues[2] * pct + fixed_annual * 1.06,
        ]

    capex_components = {
        "equipment_capex": float(equipment),
        "fitout_capex": float(fitout),
        "other_capex": float(other_capex),
    }
    capex = float(equipment) + float(fitout) + float(other_capex)
    if capex <= 0:
        extract_notes.append("fnb_capex_missing_or_unknown")

    if wc is None:
        monthly_fixed = (rent_m or 0.0) + (labor_m or 0.0) + util_m + mkt_m
        monthly_cogs = (cogs_y1 / 12.0) if cogs_y1 else 0.0
        if monthly_fixed > 0 or monthly_cogs > 0:
            wc = 2.0 * (monthly_fixed + monthly_cogs)
            extract_notes.append("fnb_working_capital_estimated_2_months_opex")
        else:
            wc = 0.0
            extract_notes.append("fnb_working_capital_unknown")

    total_initial = float(capex) + float(wc or 0.0)
    budget_gap = None
    budget_status = "UNKNOWN_BUDGET"
    if owner_budget is not None:
        gap = total_initial - float(owner_budget)
        budget_gap = gap
        budget_status = "SHORTFALL" if gap > 0 else "SURPLUS"
        extract_notes.append(f"fnb_budget_{budget_status.lower()}")

    discount = exact("discount_rate") or 0.12
    if discount > 1:
        discount = discount / 100.0

    # Always return a structured F&B result (even when incomplete) so callers do not
    # fall through into services/mobility extractors for café studies.
    if capex <= 0 and annual_revenues is None and annual_costs is None:
        extract_notes.append("fnb_extract_incomplete_insufficient_numeric_inputs")

    return {
        "capex": float(capex),
        "annual_revenues": annual_revenues,
        "annual_costs": annual_costs,
        "discount_rate": discount,
        "extract_notes": extract_notes,
        "assumption_values": {
            k: vals[k]
            for k in (
                "avg_ticket",
                "daily_covers",
                "operating_days_year",
                "food_cost_pct",
                "rent_monthly",
                "labor_monthly",
                "fitout_capex",
                "equipment_capex",
                "working_capital",
                "owner_budget",
                "seats_capacity",
            )
            if k in vals
        },
        "capex_components": capex_components,
        "working_capital": float(wc or 0.0),
        "total_initial_funding": total_initial,
        "owner_budget": float(owner_budget) if owner_budget is not None else None,
        "budget_gap": budget_gap,
        "budget_status": budget_status,
        "currency": "SAR",
        "unknown_assumption_keys": unknown_keys,
        "gross_profit_y1": (annual_revenues[0] - (cogs_y1 or 0.0)) if annual_revenues else None,
        "cogs_y1": cogs_y1,
        "ebitda_y1": (
            (annual_revenues[0] - annual_costs[0]) if annual_revenues and annual_costs else None
        ),
        "incomplete": annual_revenues is None or annual_costs is None or capex <= 0,
    }
