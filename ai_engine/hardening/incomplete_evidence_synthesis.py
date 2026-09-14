"""Investment-grade synthesis under incomplete evidence.

Distinguishes VERIFIED FACT / SYSTEM_ESTIMATE / USER_ASSUMPTION / UNKNOWN,
quantifies uncertainty, builds ranges/scenarios when possible, and produces a
commercially actionable recommendation without inventing magic numbers.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional


_CRITICAL_FN_KEYS = (
    "avg_ticket",
    "daily_covers",
    "rent_monthly",
    "labor_monthly",
    "food_cost_pct",
    "fitout_capex",
    "equipment_capex",
    "working_capital",
    "owner_budget",
)


def _prov(a: Any) -> str:
    if isinstance(a, dict):
        pc = a.get("provenance_class")
        origin = a.get("origin")
        val = a.get("value")
    else:
        pc = getattr(a, "provenance_class", None)
        origin = getattr(a, "origin", None)
        val = getattr(a, "value", None)
    if str(val or "").strip().upper() == "UNKNOWN" or not str(val or "").strip():
        return "UNKNOWN"
    if pc:
        p = str(pc).upper()
        if p in {"USER_PROVIDED", "USER_ASSUMPTION"}:
            return "USER_ASSUMPTION"
        if p in {"EVIDENCE_BACKED", "VERIFIED", "VERIFIED_FACT"}:
            return "VERIFIED_FACT"
        if p == "SYSTEM_ESTIMATE":
            return "SYSTEM_ESTIMATE"
        if p == "UNKNOWN":
            return "UNKNOWN"
    o = str(origin or "").lower()
    if o == "user":
        return "USER_ASSUMPTION"
    if o in {"document", "knowledge_reference"}:
        return "VERIFIED_FACT"
    if o in {"ai_estimated", "rule_fallback"}:
        return "SYSTEM_ESTIMATE"
    return "UNKNOWN"


def _entry(a: Any) -> dict[str, Any]:
    if isinstance(a, dict):
        return {
            "key": a.get("key"),
            "value": a.get("value"),
            "low": a.get("low"),
            "base": a.get("base") or a.get("value"),
            "high": a.get("high"),
            "provenance": _prov(a),
            "estimate_basis": a.get("estimate_basis"),
            "estimate_rationale": a.get("estimate_rationale") or a.get("source"),
            "source": a.get("source"),
        }
    return {
        "key": getattr(a, "key", None),
        "value": getattr(a, "value", None),
        "low": getattr(a, "low", None),
        "base": getattr(a, "base", None) or getattr(a, "value", None),
        "high": getattr(a, "high", None),
        "provenance": _prov(a),
        "estimate_basis": getattr(a, "estimate_basis", None),
        "estimate_rationale": getattr(a, "estimate_rationale", None)
        or getattr(a, "source", None),
        "source": getattr(a, "source", None),
    }


def _as_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").replace("%", "").split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def build_incomplete_evidence_synthesis(
    *,
    assumptions: Iterable[Any] | None,
    market_research: dict[str, Any] | None = None,
    financial_results: dict[str, Any] | None = None,
    claims: Iterable[Any] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Return investment-grade synthesis payload (safe under partial evidence)."""
    entries = [_entry(a) for a in (assumptions or [])]
    by_key = {str(e["key"]): e for e in entries if e.get("key")}

    classified = {
        "VERIFIED_FACT": [e for e in entries if e["provenance"] == "VERIFIED_FACT"],
        "SYSTEM_ESTIMATE": [e for e in entries if e["provenance"] == "SYSTEM_ESTIMATE"],
        "USER_ASSUMPTION": [e for e in entries if e["provenance"] == "USER_ASSUMPTION"],
        "UNKNOWN": [e for e in entries if e["provenance"] == "UNKNOWN"],
    }

    material_missing = []
    for key in _CRITICAL_FN_KEYS:
        e = by_key.get(key)
        if e is None or e["provenance"] == "UNKNOWN":
            material_missing.append(key)

    # Scenarios from ranges where available
    scenarios: dict[str, Any] = {"low": {}, "base": {}, "high": {}, "notes": []}
    for key, e in by_key.items():
        if e["provenance"] == "UNKNOWN":
            continue
        low = _as_float(e.get("low"))
        base = _as_float(e.get("base") or e.get("value"))
        high = _as_float(e.get("high"))
        if base is None:
            continue
        scenarios["base"][key] = base
        scenarios["low"][key] = low if low is not None else base * 0.85
        scenarios["high"][key] = high if high is not None else base * 1.15
        if low is None and high is None and e["provenance"] == "SYSTEM_ESTIMATE":
            scenarios["notes"].append(
                f"{key}: single-point SYSTEM_ESTIMATE; applied ±15% uncertainty band "
                f"(not primary evidence)."
            )
        elif low is not None or high is not None:
            scenarios["notes"].append(
                f"{key}: evidence-derived range low={low} base={base} high={high}."
            )

    mr = market_research or {}
    competitors = [
        c
        for c in (mr.get("competitors") or [])
        if isinstance(c, dict) and c.get("name") and c.get("status") != "NOT_FOUND"
    ]
    location = [
        loc
        for loc in (mr.get("location_economics") or [])
        if isinstance(loc, dict) and loc.get("status") != "NOT_FOUND"
    ]
    pricing = [
        p
        for p in (mr.get("pricing_signals") or [])
        if isinstance(p, dict) and p.get("status") not in {None, "NOT_FOUND"}
    ]

    fr = financial_results or {}
    revenue_blocked = any(
        str(fr.get(k) or 0) in {"0", "0.0", ""} or fr.get(k) in (0, 0.0, None)
        for k in ("revenue_y1", "revenue_year1", "total_revenue_y1")
    )
    # Also inspect nested
    if isinstance(fr.get("annual"), dict):
        revenue_blocked = revenue_blocked and not fr["annual"].get("revenue_y1")

    unknown_critical = len(material_missing)
    has_comp = len(competitors) > 0
    has_loc = len(location) > 0
    has_est = len(classified["SYSTEM_ESTIMATE"]) > 0
    has_user = len(classified["USER_ASSUMPTION"]) > 0

    # Commercial recommendation under uncertainty (never fake GO on empty ops)
    if not has_comp and not has_est and unknown_critical >= 4:
        rec_verdict = "INSUFFICIENT_EVIDENCE"
        usefulness = "PARTIAL"
    elif has_comp and has_loc and (has_est or has_user):
        # Competitors + location + at least some estimates/owner inputs:
        # commercially useful even when other fields remain UNKNOWN.
        rec_verdict = "GO_WITH_CONDITIONS" if unknown_critical <= 6 else "DEFER"
        usefulness = "PASS"
    elif has_comp and (has_loc or has_est):
        rec_verdict = "DEFER" if unknown_critical >= 3 else "GO_WITH_CONDITIONS"
        usefulness = "PASS" if unknown_critical <= 5 else "PARTIAL"
    elif has_comp or has_est:
        rec_verdict = "DEFER"
        usefulness = "PARTIAL"
    else:
        rec_verdict = "INSUFFICIENT_EVIDENCE"
        usefulness = "PARTIAL"

    ar = language == "ar"
    if ar:
        recommendation = (
            f"التوصية التجارية تحت عدم اليقين: {rec_verdict}. "
            f"المنافسون المصدّرون: {len(competitors)}؛ إشارات اقتصاد الموقع: {len(location)}؛ "
            f"تقديرات النظام: {len(classified['SYSTEM_ESTIMATE'])}؛ "
            f"قيم حرجة غير محلولة: {', '.join(material_missing) or 'لا يوجد'}. "
            "لا تُختلق أرقام؛ أكمل جمع إيجار/أجور/تذكرة/CAPEX بعروض أولية قبل الالتزام."
        )
        next_steps = [
            "تأكيد الإيجار بعروض حيّة للمنطقة المستهدفة",
            "جمع قوائم أسعار/تذاكر من 3–5 منافسين محليين",
            "طلب عروض تجهيز ومعدات ضمن ميزانية المالك",
            "إعادة تشغيل النموذج المالي بعد استبدال UNKNOWN بتقديرات موثقة",
        ]
    else:
        recommendation = (
            f"Commercial recommendation under uncertainty: {rec_verdict}. "
            f"Sourced competitors: {len(competitors)}; location-economy signals: {len(location)}; "
            f"SYSTEM_ESTIMATE fields: {len(classified['SYSTEM_ESTIMATE'])}; "
            f"material unresolved: {', '.join(material_missing) or 'none'}. "
            "Do not invent numbers — close rent/labor/ticket/CAPEX with primary quotes "
            "before capital commitment. Use low/base/high bands where estimates exist."
        )
        next_steps = [
            "Confirm district rent with live landlord/broker quotes",
            "Collect menu/ticket evidence from 3–5 local peers",
            "Obtain fit-out and equipment quotes within owner budget",
            "Re-run the financial model after replacing UNKNOWN with sourced estimates",
            "Stage investment: soft commitments only until critical UNKNOWN keys close",
        ]

    coverage = "PASS" if has_comp and has_loc and (has_est or has_user) else "PARTIAL"
    investment_grade = (
        "PASS"
        if coverage == "PASS"
        and usefulness == "PASS"
        and rec_verdict in {"GO_WITH_CONDITIONS", "DEFER", "GO", "NO_GO"}
        and has_comp
        and (has_loc or has_est)
        else "FAIL"
    )

    claim_count = 0
    for c in claims or []:
        claim_count += 1

    return {
        "provenance_breakdown": {
            k: [{"key": e["key"], "value": e["value"]} for e in v]
            for k, v in classified.items()
        },
        "material_missing_evidence": material_missing,
        "scenarios": scenarios,
        "market_coverage": {
            "competitors_sourced": len(competitors),
            "location_signals": len(location),
            "pricing_signals": len(pricing),
            "claim_count": claim_count,
        },
        "recommendation": {
            "verdict": rec_verdict,
            "summary": recommendation,
            "next_steps": next_steps,
            "commercially_actionable": rec_verdict
            in {"GO_WITH_CONDITIONS", "DEFER", "GO", "NO_GO"},
        },
        "parity_self_assessment": {
            "claude_level_coverage": coverage,
            "claude_level_decision_usefulness": usefulness,
            "investment_grade_study": investment_grade,
        },
        "uncertainty_notes": scenarios.get("notes") or [],
        "revenue_inputs_incomplete": bool(
            "avg_ticket" in material_missing or "daily_covers" in material_missing
        ),
    }
