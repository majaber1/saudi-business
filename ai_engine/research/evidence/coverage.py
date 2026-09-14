"""Numeric evidence coverage validation and gap targeting."""
from __future__ import annotations

from typing import Any

# Material operating-economics keys for commercially useful studies.
MATERIAL_NUMERIC_KEYS: tuple[str, ...] = (
    "avg_ticket",
    "daily_covers",
    "rent_monthly",
    "labor_monthly",
    "food_cost_pct",
    "equipment_capex",
    "fitout_capex",
    "other_capex",
    "working_capital",
)


def _is_numeric_filled(value: Any) -> bool:
    if value is None:
        return False
    s = str(value).strip().upper()
    if not s or s in {"UNKNOWN", "NONE", "NULL", "N/A", "NA"}:
        return False
    try:
        float(s.replace(",", "").replace("%", ""))
        return True
    except ValueError:
        return False


def coverage_gaps(
    *,
    assumptions: list[Any] | None = None,
    estimate_keys: list[str] | None = None,
    required_keys: list[str] | None = None,
) -> list[str]:
    """Return material keys still missing numeric evidence-backed values."""
    required = list(required_keys or MATERIAL_NUMERIC_KEYS)
    filled: set[str] = set(estimate_keys or [])
    for a in assumptions or []:
        if isinstance(a, dict):
            key = str(a.get("key") or "")
            val = a.get("value")
            prov = str(a.get("provenance_class") or "")
        else:
            key = str(getattr(a, "key", "") or "")
            val = getattr(a, "value", None)
            prov = str(getattr(a, "provenance_class", "") or "")
        if key and _is_numeric_filled(val) and prov in {
            "SYSTEM_ESTIMATE",
            "VERIFIED_FACT",
            "USER_PROVIDED",
            "USER_ASSUMPTION",
            "EVIDENCE_BACKED",
        }:
            filled.add(key)
        elif key and _is_numeric_filled(val) and prov not in {"UNKNOWN", ""}:
            filled.add(key)
    return [k for k in required if k not in filled]


def validate_numeric_coverage(
    *,
    assumptions: list[Any] | None = None,
    estimate_keys: list[str] | None = None,
    required_keys: list[str] | None = None,
) -> dict[str, Any]:
    required = list(required_keys or MATERIAL_NUMERIC_KEYS)
    gaps = coverage_gaps(
        assumptions=assumptions,
        estimate_keys=estimate_keys,
        required_keys=required,
    )
    present = [k for k in required if k not in gaps]
    ratio = (len(present) / len(required)) if required else 0.0
    status = "PASS" if not gaps else ("PARTIAL" if present else "FAIL")
    return {
        "status": status,
        "required": required,
        "present": present,
        "gaps": gaps,
        "coverage_ratio": round(ratio, 3),
        "commercially_useful": set(present) >= {
            "avg_ticket",
            "rent_monthly",
            "labor_monthly",
            "equipment_capex",
        }
        and "daily_covers" in present,
    }
