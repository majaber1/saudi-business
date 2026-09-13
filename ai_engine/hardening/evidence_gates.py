"""Evidence → verdict gates (deterministic decision safety).

Never allow poor/missing critical evidence + strong GO.
"""
from __future__ import annotations

from typing import Any, Iterable

CRITICAL_EVIDENCE_THEMES: dict[str, tuple[str, ...]] = {
    "fnb": ("pricing", "competitors", "location_economics", "demand"),
    "retail": ("pricing", "competitors", "location_economics"),
    "industrial": ("capex", "supply_chain", "demand", "regulation"),
    "manufacturing": ("capex", "supply_chain", "demand", "regulation"),
    "saas_digital": ("pricing", "competitors", "acquisition", "retention"),
    "saas": ("pricing", "competitors", "acquisition", "retention"),
    "services": ("pricing", "competitors", "demand"),
    "marketplace": ("pricing", "competitors", "acquisition", "supply_chain"),
    "healthcare": ("pricing", "regulation", "demand", "location_economics"),
    "education": ("pricing", "demand", "location_economics"),
    "other": ("pricing", "demand"),
}

THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "pricing": ("price", "pricing", "ticket", "fee", "subscription", "سعر", "تسعير", "رسوم"),
    "competitors": ("competitor", "competition", "rival", "منافس", "منافسة"),
    "location_economics": ("rent", "location", "district", "footfall", "إيجار", "موقع", "حي"),
    "demand": ("demand", "market size", "customers", "covers", "طلب", "حجم السوق", "عملاء"),
    "capex": ("capex", "machinery", "equipment", "plant", "نفقات رأسمالية", "آلات", "معدات"),
    "supply_chain": ("supply", "feedstock", "raw material", "supplier", "سلسلة التوريد", "مواد خام"),
    "regulation": ("regulation", "license", "permit", "saso", "zatca", "ترخيص", "تنظيم", "هيئة"),
    "acquisition": ("cac", "acquisition", "marketing", "اكتساب", "تسويق"),
    "retention": ("churn", "retention", "ltv", "تسرب", "احتفاظ"),
}

_VERDICT_RANK = {
    "GO": 4,
    "GO_WITH_CONDITIONS": 3,
    "DEFER": 2,
    "NO_GO": 1,
    "INSUFFICIENT_EVIDENCE": 0,
}


def _claim_texts(claims: Iterable[Any] | None) -> list[str]:
    out: list[str] = []
    for c in claims or []:
        if isinstance(c, dict):
            out.append(str(c.get("statement") or c.get("text") or c.get("claim") or ""))
            out.append(str(c.get("category") or c.get("claim_type") or ""))
            out.append(str(c.get("source") or ""))
        else:
            out.append(str(getattr(c, "statement", "") or getattr(c, "text", "") or c))
    return [t.lower() for t in out if t]


def _theme_present(theme: str, texts: list[str]) -> bool:
    keys = THEME_KEYWORDS.get(theme, (theme,))
    blob = " | ".join(texts)
    return any(k.lower() in blob for k in keys)


def _norm_verdict(verdict: str | None) -> str:
    if not verdict:
        return "INSUFFICIENT_EVIDENCE"
    v = str(verdict).upper().strip().replace(" ", "_").replace("-", "_")
    aliases = {
        "GO_WITH_CONDITIONS": "GO_WITH_CONDITIONS",
        "CONDITIONAL_GO": "GO_WITH_CONDITIONS",
        "GO_WITH_CONDITION": "GO_WITH_CONDITIONS",
        "NOGO": "NO_GO",
        "NO_GO": "NO_GO",
    }
    return aliases.get(v, v)


def _rank(verdict: str | None) -> int:
    return _VERDICT_RANK.get(_norm_verdict(verdict), 0)


def evaluate_evidence_verdict_gates(
    *,
    archetype: str | None,
    claims: Iterable[Any] | None,
    research_quality: dict[str, Any] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    arch = (archetype or "other").lower().strip()
    required = CRITICAL_EVIDENCE_THEMES.get(arch, CRITICAL_EVIDENCE_THEMES["other"])
    texts = _claim_texts(claims)
    missing = [t for t in required if not _theme_present(t, texts)]

    rq = research_quality or {}
    low_quality = False
    summary = rq.get("summary") if isinstance(rq, dict) else None
    if isinstance(summary, dict):
        low = summary.get("low_quality") or summary.get("low_quality_count")
        try:
            low_quality = int(low or 0) >= 3
        except (TypeError, ValueError):
            low_quality = False

    codes: list[str] = []
    messages: list[str] = []
    ar = language == "ar"
    if missing:
        codes.append("INSUFFICIENT_EVIDENCE")
        miss = ", ".join(missing)
        messages.append(
            f"Critical evidence themes missing for this business type: {miss}. Strong GO is not allowed."
            if not ar
            else f"ثيمات أدلة حرجة ناقصة لهذا النوع من الأعمال: {miss}. لا يُسمح بتوصية GO قوية."
        )
    if low_quality:
        codes.append("EVIDENCE_QUALITY_WARNING")
        messages.append(
            "Research quality signals many low-quality claims. Decision confidence must be reduced."
            if not ar
            else "إشارات جودة البحث تظهر مطالبات منخفضة الجودة. يجب خفض ثقة القرار."
        )

    if len(missing) >= 2 or (missing and low_quality):
        max_verdict = "INSUFFICIENT_EVIDENCE"
    elif missing:
        max_verdict = "GO_WITH_CONDITIONS"
    else:
        max_verdict = "GO"

    confidence_penalty = min(0.6, 0.15 * len(missing) + (0.1 if low_quality else 0.0))
    return {
        "status": "PASS" if not missing else "FAIL",
        "codes": codes,
        "messages": messages,
        "missing_themes": missing,
        "required_themes": list(required),
        "max_allowed_verdict": max_verdict,
        "confidence_penalty": confidence_penalty,
    }


def apply_decision_safety(
    *,
    verdict: str | None,
    rationale: str | None = None,
    conditions: list[str] | None = None,
    confidence: float | None = None,
    financial_gate: dict[str, Any] | None = None,
    evidence_gate: dict[str, Any] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Downgrade unsafe verdicts. Never invent nicer numbers."""
    ar = language == "ar"
    original = _norm_verdict(verdict)
    current = original

    fin = financial_gate or {}
    ev = evidence_gate or {}
    warnings = list(fin.get("messages") or []) + list(ev.get("messages") or [])
    codes = list(fin.get("codes") or []) + list(ev.get("codes") or [])
    new_conditions = list(conditions or [])

    if "FINANCIAL_INCONSISTENCY" in codes or "CURRENCY_VALIDATION_REQUIRED" in codes:
        if _rank(current) >= _rank("GO"):
            current = "GO_WITH_CONDITIONS"
        new_conditions.append(
            "Resolve financial validation gates before full commitment."
            if not ar
            else "عالج بوابات التحقق المالي قبل الالتزام الكامل."
        )

    max_allowed = ev.get("max_allowed_verdict") or "GO"
    if _rank(current) > _rank(max_allowed):
        current = _norm_verdict(max_allowed)

    if ev.get("missing_themes") and current == "GO":
        current = (
            "GO_WITH_CONDITIONS"
            if len(ev.get("missing_themes") or []) == 1
            else "INSUFFICIENT_EVIDENCE"
        )

    if ev.get("missing_themes"):
        for theme in ev["missing_themes"]:
            new_conditions.append(
                f"Collect critical evidence: {theme}."
                if not ar
                else f"اجمع أدلة حرجة حول: {theme}."
            )

    base_conf = 0.7 if confidence is None else float(confidence)
    penalty = float(fin.get("confidence_penalty") or 0) + float(ev.get("confidence_penalty") or 0)
    adj_conf = max(0.05, min(0.95, base_conf - penalty))

    rationale_out = rationale or ""
    if codes:
        gate_note = (
            " Decision safety gates reduced confidence: " + ", ".join(sorted(set(codes))) + "."
            if not ar
            else " خفّضت بوابات سلامة القرار مستوى الثقة: " + "، ".join(sorted(set(codes))) + "."
        )
        rationale_out = (rationale_out + gate_note).strip()

    return {
        "verdict": current,
        "original_verdict": original,
        "rationale": rationale_out,
        "conditions": new_conditions,
        "confidence": adj_conf,
        "warnings": warnings,
        "gate_codes": sorted(set(codes)),
        "downgraded": _rank(current) < _rank(original),
        "false_confidence_blocked": bool(codes and original == "GO"),
    }
