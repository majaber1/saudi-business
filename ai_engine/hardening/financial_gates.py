"""Deterministic financial trust gates.

Do NOT silently correct numbers. Surface validation codes that reduce decision confidence.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _assumption_map(assumptions: dict[str, Any] | Iterable[Any] | None) -> dict[str, Any]:
    if assumptions is None:
        return {}
    if isinstance(assumptions, dict):
        return {str(k): v for k, v in assumptions.items()}
    out: dict[str, Any] = {}
    for item in assumptions:
        if isinstance(item, dict):
            key = item.get("key") or item.get("id") or item.get("name")
            val = item.get("value", item.get("base"))
            if key:
                out[str(key)] = val
            continue
        key = getattr(item, "key", None) or getattr(item, "id", None)
        if key is None:
            continue
        val = getattr(item, "value", None)
        out[str(key)] = val if val is not None else getattr(item, "base", None)
    return out


def evaluate_financial_trust_gates(
    *,
    financial_results: dict[str, Any] | None,
    assumptions: dict[str, Any] | Iterable[Any] | None = None,
    archetype: str | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Return gate codes + messages. Never mutates inputs / never invents corrections."""
    fr = dict(financial_results or {})
    asmap = _assumption_map(assumptions)
    arch = (archetype or "").lower().strip()
    codes: list[str] = []
    messages: list[str] = []
    ar = language == "ar"

    npv = _as_float(fr.get("npv"))
    irr = fr.get("irr")
    irr_f = _as_float(irr) if not isinstance(irr, str) else None
    if isinstance(irr, str) and irr.lower() in {"null", "none", "n/a", ""}:
        irr_f = None
    payback = _as_float(fr.get("payback_months"))
    if payback is None and fr.get("payback_years") is not None:
        py = _as_float(fr.get("payback_years"))
        payback = py * 12.0 if py is not None else None

    irr_available = fr.get("irr_available")
    if irr_available is None:
        irr_available = irr_f is not None
    payback_available = fr.get("payback_available")
    if payback_available is None:
        payback_available = payback is not None

    # Currency consistency
    currencies: set[str] = set()
    for key in ("currency", "reporting_currency", "investment_currency"):
        cur = fr.get(key) or asmap.get(key)
        if cur:
            currencies.add(str(cur).upper())
    text_blob = " ".join(str(v) for v in list(fr.values())[:50])
    if "USD" in text_blob.upper() and ("SAR" in text_blob.upper() or "ريال" in text_blob):
        currencies.update({"USD", "SAR"})
    for k, v in asmap.items():
        if "currency" in str(k).lower() and v:
            currencies.add(str(v).upper())
    money_curs = {c for c in currencies if c in {"SAR", "USD", "EUR"}}
    if len(money_curs) > 1:
        codes.append("CURRENCY_VALIDATION_REQUIRED")
        messages.append(
            "Currency mismatch detected (e.g. SAR vs USD). Assumption requires validation — no silent conversion applied."
            if not ar
            else "تم رصد تعارض عملة (مثل ريال/دولار). الافتراض يحتاج تحققاً — لم يتم التحويل تلقائياً."
        )

    if npv is not None and npv > 0 and not irr_available:
        codes.append("FINANCIAL_INCONSISTENCY")
        messages.append(
            "NPV is positive but IRR cannot be calculated. Assumption / cash-flow profile requires validation."
            if not ar
            else "صافي القيمة الحالية موجب لكن لا يمكن حساب معدل العائد الداخلي. يلزم التحقق من الافتراضات / التدفقات."
        )

    if npv is not None and npv > 0 and not payback_available:
        codes.append("PAYBACK_VALIDATION_REQUIRED")
        messages.append(
            "Payback cannot be calculated while NPV is positive. Cash recovery requires validation."
            if not ar
            else "لا يمكن حساب فترة الاسترداد مع صافي قيمة حالية موجبة. يلزم التحقق من استرداد النقد."
        )

    avg_ticket = _as_float(asmap.get("avg_ticket")) or _as_float(asmap.get("average_ticket"))
    daily = _as_float(asmap.get("daily_covers")) or _as_float(asmap.get("daily_transactions"))
    seats = _as_float(asmap.get("seats_capacity")) or _as_float(asmap.get("seats"))
    if avg_ticket and daily and seats and seats > 0:
        turns = daily / seats
        if turns > 8:
            codes.append("REVENUE_CAPACITY_VALIDATION_REQUIRED")
            messages.append(
                f"Implied {turns:.1f} turns per seat/day looks extreme vs capacity. Assumption requires validation."
                if not ar
                else f"معدل {turns:.1f} دورة لكل مقعد يومياً يبدو مبالغاً فيه مقابل السعة. يلزم التحقق."
            )

    util = _as_float(asmap.get("utilization")) or _as_float(asmap.get("plant_utilization"))
    if util is not None:
        util_pct = util * 100 if util <= 1 else util
        if util_pct <= 0 or util_pct > 100:
            codes.append("UTILIZATION_VALIDATION_REQUIRED")
            messages.append(
                "Plant utilization is outside 0–100%. Assumption requires validation."
                if not ar
                else "نسبة تشغيل المصنع خارج النطاق 0–100%. يلزم التحقق من الافتراض."
            )
        elif util_pct < 15 and arch in {"industrial", "manufacturing", "fnb"}:
            # for industrial primarily; keep fnb out of this branch
            if arch in {"industrial", "manufacturing"}:
                codes.append("UTILIZATION_VALIDATION_REQUIRED")
                messages.append(
                    "Utilization is very low for a manufacturing case. Assumption requires validation."
                    if not ar
                    else "نسبة التشغيل منخفضة جداً لحالة تصنيع. يلزم التحقق من الافتراض."
                )

    capex = (
        _as_float(fr.get("capex"))
        or _as_float(asmap.get("capex_machinery"))
        or _as_float(asmap.get("initial_investment"))
    )
    selling = _as_float(asmap.get("selling_price")) or _as_float(asmap.get("unit_price"))
    if (
        arch in {"industrial", "manufacturing"}
        and capex is not None
        and selling is not None
        and capex > 0
        and selling > capex * 50
    ):
        codes.append("CAPEX_UNIT_ECONOMICS_VALIDATION_REQUIRED")
        messages.append(
            "Unit selling price is extreme relative to machinery CAPEX. Assumption requires validation."
            if not ar
            else "سعر بيع الوحدة مبالغ فيه مقارنة بنفقات الآلات الرأسمالية. يلزم التحقق."
        )

    if arch in {"saas_digital", "saas"}:
        cac = _as_float(asmap.get("cac"))
        churn = _as_float(asmap.get("churn")) or _as_float(asmap.get("monthly_churn"))
        pricing = _as_float(asmap.get("pricing")) or _as_float(asmap.get("subscription_price"))
        if churn is not None:
            churn_pct = churn * 100 if churn <= 1 else churn
            if churn_pct < 0 or churn_pct > 40:
                codes.append("CHURN_VALIDATION_REQUIRED")
                messages.append(
                    "Monthly churn assumption looks extreme. Assumption requires validation."
                    if not ar
                    else "افتراض التسرب الشهري يبدو متطرفاً. يلزم التحقق."
                )
        if cac is not None and pricing is not None and pricing > 0 and cac > pricing * 36:
            codes.append("CAC_VALIDATION_REQUIRED")
            messages.append(
                "CAC is very high vs subscription price. Assumption requires validation."
                if not ar
                else "تكلفة اكتساب العميل مرتفعة جداً مقابل سعر الاشتراك. يلزم التحقق."
            )

    food_cost = _as_float(asmap.get("food_cost_pct")) or _as_float(asmap.get("cogs_pct"))
    if food_cost is not None:
        fc = food_cost * 100 if food_cost <= 1 else food_cost
        if fc < 5 or fc > 85:
            codes.append("MARGIN_VALIDATION_REQUIRED")
            messages.append(
                "Food/COGS percentage looks extreme. Assumption requires validation."
                if not ar
                else "نسبة تكلفة البضاعة / الطعام تبدو متطرفة. يلزم التحقق."
            )

    unique_codes = sorted(set(codes))
    confidence_penalty = min(0.55, 0.12 * len(unique_codes))
    return {
        "status": "PASS" if not unique_codes else "FAIL",
        "codes": unique_codes,
        "messages": messages,
        "confidence_penalty": confidence_penalty,
        "requires_validation": bool(unique_codes),
        "silent_correction_applied": False,
    }
