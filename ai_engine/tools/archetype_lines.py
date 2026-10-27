"""Explicit line-item projections for specialty coffee and Saudi SaaS.

Missing amounts stay missing. Estimated amounts stay estimated. Neither is
turned into a sourced fact or an investment-ready recommendation.
"""
from __future__ import annotations

from typing import Any

from ai_engine.tools.calculator import calculate_irr, calculate_npv

COFFEE_ARCHETYPES = {"fnb"}
SAAS_ARCHETYPES = {"saas_digital"}
CALCULATION_VERSION = "archetype_lines.v1"
CASH_FLOW_BASIS = "PRE_TAX_OPERATING_PROJECTION"


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("SAR", "").replace("ريال", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _verification(row: dict[str, Any]) -> str:
    if row.get("ai_estimated") or row.get("origin") in {"ai_estimated", "default", "rule_fallback"}:
        return "ESTIMATED"
    return "OWNER_SUPPLIED"


def _ratio(row: dict[str, Any] | None) -> tuple[float | None, str | None]:
    """Return (ratio, error). A bare number above 1 is not divided by 100."""
    if row is None:
        return None, None
    raw = row.get("value")
    if isinstance(raw, str) and raw.strip().endswith("%"):
        number = _number(raw.strip()[:-1])
        if number is None or number < 0 or number > 100:
            return None, "invalid_percent"
        return number / 100.0, None
    number = _number(raw)
    if number is None:
        return None, "invalid_number"
    label = row.get("rate_representation")
    if label == "PERCENT":
        if number < 0 or number > 100:
            return None, "invalid_percent"
        return number / 100.0, None
    if label == "RATIO":
        if number < 0 or number > 1:
            return None, "invalid_ratio"
        return number, None
    if 0 <= number <= 1:
        return number, None
    return None, "ambiguous_rate"


def _line(line_id: str, monthly: float | None, status: str, lineage: list[dict[str, Any]], months: int) -> dict[str, Any]:
    annual = None if monthly is None else round(monthly * months, 2)
    return {
        "id": line_id,
        "monthly": None if monthly is None else round(monthly, 2),
        "annual": annual,
        "status": status,
        "lineage": lineage,
    }


def _lookup(rows: dict[str, dict[str, Any]], *keys: str) -> tuple[str | None, dict[str, Any] | None]:
    for key in keys:
        if key in rows and rows[key].get("value") not in (None, ""):
            return key, rows[key]
    return None, None


def _money_line(rows: dict[str, dict[str, Any]], line_id: str, *keys: str) -> dict[str, Any]:
    key, row = _lookup(rows, *keys)
    if row is None:
        return _line(line_id, None, "MISSING", [], 0)
    amount = _number(row.get("value"))
    if amount is None:
        return _line(line_id, None, "AMBIGUOUS", [{"key": key, "value": row.get("value"), "verification": "AMBIGUOUS"}], 0)
    return _line(
        line_id,
        amount,
        _verification(row),
        [{"key": key, "value": amount, "verification": _verification(row)}],
        0,
    )


def _with_months(line: dict[str, Any], months: int) -> dict[str, Any]:
    monthly = line["monthly"]
    line["annual"] = None if monthly is None else round(monthly * months, 2)
    return line


def _coffee_lines(rows: dict[str, dict[str, Any]], months: int) -> list[dict[str, Any]]:
    revenue_key, revenue_row = _lookup(rows, "coffee_revenue_monthly", "revenue_monthly")
    if revenue_row is not None:
        revenue = _money_line(rows, "revenue", revenue_key or "revenue_monthly")
    else:
        ticket_key, ticket = _lookup(rows, "avg_ticket")
        covers_key, covers = _lookup(rows, "daily_covers")
        days_key, days = _lookup(rows, "operating_days_per_month")
        parts = ((ticket_key, ticket), (covers_key, covers), (days_key, days))
        if any(part[1] is None for part in parts):
            revenue = _line("revenue", None, "MISSING", [], months)
        else:
            values = [_number(part[1].get("value")) for part in parts]
            if any(value is None for value in values):
                revenue = _line("revenue", None, "AMBIGUOUS", [], months)
            else:
                monthly = values[0] * values[1] * values[2]
                status = "ESTIMATED" if any(_verification(part[1]) == "ESTIMATED" for part in parts) else "OWNER_SUPPLIED"
                revenue = _line(
                    "revenue",
                    monthly,
                    status,
                    [
                        {"key": part[0], "value": _number(part[1].get("value")), "verification": _verification(part[1])}
                        for part in parts
                    ],
                    months,
                )
    rent = _with_months(_money_line(rows, "rent", "rent_monthly"), months)
    payroll = _with_months(_money_line(rows, "payroll", "labor_monthly", "payroll_monthly"), months)
    other_key, other_row = _lookup(rows, "other_operating_cost_monthly")
    food_key, food_row = _lookup(rows, "food_cost_pct")
    if other_row is not None and revenue["monthly"] is not None:
        other = _with_months(_money_line(rows, "operating_cost", other_key or "other_operating_cost_monthly"), months)
        ratio, error = _ratio(food_row) if food_row is not None else (None, None)
        if food_row is not None and error is None and ratio is not None:
            cogs = revenue["monthly"] * ratio
            status = "ESTIMATED" if other["status"] == "ESTIMATED" or _verification(food_row) == "ESTIMATED" else other["status"]
            operating = _line(
                "operating_cost",
                other["monthly"] + cogs,
                status,
                other["lineage"] + [{"key": food_key, "value": ratio, "verification": _verification(food_row)}],
                months,
            )
        elif food_row is not None and error is not None:
            operating = _line("operating_cost", None, "AMBIGUOUS", [{"key": food_key, "value": food_row.get("value"), "verification": "AMBIGUOUS"}], months)
        else:
            operating = other
    elif food_row is not None and revenue["monthly"] is not None:
        ratio, error = _ratio(food_row)
        if error is not None or ratio is None:
            operating = _line("operating_cost", None, "AMBIGUOUS", [{"key": food_key, "value": food_row.get("value"), "verification": "AMBIGUOUS"}], months)
        else:
            operating = _line(
                "operating_cost",
                revenue["monthly"] * ratio,
                "ESTIMATED" if _verification(food_row) == "ESTIMATED" or revenue["status"] == "ESTIMATED" else "OWNER_SUPPLIED",
                [{"key": food_key, "value": ratio, "verification": _verification(food_row)}],
                months,
            )
    elif other_row is not None:
        operating = _with_months(_money_line(rows, "operating_cost", "other_operating_cost_monthly"), months)
    else:
        operating = _line("operating_cost", None, "MISSING", [], months)
    revenue = _with_months(revenue, months)
    return [revenue, rent, payroll, operating]


def _saas_lines(rows: dict[str, dict[str, Any]], months: int) -> list[dict[str, Any]]:
    mrr_key, mrr_row = _lookup(rows, "mrr", "subscription_revenue_monthly")
    arr_key, arr_row = _lookup(rows, "arr")
    customers_key, customers = _lookup(rows, "target_customers")
    price_key, price = _lookup(rows, "pricing")
    if mrr_row is not None:
        revenue = _with_months(_money_line(rows, "subscription_revenue", mrr_key or "mrr"), months)
    elif arr_row is not None:
        amount = _number(arr_row.get("value"))
        if amount is None:
            revenue = _line("subscription_revenue", None, "AMBIGUOUS", [], months)
        else:
            revenue = _line(
                "subscription_revenue",
                amount / 12.0,
                _verification(arr_row),
                [{"key": arr_key, "value": amount, "verification": _verification(arr_row)}],
                months,
            )
    elif customers is not None and price is not None:
        count = _number(customers.get("value"))
        fee = _number(price.get("value"))
        if count is None or fee is None:
            revenue = _line("subscription_revenue", None, "AMBIGUOUS", [], months)
        else:
            status = "ESTIMATED" if _verification(customers) == "ESTIMATED" or _verification(price) == "ESTIMATED" else "OWNER_SUPPLIED"
            revenue = _line(
                "subscription_revenue",
                count * fee,
                status,
                [
                    {"key": customers_key, "value": count, "verification": _verification(customers)},
                    {"key": price_key, "value": fee, "verification": _verification(price)},
                ],
                months,
            )
    else:
        revenue = _line("subscription_revenue", None, "MISSING", [], months)

    spend_key, spend = _lookup(rows, "acquisition_cost_monthly")
    new_key, new_customers = _lookup(rows, "new_customers_monthly")
    cac_key, cac = _lookup(rows, "cac")
    if spend is not None:
        acquisition = _with_months(_money_line(rows, "acquisition_cost", spend_key or "acquisition_cost_monthly"), months)
    elif new_customers is not None and cac is not None:
        additions = _number(new_customers.get("value"))
        cost = _number(cac.get("value"))
        if additions is None or cost is None:
            acquisition = _line("acquisition_cost", None, "AMBIGUOUS", [], months)
        else:
            status = "ESTIMATED" if _verification(new_customers) == "ESTIMATED" or _verification(cac) == "ESTIMATED" else "OWNER_SUPPLIED"
            acquisition = _line(
                "acquisition_cost",
                additions * cost,
                status,
                [
                    {"key": new_key, "value": additions, "verification": _verification(new_customers)},
                    {"key": cac_key, "value": cost, "verification": _verification(cac)},
                ],
                months,
            )
    else:
        acquisition = _line("acquisition_cost", None, "MISSING", [], months)
    hosting = _with_months(_money_line(rows, "hosting", "hosting_monthly"), months)
    return [revenue, acquisition, hosting]


def _capex(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _money_line(rows, "capex", "fitout_capex", "capex", "initial_investment")


def _discount(rows: dict[str, dict[str, Any]]) -> tuple[float | None, str]:
    _key, row = _lookup(rows, "discount_rate")
    if row is None:
        return None, "MISSING"
    ratio, error = _ratio(row)
    if error is not None or ratio is None:
        return None, "AMBIGUOUS"
    return ratio, _verification(row)


def project_archetype_lines(
    archetype: str,
    assumptions: dict[str, dict[str, Any]] | None,
    *,
    horizon_months: int = 12,
) -> dict[str, Any] | None:
    kind = (archetype or "").lower().strip()
    if kind in COFFEE_ARCHETYPES:
        family = "specialty_coffee"
    elif kind in SAAS_ARCHETYPES:
        family = "saudi_saas"
    else:
        return None
    if horizon_months < 1 or horizon_months > 60:
        horizon_months = 12
    rows = {str(key).lower(): dict(value) for key, value in (assumptions or {}).items()}
    lines = _coffee_lines(rows, horizon_months) if family == "specialty_coffee" else _saas_lines(rows, horizon_months)
    capex = _capex(rows)
    discount, discount_status = _discount(rows)
    material_statuses = [line["status"] for line in lines]
    blocked = any(status in {"MISSING", "AMBIGUOUS"} for status in material_statuses)
    estimated = any(status == "ESTIMATED" for status in material_statuses) or capex["status"] == "ESTIMATED" or discount_status == "ESTIMATED"
    monthlies = [line["monthly"] for line in lines]
    if blocked or any(amount is None for amount in monthlies):
        net_monthly = None
        monthly_cash_flows = None
        annual_cash_flows = None
    else:
        revenue = monthlies[0]
        costs = sum(monthlies[1:])
        net_monthly = round(revenue - costs, 2)
        monthly_cash_flows = [net_monthly for _ in range(horizon_months)]
        years = (horizon_months + 11) // 12
        annual_cash_flows = []
        for year in range(years):
            start = year * 12
            chunk = monthly_cash_flows[start:start + 12]
            annual_cash_flows.append(round(sum(chunk), 2))
    npv = None
    irr = None
    if (
        not blocked
        and not estimated
        and capex["status"] == "OWNER_SUPPLIED"
        and capex["monthly"] is not None
        and discount_status == "OWNER_SUPPLIED"
        and discount is not None
        and annual_cash_flows is not None
    ):
        series = [-float(capex["monthly"])] + annual_cash_flows
        npv = calculate_npv(series, discount)
        irr = calculate_irr(series)
    if blocked or capex["status"] in {"MISSING", "AMBIGUOUS"} or discount_status in {"MISSING", "AMBIGUOUS"}:
        verdict = "INSUFFICIENT_EVIDENCE"
        investment_grade = False
    elif estimated:
        verdict = "DEFER"
        investment_grade = False
    elif net_monthly is not None and net_monthly < 0:
        verdict = "NO_GO"
        investment_grade = False
    else:
        verdict = None
        investment_grade = True
    return {
        "archetype": kind,
        "model_family": family,
        "calculation_version": CALCULATION_VERSION,
        "cash_flow_basis": CASH_FLOW_BASIS,
        "tax_lines_included": False,
        "horizon_months": horizon_months,
        "lines": lines,
        "lineage": [item for line in lines for item in line["lineage"]],
        "capex": None if capex["monthly"] is None else capex["monthly"],
        "capex_status": capex["status"],
        "discount_rate": discount,
        "discount_rate_status": "EXPLICIT" if discount_status == "OWNER_SUPPLIED" else discount_status,
        "monthly_net": net_monthly,
        "monthly_cash_flows": monthly_cash_flows,
        "annual_cash_flows": annual_cash_flows,
        "npv": npv,
        "irr": irr,
        "investment_grade": investment_grade,
        "gate_status": "PASS" if investment_grade else "BLOCKED",
        "verdict_override": verdict,
        "cost_verification": "UNVERIFIED_ESTIMATE" if estimated and not blocked else ("MISSING" if blocked else "OWNER_SUPPLIED"),
        "analysis_complete": investment_grade,
        "summary_en": (
            "Pre-tax operating projection from explicit archetype lines. "
            "Missing or estimated lines are not investment-ready."
        ),
        "summary_ar": "إسقاط تشغيلي قبل الضريبة من بنود النموذج. البنود الناقصة أو التقديرية ليست بدرجة استثمارية.",
    }


def rows_from_mapping(values: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for key, raw in values.items():
        if isinstance(raw, dict):
            rows[str(key).lower()] = dict(raw)
            rows[str(key).lower()].setdefault("origin", "user")
        else:
            rows[str(key).lower()] = {"value": raw, "origin": "user", "ai_estimated": False}
    return rows


def project_driver_scenario(
    archetype: str,
    assumptions: dict[str, Any],
    overrides: dict[str, Any],
    *,
    horizon_months: int = 12,
) -> dict[str, Any]:
    if any(key in {"multiplier", "scenario_multiplier"} for key in overrides):
        return {
            "status": "REJECTED",
            "reason": "bare_multiplier_rejected",
            "investment_grade": False,
            "verdict_override": "INSUFFICIENT_EVIDENCE",
            "gate_status": "BLOCKED",
        }
    rows = rows_from_mapping(assumptions)
    for key, raw in overrides.items():
        rows[str(key).lower()] = {"value": raw, "origin": "user", "ai_estimated": False, "scenario_override": True}
    projected = project_archetype_lines(archetype, rows, horizon_months=horizon_months)
    if projected is None:
        return {"status": "REJECTED", "reason": "unsupported_archetype", "investment_grade": False}
    projected["scenario_overrides"] = sorted(str(key).lower() for key in overrides)
    return projected


def project_study_archetype(state: Any) -> dict[str, Any] | None:
    profile = getattr(state, "profile", None)
    archetype = str(getattr(profile, "archetype", "") or "")
    if archetype.lower() not in COFFEE_ARCHETYPES | SAAS_ARCHETYPES:
        return None
    rows: dict[str, dict[str, Any]] = {}
    for assumption in getattr(state, "assumptions", None) or []:
        key = str(getattr(assumption, "key", "") or "").lower()
        if not key:
            continue
        raw = getattr(assumption, "base", None)
        if raw in (None, ""):
            raw = getattr(assumption, "value", None)
        rows[key] = {
            "value": raw,
            "origin": getattr(assumption, "origin", "user"),
            "ai_estimated": bool(getattr(assumption, "ai_estimated", False)),
            "rate_representation": getattr(assumption, "rate_representation", None),
        }
    horizon = rows.get("horizon_months", {}).get("value")
    months = int(_number(horizon) or 12)
    return project_archetype_lines(archetype, rows, horizon_months=months)
