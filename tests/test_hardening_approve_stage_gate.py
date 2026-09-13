"""API choke-point coverage for Product Hardening (approve_stage critical keys)."""
from __future__ import annotations

from ai_engine.hardening import assumption_requirement_explanations


def _missing_critical(archetype: str, assumptions: list[dict]) -> list[str]:
    """Mirror of study_engine approve_stage critical-key gate."""
    req_meta = assumption_requirement_explanations(archetype, language="en")
    critical = set(req_meta.get("critical_keys") or [])
    present = {
        str(a.get("key"))
        for a in assumptions
        if a.get("key") and str(a.get("value") or "").strip()
    }
    return sorted(k for k in critical if k not in present)


def test_fnb_approve_blocked_when_critical_keys_missing():
    missing = _missing_critical(
        "fnb",
        [{"key": "business_model", "value": "specialty coffee"}],
    )
    assert "avg_ticket" in missing
    assert "daily_covers" in missing
    assert "rent_monthly" in missing


def test_fnb_approve_allowed_when_critical_keys_present():
    filled = [
        {"key": k, "value": "1"}
        for k in assumption_requirement_explanations("fnb")["critical_keys"]
    ]
    assert _missing_critical("fnb", filled) == []


def test_industrial_approve_requires_capacity_and_capex():
    missing = _missing_critical("industrial", [{"key": "workforce", "value": "12"}])
    assert "production_capacity" in missing
    assert "capex_machinery" in missing
