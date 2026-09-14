"""Evidence → verdict gates (deterministic decision safety).

Never allow poor/missing critical evidence + strong GO.
Also detect allowlisted numeric contradictions between evidence and assumptions.
Does NOT modify Research Quality authority / freshness / conflict ranking.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

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

# Allowlisted comparable families only. Never cross-compare families.
# period: day | month | once
# currency: None means dimensionless count (not money).
_ASSUMPTION_NUMERIC_KEYS: dict[str, tuple[str, str, Optional[str]]] = {
    # metric_family, period, currency
    "daily_covers": ("transaction_volume", "day", None),
    "daily_transactions": ("transaction_volume", "day", None),
    "transactions_per_day": ("transaction_volume", "day", None),
    "covers_per_day": ("transaction_volume", "day", None),
    "monthly_transactions": ("transaction_volume", "month", None),
    "transactions_per_month": ("transaction_volume", "month", None),
    "monthly_covers": ("transaction_volume", "month", None),
    "avg_ticket": ("avg_ticket", "once", "SAR"),
    "average_ticket": ("avg_ticket", "once", "SAR"),
    "ticket_size": ("avg_ticket", "once", "SAR"),
}

# Days-per-month convention for deterministic day↔month conversion of counts only.
_PERIOD_DAYS = {"day": 1.0, "month": 30.0}

# Material contradiction when normalized ratio exceeds this (max/min).
_MATERIAL_RATIO = 3.0

_NUMBER_RE = re.compile(
    r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w.])"
)


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


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    # Strip trailing units like "SAR", "/day"
    m = re.match(r"^([+-]?\d+(?:\.\d+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _assumption_entries(assumptions: dict[str, Any] | Iterable[Any] | None) -> list[dict[str, Any]]:
    """Flatten assumptions into {key, value, unit, currency} dicts."""
    if assumptions is None:
        return []
    entries: list[dict[str, Any]] = []
    if isinstance(assumptions, dict):
        for key, val in assumptions.items():
            if isinstance(val, dict) and ("value" in val or "base" in val):
                entries.append(
                    {
                        "key": str(key),
                        "value": val.get("value", val.get("base")),
                        "unit": val.get("unit"),
                        "currency": val.get("currency"),
                    }
                )
            else:
                entries.append({"key": str(key), "value": val, "unit": None, "currency": None})
        return entries
    for item in assumptions:
        if isinstance(item, dict):
            key = item.get("key") or item.get("id") or item.get("name")
            if not key:
                continue
            entries.append(
                {
                    "key": str(key),
                    "value": item.get("value", item.get("base")),
                    "unit": item.get("unit"),
                    "currency": item.get("currency"),
                }
            )
            continue
        key = getattr(item, "key", None) or getattr(item, "id", None)
        if key is None:
            continue
        val = getattr(item, "value", None)
        if val is None:
            val = getattr(item, "base", None)
        entries.append(
            {
                "key": str(key),
                "value": val,
                "unit": getattr(item, "unit", None),
                "currency": getattr(item, "currency", None),
            }
        )
    return entries


def _normalize_period(value: float, period: str, target: str) -> Optional[float]:
    if period == target:
        return value
    if period not in _PERIOD_DAYS or target not in _PERIOD_DAYS:
        return None
    if period == "once" or target == "once":
        return value if period == target else None
    # Convert via day basis for count metrics only.
    per_day = value / _PERIOD_DAYS[period]
    return per_day * _PERIOD_DAYS[target]


def _detect_currency(text: str) -> Optional[str]:
    t = text.lower()
    if "usd" in t or "$" in t or "dollar" in t:
        return "USD"
    if "sar" in t or "ر.س" in t or "ريال" in t:
        return "SAR"
    return None


def _extract_evidence_transaction_facts(claims: Iterable[Any] | None) -> list[dict[str, Any]]:
    """Pull allowlisted transaction-volume facts from claim text."""
    facts: list[dict[str, Any]] = []
    for c in claims or []:
        if isinstance(c, dict):
            statement = str(c.get("statement") or c.get("text") or c.get("claim") or "")
        else:
            statement = str(getattr(c, "statement", "") or getattr(c, "text", "") or c)
        if not statement:
            continue
        low = statement.lower()
        # Skip market-size / revenue language to avoid false compares.
        if any(
            tok in low
            for tok in (
                "market size",
                "tam",
                "sam",
                "som",
                "revenue",
                "sales volume sar",
                "gdp",
                "حجم السوق",
                "إيراد",
            )
        ) and not any(tok in low for tok in ("transaction", "transactions", "covers", "cover", "معاملات", "زبائن")):
            continue

        period: Optional[str] = None
        if re.search(r"\bper\s*day\b|\b/day\b|\bdaily\b|\beach day\b|\bيوم(?:ي|يا)?\b", low):
            period = "day"
        elif re.search(r"\bper\s*month\b|\b/month\b|\bmonthly\b|\beach month\b|\bشهر(?:ي|يا)?\b", low):
            period = "month"

        is_tx = bool(
            re.search(
                r"\btransactions?\b|\bcovers?\b|\borders?\b|\bvisits?\b|\bمعاملات?\b|\bزبائن\b",
                low,
            )
        )
        if not is_tx or period is None:
            continue

        # Prefer number nearest to the metric keyword.
        nums = []
        for m in _NUMBER_RE.finditer(statement.replace("\u066c", ",")):
            raw = m.group(1).replace(",", "")
            try:
                nums.append((m.start(), float(raw)))
            except ValueError:
                continue
        if not nums:
            continue
        # Choose the largest plausible count near transaction wording (avoid years like 2026).
        candidates = [n for _, n in nums if 1 <= n <= 10_000_000 and n not in {2024, 2025, 2026, 2027}]
        if not candidates:
            continue
        value = max(candidates)
        currency = _detect_currency(statement)
        # Counts must not carry currency — if currency detected near money verbs, skip.
        if currency and re.search(r"\b(sar|usd|revenue|sales|price|ticket)\b", low):
            # e.g. "5000 SAR ticket" is not transaction volume
            if "ticket" in low or "price" in low or "revenue" in low or "sales" in low:
                continue
        facts.append(
            {
                "metric": "transaction_volume",
                "value": value,
                "unit": "count",
                "period": period,
                "currency": None,
                "source_text": statement[:240],
            }
        )
    return facts


def _extract_assumption_facts(assumptions: dict[str, Any] | Iterable[Any] | None) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for entry in _assumption_entries(assumptions):
        key = str(entry.get("key") or "").strip().lower()
        meta = _ASSUMPTION_NUMERIC_KEYS.get(key)
        if not meta:
            continue
        family, period, default_currency = meta
        value = _as_float(entry.get("value"))
        if value is None:
            continue
        unit_raw = str(entry.get("unit") or "").strip().lower()
        currency = entry.get("currency")
        if currency:
            currency = str(currency).upper()
        elif default_currency:
            currency = default_currency
        # Reject percent disguised as volume.
        if family == "transaction_volume" and (
            "%" in unit_raw or "percent" in unit_raw or "pct" in unit_raw
        ):
            continue
        if family == "avg_ticket":
            # Do not compare if unit explicitly USD while family defaults SAR without trusted FX.
            if "usd" in unit_raw or currency == "USD":
                # Still record but mark currency USD so compare refuses SAR↔USD.
                currency = "USD"
            elif not currency:
                currency = "SAR"
        facts.append(
            {
                "metric": family,
                "assumption_key": key,
                "value": value,
                "unit": "count" if family == "transaction_volume" else "currency",
                "period": period,
                "currency": currency,
            }
        )
    return facts


def evaluate_numeric_evidence_assumption_consistency(
    *,
    claims: Iterable[Any] | None,
    assumptions: dict[str, Any] | Iterable[Any] | None,
    language: str = "en",
) -> dict[str, Any]:
    """Allowlisted deterministic numeric consistency check.

    Only compares same metric family with compatible unit/period/currency.
    Never invents FX conversion. Never compares market size vs project revenue.
    """
    ar = language == "ar"
    contradictions: list[dict[str, Any]] = []
    evidence_facts = _extract_evidence_transaction_facts(claims)
    assumption_facts = _extract_assumption_facts(assumptions)

    # Compare transaction_volume family only for evidence↔assumption (primary P1 class).
    # avg_ticket evidence extraction is intentionally not free-text scraped to avoid
    # false SAR↔USD / percent collisions; assumption-only ticket checks are skipped here.
    for ev in evidence_facts:
        for asu in assumption_facts:
            if ev["metric"] != asu["metric"]:
                continue
            if ev["metric"] != "transaction_volume":
                continue
            # Counts: currency must both be None.
            if ev.get("currency") or asu.get("currency"):
                continue
            target_period = asu["period"]
            ev_norm = _normalize_period(float(ev["value"]), ev["period"], target_period)
            asu_norm = float(asu["value"])
            if ev_norm is None or asu_norm <= 0 or ev_norm <= 0:
                continue
            ratio = max(ev_norm, asu_norm) / min(ev_norm, asu_norm)
            if ratio < _MATERIAL_RATIO:
                continue
            finding = {
                "code": "EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION",
                "evidence_metric": ev["metric"],
                "evidence_value": ev["value"],
                "evidence_unit": ev["unit"],
                "evidence_period": ev["period"],
                "assumption_metric": asu["metric"],
                "assumption_key": asu.get("assumption_key"),
                "assumption_value": asu["value"],
                "assumption_unit": asu["unit"],
                "assumption_period": asu["period"],
                "normalized_period": target_period,
                "normalized_evidence_value": round(ev_norm, 4),
                "normalized_assumption_value": round(asu_norm, 4),
                "ratio": round(ratio, 4),
                "contradiction_reason": (
                    f"Evidence {ev['value']} transactions/{ev['period']} normalizes to "
                    f"{ev_norm:.4g}/{target_period}, vs assumption {asu['value']}/{target_period} "
                    f"(ratio {ratio:.2f}× ≥ {_MATERIAL_RATIO}×)."
                ),
            }
            contradictions.append(finding)

    codes: list[str] = []
    messages: list[str] = []
    if contradictions:
        codes.append("EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION")
        for finding in contradictions:
            messages.append(
                finding["contradiction_reason"]
                if not ar
                else (
                    f"تناقض رقمي بين الدليل والافتراض: الدليل {finding['evidence_value']} "
                    f"لكل {finding['evidence_period']} مقابل الافتراض {finding['assumption_value']} "
                    f"لكل {finding['assumption_period']}."
                )
            )

    return {
        "status": "FAIL" if contradictions else "PASS",
        "codes": codes,
        "messages": messages,
        "findings": contradictions,
        "confidence_penalty": min(0.35, 0.2 * len(contradictions)),
    }


def evaluate_evidence_verdict_gates(
    *,
    archetype: str | None,
    claims: Iterable[Any] | None,
    research_quality: dict[str, Any] | None = None,
    assumptions: dict[str, Any] | Iterable[Any] | None = None,
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

    numeric = evaluate_numeric_evidence_assumption_consistency(
        claims=claims,
        assumptions=assumptions,
        language=language,
    )
    if numeric.get("codes"):
        codes.extend(numeric["codes"])
        messages.extend(numeric.get("messages") or [])
        confidence_penalty = min(0.75, confidence_penalty + float(numeric.get("confidence_penalty") or 0))
        # Critical numeric contradiction cannot support an unconstrained GO.
        if _rank(max_verdict) > _rank("GO_WITH_CONDITIONS"):
            max_verdict = "GO_WITH_CONDITIONS"

    return {
        "status": "PASS" if not missing and not numeric.get("findings") else "FAIL",
        "codes": sorted(set(codes)),
        "messages": messages,
        "missing_themes": missing,
        "required_themes": list(required),
        "max_allowed_verdict": max_verdict,
        "confidence_penalty": confidence_penalty,
        "numeric_contradictions": list(numeric.get("findings") or []),
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

    if "EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION" in codes:
        if _rank(current) >= _rank("GO"):
            current = "GO_WITH_CONDITIONS"
        for finding in ev.get("numeric_contradictions") or []:
            reason = finding.get("contradiction_reason") or "Evidence contradicts assumption numerically."
            new_conditions.append(
                f"Resolve evidence–assumption numeric contradiction: {reason}"
                if not ar
                else f"عالج التناقض الرقمي بين الدليل والافتراض: {reason}"
            )
        if not ev.get("numeric_contradictions"):
            new_conditions.append(
                "Resolve evidence–assumption numeric contradiction before full commitment."
                if not ar
                else "عالج التناقض الرقمي بين الدليل والافتراض قبل الالتزام الكامل."
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
        "numeric_contradictions": list(ev.get("numeric_contradictions") or []),
    }
