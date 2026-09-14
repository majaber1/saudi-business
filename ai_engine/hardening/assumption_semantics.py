"""Semantic types + validation for assumption estimates.

Prevents physically impossible / placeholder-class values (e.g. generic 10000)
from surviving into financial analysis. Prefer UNKNOWN over fake precision.
No Claude numbers. No Phase 9A benchmarks.
"""
from __future__ import annotations

from typing import Any, Optional

PROVENANCE_USER = "USER_PROVIDED"
PROVENANCE_EVIDENCE = "EVIDENCE_BACKED"
PROVENANCE_SYSTEM = "SYSTEM_ESTIMATE"
PROVENANCE_UNKNOWN = "UNKNOWN"

_PLACEHOLDER_SENTINELS = frozenset({"10000", "100000", "1000", "9999", "12345"})

SEMANTIC_TYPES: dict[str, str] = {
    "seats_capacity": "seat_count",
    "store_area_m2": "area_m2",
    "operating_hours_day": "hours_per_day",
    "operating_days_year": "days_per_year",
    "daily_covers": "transactions_per_day",
    "avg_ticket": "sar_per_transaction",
    "rent_monthly": "sar_per_month",
    "labor_monthly": "sar_per_month",
    "utilities_monthly": "sar_per_month",
    "marketing_monthly": "sar_per_month",
    "food_cost_pct": "percentage",
    "delivery_dependency": "categorical",
    "fitout_capex": "sar_capex",
    "equipment_capex": "sar_capex",
    "working_capital": "sar_working_capital",
    "owner_budget": "sar_budget",
    "business_model": "categorical",
    "location_city": "text_location",
}


def semantic_type_for_key(key: str, input_type: str | None = None) -> str:
    if key in SEMANTIC_TYPES:
        return SEMANTIC_TYPES[key]
    it = (input_type or "").lower()
    if it == "percent":
        return "percentage"
    if it == "currency":
        return "sar_amount"
    if it == "number":
        return "number"
    if it in {"single_select", "multi_select"}:
        return "categorical"
    return "text"


def _parse_numeric(raw: str) -> Optional[float]:
    if raw is None:
        return None
    cleaned = (
        str(raw)
        .replace(",", "")
        .replace("%", "")
        .replace("SAR", "")
        .replace("ر.س", "")
        .strip()
    )
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def is_placeholder_sentinel(value: Any, *, key: str = "", input_type: str | None = None) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    if s in _PLACEHOLDER_SENTINELS:
        return True
    sem = semantic_type_for_key(key, input_type)
    num = _parse_numeric(s)
    if num is None:
        return False
    if sem == "hours_per_day" and num >= 100:
        return True
    if sem == "seat_count" and num >= 5000:
        return True
    if sem == "transactions_per_day" and num >= 5000:
        return True
    if sem == "sar_per_transaction" and num >= 5000:
        return True
    if sem == "percentage" and (num < 0 or num > 100):
        return True
    return False


def validate_assumption_value(
    *,
    key: str,
    value: Any,
    input_type: str | None = None,
    unit: str | None = None,
) -> dict[str, Any]:
    _ = unit
    sem = semantic_type_for_key(key, input_type)
    raw = "" if value is None else str(value).strip()

    if not raw or raw.lower() in {"unknown", "n/a", "na", "none", "null", "tbd", "غير معروف"}:
        return {
            "ok": False,
            "value": None,
            "code": "UNKNOWN",
            "message": f"{key} is unknown / not provided",
            "semantic_type": sem,
        }

    if sem in {"categorical", "text_location", "text"}:
        if raw in _PLACEHOLDER_SENTINELS or _parse_numeric(raw) in {10000.0, 100000.0}:
            return {
                "ok": False,
                "value": None,
                "code": "PLACEHOLDER_REJECTED",
                "message": f"{key} rejected placeholder-class value",
                "semantic_type": sem,
            }
        return {"ok": True, "value": raw, "code": None, "message": None, "semantic_type": sem}

    num = _parse_numeric(raw)
    if num is None:
        return {
            "ok": False,
            "value": None,
            "code": "NON_NUMERIC",
            "message": f"{key} expects a number",
            "semantic_type": sem,
        }

    if is_placeholder_sentinel(raw, key=key, input_type=input_type):
        return {
            "ok": False,
            "value": None,
            "code": "PLACEHOLDER_REJECTED",
            "message": f"{key} rejected placeholder-class value {raw}",
            "semantic_type": sem,
        }

    if sem == "hours_per_day":
        if num <= 0 or num > 24:
            return {
                "ok": False,
                "value": None,
                "code": "HOURS_OUT_OF_RANGE",
                "message": "operating hours/day must be > 0 and <= 24",
                "semantic_type": sem,
            }
    elif sem == "days_per_year":
        if num <= 0 or num > 366:
            return {
                "ok": False,
                "value": None,
                "code": "DAYS_OUT_OF_RANGE",
                "message": "operating days/year must be > 0 and <= 366",
                "semantic_type": sem,
            }
    elif sem == "percentage":
        if num < 0 or num > 100:
            return {
                "ok": False,
                "value": None,
                "code": "PERCENT_OUT_OF_RANGE",
                "message": "percentage must be between 0 and 100",
                "semantic_type": sem,
            }
    elif sem == "seat_count":
        if num <= 0 or num != int(num) or num > 800:
            return {
                "ok": False,
                "value": None,
                "code": "SEATS_IMPLAUSIBLE",
                "message": "seat count must be a positive integer within F&B plausibility (<=800)",
                "semantic_type": sem,
            }
    elif sem == "area_m2":
        if num <= 0 or num > 5000:
            return {
                "ok": False,
                "value": None,
                "code": "AREA_IMPLAUSIBLE",
                "message": "store area_m2 must be positive and within plausibility (<=5000)",
                "semantic_type": sem,
            }
    elif sem == "transactions_per_day":
        if num <= 0 or num > 2000:
            return {
                "ok": False,
                "value": None,
                "code": "ORDERS_IMPLAUSIBLE",
                "message": "daily transactions must be positive and within F&B plausibility (<=2000)",
                "semantic_type": sem,
            }
    elif sem == "sar_per_transaction":
        if num <= 0 or num > 500:
            return {
                "ok": False,
                "value": None,
                "code": "TICKET_IMPLAUSIBLE",
                "message": "average ticket (SAR) must be positive and within F&B plausibility (<=500)",
                "semantic_type": sem,
            }
    elif sem in {"sar_per_month", "sar_capex", "sar_working_capital", "sar_budget", "sar_amount"}:
        if num < 0:
            return {
                "ok": False,
                "value": None,
                "code": "NEGATIVE_CURRENCY",
                "message": f"{key} currency amount cannot be negative",
                "semantic_type": sem,
            }
        if sem == "sar_per_month" and key == "rent_monthly" and num > 500_000:
            return {
                "ok": False,
                "value": None,
                "code": "RENT_IMPLAUSIBLE",
                "message": "monthly rent exceeds single-unit F&B plausibility guard",
                "semantic_type": sem,
            }
    elif sem == "number":
        if num < 0:
            return {
                "ok": False,
                "value": None,
                "code": "NEGATIVE_NUMBER",
                "message": f"{key} cannot be negative",
                "semantic_type": sem,
            }

    if sem in {"seat_count", "transactions_per_day", "days_per_year"} and num == int(num):
        out_val = str(int(num))
    else:
        out_val = str(num)
    return {"ok": True, "value": out_val, "code": None, "message": None, "semantic_type": sem}


def map_origin_to_provenance(origin: str | None, *, has_evidence_value: bool = False) -> str:
    o = (origin or "").lower()
    if o == "user":
        return PROVENANCE_USER
    if o == "document" or (o == "knowledge_reference" and has_evidence_value):
        return PROVENANCE_EVIDENCE
    if o in {"ai_estimated", "rule_fallback", "default", "knowledge_reference"}:
        return PROVENANCE_SYSTEM
    return PROVENANCE_UNKNOWN
