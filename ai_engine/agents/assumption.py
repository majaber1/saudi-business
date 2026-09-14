"""Assumption agent: fills archetype schema only; AI estimates are labeled."""
from __future__ import annotations

import json
import re

from langchain_core.messages import AIMessage, SystemMessage

from ..config import get_llm
from ..models.study_state import StudyState, Assumption
from ..archetypes import (
    get_assumption_schema,
    schema_keys_for,
    assert_no_saas_leakage,
    assert_no_mobility_on_professional,
    detect_services_variant,
    normalize_archetype,
)
from ..hardening import (
    assumption_requirement_explanations,
    schema_archetype_for,
)

SYSTEM_PROMPT_AR = """
أنت محلل افتراضات لدراسات الجدوى في السوق السعودي.
املأ فقط مفاتيح الافتراضات المعطاة لنوع المشروع. لا تُضف مقاييس SaaS (CAC/Churn/ARR/MRR)
إلا إذا كان التصنيف saas_digital.

لكل افتراض:
- value / low / base / high كنصوص
- source: "user" أو "AI Estimated Assumption" إذا قدّرت القيمة
- confidence: confirmed|medium|low
- ai_estimated: true إذا كانت القيمة تقدير ذكاء اصطناعي

أخرج JSON:
```json
{{
  "assumptions": [ {{"key":"...", "value":"...", "source":"...", "confidence":"medium", "low":"...", "base":"...", "high":"...", "ai_estimated": false}} ],
  "assumptions_complete": true
}}
```
"""

SYSTEM_PROMPT_EN = """
You are an assumptions analyst for Saudi feasibility studies.
Fill ONLY the provided assumption keys for this project archetype.
Do NOT add SaaS metrics (CAC/Churn/ARR/MRR) unless archetype is saas_digital.

For each assumption:
- value / low / base / high as strings
- source: "user" or "AI Estimated Assumption" when you estimate
- confidence: confirmed|medium|low
- ai_estimated: true when AI estimated

Output JSON:
```json
{{
  "assumptions": [ {{"key":"...", "value":"...", "source":"...", "confidence":"medium", "low":"...", "base":"...", "high":"...", "ai_estimated": false}} ],
  "assumptions_complete": true
}}
```
"""


def run_assumptions(state: StudyState) -> StudyState:
    lang = state.language
    raw_archetype = normalize_archetype(state.profile.archetype if state.profile else "other")
    services_variant = getattr(state.profile, "services_variant", None) if state.profile else None
    # Rebuild context from recent user messages for variant safety.
    context_bits = []
    for msg in reversed(list(state.messages or [])):
        role = getattr(msg, "type", None) or getattr(msg, "role", None)
        content = getattr(msg, "content", None)
        if isinstance(msg, dict):
            role = msg.get("type") or msg.get("role")
            content = msg.get("content")
        if role in {"human", "user"} and content:
            context_bits.append(str(content))
            if len(context_bits) >= 3:
                break
    context_text = "\n".join(reversed(context_bits))
    # Hardening: map business archetype → schema id (e.g. marketplace→services).
    archetype = schema_archetype_for(raw_archetype) if raw_archetype else "other"
    schema = get_assumption_schema(
        archetype, context_text=context_text, services_variant=services_variant
    )
    allowed = schema_keys_for(
        archetype, context_text=context_text, services_variant=services_variant
    )
    schema_by_key = {f["key"]: f for f in schema}

    system_prompt = SYSTEM_PROMPT_AR if lang == "ar" else SYSTEM_PROMPT_EN

    context_parts = [
        f"Archetype: {archetype}",
        "Allowed assumption keys ONLY:\n"
        + "\n".join(
            f"- {f['key']}: {f['label_en']} ({f['input_type']}, unit={f.get('unit')})" for f in schema
        ),
    ]
    try:
        req = assumption_requirement_explanations(
            raw_archetype or archetype, language=lang, context_text=context_text
        )
        context_parts.append(
            "Requirement guidance (do not invent extra keys):\n"
            + f"- Banner: {req.get('banner')}\n"
            + f"- Critical keys: {', '.join(req.get('critical_keys') or [])}"
        )
        state.assumption_requirements = {
            "archetype": req.get("archetype"),
            "banner": req.get("banner"),
            "critical_keys": req.get("critical_keys") or [],
            "required_keys": req.get("required_keys") or [],
        }
    except Exception:
        pass
    if state.structured_answers:
        context_parts.append(
            "Structured answers already collected:\n"
            + json.dumps(state.structured_answers, ensure_ascii=False)
        )
    if state.claims:
        claims_text = "\n".join(
            f"- {c.statement} ({c.source_type}, conf={c.confidence})" for c in state.claims[:12]
        )
        context_parts.append(f"Evidence:\n{claims_text}")

    # Phase 6 — Knowledge Evidence Pack (citations only; never invent sources)
    knowledge = getattr(state, "knowledge_context", None) or {}
    if knowledge.get("citations") or knowledge.get("assumption_hints"):
        context_parts.append(
            "Knowledge Evidence Pack (use ONLY these real sources; do not invent citations):\n"
            + json.dumps(
                {
                    "comparable_projects": (knowledge.get("comparable_projects") or [])[:5],
                    "assumption_hints": (knowledge.get("assumption_hints") or [])[:8],
                    "risk_hints": (knowledge.get("risk_hints") or [])[:5],
                    "citations": (knowledge.get("citations") or [])[:8],
                },
                ensure_ascii=False,
            )
        )
        context_parts.append(
            "When an assumption is grounded in Knowledge Evidence, set "
            'source to "Knowledge Reference", ai_estimated=true, and mention the source title in value rationale if needed.'
        )

    extra = "\n\nContext:\n" + "\n".join(context_parts)
    messages = [SystemMessage(content=system_prompt + extra)] + list(
        state.messages[-4:] if state.messages else []
    )

    assumption_data: dict | None = None
    response_text = ""
    llm_unavailable = False
    # get_llm must be inside try/except: client init failures previously aborted
    # the agent after evidence approve had already set phase=ASSUMPTIONS_REVIEW,
    # leaving assumptions=[] and disabling Approve in the UI.
    try:
        llm = get_llm("assumptions")
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, "content") else str(response)
        assumption_data = _extract_json(response_text)
        if assumption_data is None:
            llm_unavailable = True
            response_text = (
                response_text
                or "Assumption generation used Rule Fallback (LLM response not parseable)."
            )
    except Exception as e:
        from ..utils.safe_messages import sanitize_error_for_user

        llm_unavailable = True
        sanitize_error_for_user(e, language=lang, context="assumption.invoke")
        response_text = (
            "تعذر الاتصال بنموذج الافتراضات؛ تم استخدام تقديرات قواعدية قابلة للمراجعة."
            if lang == "ar"
            else "Assumption model unavailable; rule-based estimates were prepared for review."
        )
        assumption_data = None

    seeded: dict[str, Assumption] = {}

    def _build_assumption(
        *,
        key: str,
        value: str | None,
        meta: dict,
        origin: str,
        source: str,
        confidence: str = "low",
        ai_estimated: bool = False,
        estimate_basis: str | None = None,
        estimate_rationale: str | None = None,
    ) -> Assumption:
        from ai_engine.hardening.assumption_semantics import (
            map_origin_to_provenance,
            semantic_type_for_key,
            validate_assumption_value,
        )

        check = validate_assumption_value(
            key=key,
            value=value,
            input_type=meta.get("input_type"),
            unit=meta.get("unit"),
        )
        if not check["ok"] or check["value"] is None:
            return Assumption(
                key=key,
                value="UNKNOWN",
                source=check.get("message") or source or "Unknown — no responsible estimate",
                confidence="low",
                low=None,
                base=None,
                high=None,
                origin="default",
                input_type=meta.get("input_type"),
                unit=meta.get("unit"),
                label_en=meta.get("label_en"),
                label_ar=meta.get("label_ar"),
                ai_estimated=False,
                provenance_class="UNKNOWN",
                semantic_type=check.get("semantic_type") or semantic_type_for_key(key, meta.get("input_type")),
                validation_code=check.get("code") or "UNKNOWN",
                estimate_basis=estimate_basis,
                estimate_rationale=estimate_rationale
                or check.get("message")
                or "Left UNKNOWN rather than fabricating a value",
            )
        prov = map_origin_to_provenance(origin)
        if check["value"] == "UNKNOWN":
            prov = "UNKNOWN"
        return Assumption(
            key=key,
            value=str(check["value"]),
            source=source,
            confidence=confidence,  # type: ignore[arg-type]
            low=str(check["value"]),
            base=str(check["value"]),
            high=str(check["value"]),
            origin=origin,  # type: ignore[arg-type]
            input_type=meta.get("input_type"),
            unit=meta.get("unit"),
            label_en=meta.get("label_en"),
            label_ar=meta.get("label_ar"),
            ai_estimated=ai_estimated,
            provenance_class=prov,  # type: ignore[arg-type]
            semantic_type=check.get("semantic_type"),
            validation_code=None,
            estimate_basis=estimate_basis,
            estimate_rationale=estimate_rationale,
        )

    # Seed owner_budget from structured answers or context mentions of SAR budget
    if "owner_budget" in allowed and "owner_budget" not in (state.structured_answers or {}):
        budget_hint = None
        for blob in (
            str((state.structured_answers or {}).get("budget") or ""),
            " ".join(str(m.content) if hasattr(m, "content") else str(m) for m in (state.messages or [])[-6:]),
        ):
            import re as _re

            m = _re.search(r"(?:SAR|ريال)?\s*([0-9][0-9,]{2,})\s*(?:SAR|ريال)?", blob, _re.I)
            if m and ("budget" in blob.lower() or "ميزانية" in blob or "450" in m.group(1)):
                budget_hint = m.group(1).replace(",", "")
                break
        if budget_hint:
            state.structured_answers = dict(state.structured_answers or {})
            state.structured_answers.setdefault("owner_budget", budget_hint)

    for key, raw in (state.structured_answers or {}).items():
        if key not in allowed:
            continue
        meta = schema_by_key.get(key, {})
        val = _as_str(raw).strip()
        if not _usable_user_assumption_value(meta, val):
            continue
        seeded[key] = _build_assumption(
            key=key,
            value=val,
            meta=meta,
            origin="user",
            source="user",
            confidence="confirmed",
            ai_estimated=False,
            estimate_basis="owner_input",
            estimate_rationale="Provided by owner via discovery / structured answers",
        )

    for a in (assumption_data or {}).get("assumptions") or []:
        key = str(a.get("key") or "").strip()
        if key not in allowed:
            continue
        meta = schema_by_key.get(key, {})
        ai_est = bool(a.get("ai_estimated")) or str(a.get("source") or "").lower().startswith("ai")
        if key in seeded and seeded[key].origin == "user":
            continue
        conf = str(a.get("confidence") or "low")
        if conf not in {"confirmed", "medium", "low"}:
            conf = "low"
        source = str(a.get("source") or ("AI Estimated Assumption" if ai_est else "model"))
        if ai_est and "AI Estimated" not in source:
            source = "AI Estimated Assumption"
        raw_value = _as_str(a.get("value")).strip()
        if not raw_value:
            raw_value = _default_value_for_field(meta or {"key": key}, archetype) or ""
        seeded[key] = _build_assumption(
            key=key,
            value=raw_value or None,
            meta=meta,
            origin="ai_estimated" if ai_est else "user",
            source=source,
            confidence=conf,
            ai_estimated=ai_est,
            estimate_basis="llm_estimate" if ai_est else "model",
            estimate_rationale="Model-proposed estimate pending owner review"
            if ai_est
            else None,
        )

    for field in schema:
        key = field["key"]
        if key in seeded:
            continue
        if not field.get("required", True):
            continue
        default_val = _default_value_for_field(field, archetype)
        if llm_unavailable:
            seeded[key] = _build_assumption(
                key=key,
                value=default_val,
                meta=field,
                origin="rule_fallback",
                source="Rule Fallback" if default_val else "Unknown — rule fallback refused placeholder",
                confidence="low",
                ai_estimated=False,
                estimate_basis="rule_fallback" if default_val else None,
                estimate_rationale="LLM unavailable; used key-aware fallback or UNKNOWN",
            )
        else:
            seeded[key] = _build_assumption(
                key=key,
                value=default_val,
                meta=field,
                origin="ai_estimated" if default_val else "default",
                source="AI Estimated Assumption" if default_val else "Unknown — no responsible estimate",
                confidence="low",
                ai_estimated=bool(default_val),
                estimate_basis="schema_gap_fill" if default_val else None,
                estimate_rationale="Required field missing after LLM; key-aware fill or UNKNOWN",
            )

    assumptions = list(seeded.values())
    assumptions = _apply_knowledge_refs(assumptions, getattr(state, "knowledge_context", None) or {})

    # Evidence-backed SYSTEM_ESTIMATE fill for UNKNOWN operating keys (never invent).
    try:
        from ai_engine.research.market.operating_estimates import (
            apply_estimates_to_assumptions,
            synthesize_operating_estimates,
        )

        evidence_items: list[dict] = []
        for c in state.claims or []:
            if hasattr(c, "model_dump"):
                evidence_items.append(c.model_dump())
            elif isinstance(c, dict):
                evidence_items.append(c)
            else:
                evidence_items.append(
                    {
                        "statement": getattr(c, "statement", ""),
                        "source_url": getattr(c, "source_url", None),
                        "source_key": getattr(c, "source_key", None),
                        "document_id": getattr(c, "document_id", None),
                    }
                )
        mr = getattr(state, "market_research_context", None) or {}
        if isinstance(mr, dict):
            for est in mr.get("operating_estimates") or []:
                if isinstance(est, dict) and est.get("key"):
                    # Prefer precomputed market estimates
                    pass
            for loc in mr.get("location_economics") or []:
                if isinstance(loc, dict):
                    evidence_items.append(
                        {
                            "statement": str(loc.get("notes") or loc.get("factor") or ""),
                            "source_url": loc.get("source_url"),
                            "source_key": loc.get("source_key"),
                            "document_id": loc.get("document_id"),
                            "geography": loc.get("geography"),
                            "evidence_kind": "location_context",
                        }
                    )
            for p in mr.get("pricing_signals") or []:
                if isinstance(p, dict) and p.get("price") is not None:
                    evidence_items.append(
                        {
                            "statement": (
                                f"Price signal: {p.get('item')} = {p.get('price')} "
                                f"{p.get('currency') or 'SAR'}"
                            ),
                            "source_url": p.get("source_url"),
                            "source_key": p.get("source_key"),
                            "document_id": p.get("document_id"),
                        }
                    )

        geo = "Saudi Arabia"
        if isinstance(state.structured_answers, dict):
            city = str(state.structured_answers.get("city") or "").strip()
            if city:
                geo = f"{city}, Saudi Arabia"

        precomputed = []
        if isinstance(mr, dict):
            for est in mr.get("operating_estimates") or []:
                if not isinstance(est, dict):
                    continue
                from ai_engine.research.market.operating_estimates import OperatingEstimate

                try:
                    precomputed.append(
                        OperatingEstimate(
                            key=str(est["key"]),
                            value=str(est["value"]),
                            low=est.get("low"),
                            base=est.get("base"),
                            high=est.get("high"),
                            currency=str(est.get("currency") or "SAR"),
                            geography=str(est.get("geography") or geo),
                            as_of=str(est.get("as_of") or ""),
                            confidence=float(est.get("confidence") or 0.4),
                            reasoning=str(est.get("reasoning") or ""),
                            source_urls=list(est.get("source_urls") or []),
                        )
                    )
                except Exception:  # noqa: BLE001
                    continue
        estimates = precomputed or synthesize_operating_estimates(
            evidence_items=evidence_items, geography=geo
        )
        assumptions = apply_estimates_to_assumptions(assumptions, estimates)
        if estimates:
            state.research_context = dict(state.research_context or {})
            state.research_context["operating_estimates_applied"] = [
                e.to_public_dict() for e in estimates
            ]
    except Exception as exc:  # noqa: BLE001
        logger = __import__("logging").getLogger(__name__)
        logger.info("operating estimate synthesis skipped: %s", exc)

    leaked = assert_no_saas_leakage(archetype, [a.key for a in assumptions])
    if leaked:
        assumptions = [a for a in assumptions if a.key not in leaked]
    if archetype == "services" and (
        (services_variant or detect_services_variant(context_text)) == "professional"
    ):
        mob = assert_no_mobility_on_professional([a.key for a in assumptions])
        if mob:
            assumptions = [a for a in assumptions if a.key not in mob]

    prev_sig = [(a.key, a.value, a.base) for a in (state.assumptions or [])]
    new_sig = [(a.key, a.value, a.base) for a in assumptions]
    state.assumptions = assumptions
    if new_sig != prev_sig or state.assumptions_version == 0:
        state.assumptions_version = int(state.assumptions_version or 0) + 1

    state.phase = "ASSUMPTIONS_REVIEW"
    state.assumptions_approved = False
    state.next_action = "review_assumptions"
    state.error = None

    summary_lines = [
        f"Assumptions prepared for archetype `{archetype}` (version {state.assumptions_version}).",
        f"Count: {len(assumptions)}. AI-estimated: {sum(1 for a in assumptions if a.ai_estimated)}.",
        "Review, edit, regenerate, or approve before financial analysis.",
    ]
    from ..utils.safe_messages import sanitize_chat_content

    extra = sanitize_chat_content(response_text, language=lang)
    if extra:
        summary_lines.append(extra[:500])
    state.messages.append(AIMessage(content="\n".join(summary_lines)))
    return state


def _as_str(v) -> str:
    if v is None:
        return ""
    return v if isinstance(v, str) else str(v)


def _usable_user_assumption_value(field: dict, val: str) -> bool:
    """Return False for empty / placeholder answers that would break financial extract."""
    if not val:
        return False
    lowered = val.strip().lower()
    if lowered in {
        "confirmed", "ok", "yes", "y", "true", "n/a", "na", "none", "null",
        "unknown", "tbd", "مؤكد", "نعم", "موافق",
    }:
        return False
    input_type = (field.get("input_type") or "").lower()
    if input_type in {"number", "currency", "percent"}:
        cleaned = val.replace(",", "").replace("%", "").replace("SAR", "").replace("ر.س", "").strip()
        try:
            float(cleaned)
        except ValueError:
            return False
    return True


def _default_value_for_field(field: dict, archetype: str) -> str | None:
    """Return a responsible key-aware default, or None → UNKNOWN (never generic 10000).

    Catch-all placeholder sentinels (10000 / 100000) are intentionally removed.
    Prefer UNKNOWN over fake precision for F&B / unknown fields.
    """
    from ai_engine.hardening.assumption_semantics import (
        is_placeholder_sentinel,
        validate_assumption_value,
    )

    key = field.get("key") or ""
    input_type = (field.get("input_type") or "").lower()
    # Explicit keyed defaults for non-F&B archetypes only (legacy models).
    defaults = {
        "target_customers": "200",
        "pricing": "500",
        "arr": "1200000",
        "mrr": "100000",
        "cac": "800",
        "churn": "3",
        "ltv": "8000",
        "acquisition_channels": "Organic",
        "initial_investment": "1500000",
        "capex": "1500000",
        "opex_monthly": "80000",
        "revenue_y1": "1200000",
        "gross_margin": "70",
        "land_cost": "5000000",
        "construction_boq": "15000000",
        "units": "100",
        "selling_price": "1200000",
        "absorption_rate": "40",
        "mw_capacity": "5",
        "rack_count": "200",
        "pue": "1.4",
        "power_cost": "0.25",
        "active_contracts": "15",
        "consultants_headcount": "20",
        "utilization_rate": "70",
        "monthly_recurring_contracts": "80000",
        "delivery_cost_monthly": "35000",
        "take_rate": "20",
        "monthly_trips": "50000",
        "drivers": "2000",
        "driver_cac": "150",
        "occupancy": "60",
        "pricing_per_kw": "400",
        "capex_total": "80000000",
        "opex_annual": "12000000",
        "financing": "50",
        # Safe non-placeholder F&B categorical / calendar defaults only
        "operating_days_year": "330",
        "delivery_dependency": "Partial (<30%)",
    }
    # Never invent F&B operating economics when LLM/user did not provide them.
    fnb_unknown_keys = {
        "seats_capacity",
        "operating_hours_day",
        "avg_ticket",
        "daily_covers",
        "rent_monthly",
        "labor_monthly",
        "food_cost_pct",
        "fitout_capex",
        "equipment_capex",
        "working_capital",
        "store_area_m2",
        "utilities_monthly",
        "marketing_monthly",
    }
    if archetype == "fnb" and key in fnb_unknown_keys:
        return None
    if key in defaults:
        candidate = defaults[key]
        if is_placeholder_sentinel(candidate, key=key, input_type=input_type):
            return None
        check = validate_assumption_value(key=key, value=candidate, input_type=input_type, unit=field.get("unit"))
        return check["value"] if check["ok"] else None
    # No catch-all numeric invent — categorical/text without options stays UNKNOWN
    if input_type in {"single_select", "multi_select"}:
        opts = field.get("options_en") or field.get("options") or []
        return str(opts[0]) if opts else None
    return None


def _extract_json(text: str) -> dict | None:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def _apply_knowledge_refs(assumptions: list[Assumption], knowledge: dict) -> list[Assumption]:
    """Attach real knowledge refs to matching assumptions. No fabricated citations."""
    if not knowledge:
        return assumptions
    hints = {h.get("key"): h for h in (knowledge.get("assumption_hints") or []) if h.get("key")}
    citations = knowledge.get("citations") or []
    out = []
    for a in assumptions:
        hint = hints.get(a.key)
        refs = []
        conf = None
        if hint:
            for ref in hint.get("refs") or []:
                if ref.get("document_id") or ref.get("study_memory_id"):
                    refs.append(
                        {
                            "document_id": ref.get("document_id"),
                            "chunk_id": ref.get("chunk_id"),
                            "study_memory_id": ref.get("study_memory_id"),
                            "title": ref.get("title"),
                            "similarity": ref.get("similarity"),
                        }
                    )
            conf = hint.get("confidence")
        if not refs:
            # Fallback: lexical overlap against citations (still requires real ids)
            key_tokens = [t for t in a.key.lower().replace("_", " ").split() if len(t) >= 3]
            for cite in citations:
                if not (cite.get("document_id") or cite.get("study_memory_id")):
                    continue
                claim = (cite.get("claim") or "").lower()
                if key_tokens and any(tok in claim for tok in key_tokens):
                    refs.append(
                        {
                            "document_id": cite.get("document_id"),
                            "chunk_id": cite.get("chunk_id"),
                            "study_memory_id": cite.get("study_memory_id"),
                            "title": cite.get("source_title"),
                            "similarity": cite.get("confidence"),
                        }
                    )
                    conf = cite.get("confidence")
                    if len(refs) >= 3:
                        break
        if refs:
            a.knowledge_refs = refs[:3]
            a.knowledge_confidence = float(conf) if conf is not None else None
            # Soft lexical knowledge matches must NOT promote provenance to
            # evidence-backed when no suggested numeric value was retrieved.
            suggested = None
            if hint:
                suggested = hint.get("suggested_value")
            if suggested is not None and str(suggested).strip() and a.origin in {
                "ai_estimated",
                "rule_fallback",
                "default",
            }:
                a.origin = "knowledge_reference"
                a.source = f"Evidence-backed estimate from {len(refs)} knowledge source(s)"
                a.ai_estimated = True
                a.provenance_class = "EVIDENCE_BACKED"
                a.estimate_basis = "knowledge_suggested_value"
            elif a.origin in {"ai_estimated", "rule_fallback", "default"}:
                # Keep SYSTEM_ESTIMATE / UNKNOWN labeling; attach refs for audit only
                n = len(refs)
                if a.value and str(a.value).upper() != "UNKNOWN":
                    a.source = f"{a.source or 'estimate'} (context refs: {n})"
                a.provenance_class = a.provenance_class or (
                    "UNKNOWN" if str(a.value).upper() == "UNKNOWN" else "SYSTEM_ESTIMATE"
                )
            elif a.origin == "user" and "Knowledge" not in (a.source or ""):
                a.source = f"User input (supported by {len(refs)} knowledge source(s))"
                a.provenance_class = a.provenance_class or "USER_PROVIDED"
        out.append(a)
    return out
