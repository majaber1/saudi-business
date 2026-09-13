from __future__ import annotations

import json
import re

from langchain_core.messages import AIMessage, SystemMessage

from ..config import get_llm
from ..models.study_state import StudyState

SYSTEM_PROMPT_AR = """
أنت مستشار قرارات استثمارية خبير في السوق السعودي.
مهمتك: إصدار القرار النهائي بناءً على كل التحليلات السابقة.

المدخلات المتاحة:
- ملف المشروع (النوع، القطاع، المرحلة)
- الأدلة والمصادر
- الافتراضات المعتمدة
- التحليل المالي (NPV, IRR, فترة الاسترداد)
- تقييم المخاطر

القرارات الممكنة:
- GO: المشروع مجدي ويُنصح بالمضي فيه
- GO_WITH_CONDITIONS: مجدي لكن بشروط محددة
- DEFER: يحتاج مزيد من المعلومات أو الانتظار
- NO_GO: غير مجدي في الوضع الحالي
- INSUFFICIENT_EVIDENCE: لا تكفي البيانات لاتخاذ قرار

قواعد صارمة:
- لا تعطِ GO إذا كان IRR سالب أو NPV سالب بشكل واضح
- لا تعطِ GO إذا كانت المخاطر الحرجة بدون خطة تخفيف
- DEFER أفضل من GO مع بيانات ناقصة
- كن صريحاً وموضوعياً
- أجب بالعربية ما لم يكتب المستخدم بالإنجليزية

أخرج JSON داخل ```json ... ```:
{
  "verdict": "GO|GO_WITH_CONDITIONS|DEFER|NO_GO|INSUFFICIENT_EVIDENCE",
  "rationale": "شرح مفصل للقرار",
  "conditions": ["الشروط إن وجدت"],
  "key_risks": ["المخاطر الرئيسية"],
  "confidence_score": 0.0-1.0,
  "next_steps": ["الخطوات التالية المقترحة"]
}
"""

SYSTEM_PROMPT_EN = """
You are an expert investment decision advisor for the Saudi market.
Your task: issue the final verdict based on all previous analyses.

Available inputs:
- Project profile (type, sector, stage)
- Evidence and sources
- Approved assumptions
- Financial analysis (NPV, IRR, payback)
- Risk assessment

Possible verdicts:
- GO: Project is feasible, recommended to proceed
- GO_WITH_CONDITIONS: Feasible but with specific conditions
- DEFER: Needs more information or should wait
- NO_GO: Not feasible in current state
- INSUFFICIENT_EVIDENCE: Not enough data for a decision

Strict rules:
- Never give GO if IRR is negative or NPV is clearly negative
- Never give GO if critical risks have no mitigation plan
- DEFER is better than GO with incomplete data
- Be honest and objective
- Reply in English if user writes in English

Output JSON inside ```json ... ```:
{
  "verdict": "GO|GO_WITH_CONDITIONS|DEFER|NO_GO|INSUFFICIENT_EVIDENCE",
  "rationale": "detailed explanation",
  "conditions": ["conditions if any"],
  "key_risks": ["key risks"],
  "confidence_score": 0.0-1.0,
  "next_steps": ["suggested next steps"]
}
"""


def run_decision(state: StudyState) -> StudyState:
    lang = state.language
    system_prompt = SYSTEM_PROMPT_AR if lang == "ar" else SYSTEM_PROMPT_EN
    llm = get_llm("decision")

    context_parts = []
    if state.profile:
        context_parts.append(
            f"Project: {state.profile.archetype} / {state.profile.sector} / "
            f"Stage: {state.profile.stage} / Goal: {state.profile.decision_goal}"
        )
    if state.claims:
        claims_text = "\n".join(f"- {c.statement} ({c.source_type}, conf: {c.confidence})" for c in state.claims[:10])
        context_parts.append(f"Evidence:\n{claims_text}")
    if state.assumptions:
        assumptions_text = "\n".join(
            f"- {a.key}: {a.value} ({a.confidence}) [low:{a.low} / base:{a.base} / high:{a.high}]"
            for a in state.assumptions
        )
        context_parts.append(f"Assumptions:\n{assumptions_text}")
    if state.financial_results:
        fr = state.financial_results
        context_parts.append(
            f"Financials: NPV={fr.get('npv')}, IRR={fr.get('irr')}, "
            f"Payback={fr.get('payback_months')}m, Breakeven={fr.get('breakeven_months')}m"
        )
        scenarios = fr.get("scenarios", {})
        if scenarios:
            context_parts.append(f"Scenarios: {json.dumps(scenarios)}")
    if state.decision_risks:
        context_parts.append(f"Critical risks: {', '.join(state.decision_risks)}")

    extra = ""
    if context_parts:
        extra = "\n\nFull Context:\n" + "\n".join(context_parts)

    messages = [SystemMessage(content=system_prompt + extra)] + state.messages

    lang = getattr(state, "language", "en") or "en"
    try:
        response = llm.invoke(messages)
        response_text = response.content
        decision_data = _extract_json(response_text)
    except Exception as e:
        from ..utils.safe_messages import sanitize_error_for_user

        sanitize_error_for_user(e, language=lang, context="decision.invoke")
        decision_data = _fallback_decision(state)
        response_text = (
            "تعذر الاتصال بنموذج القرار؛ تم إعداد حكم أولي للمراجعة في التقرير."
            if lang == "ar"
            else "Decision model unavailable; a provisional verdict was prepared for the report."
        )

    if decision_data:
        provisional_verdict = decision_data.get("verdict", "INSUFFICIENT_EVIDENCE")
        provisional_rationale = decision_data.get("rationale", "")
        provisional_conditions = list(decision_data.get("conditions", []) or [])
        provisional_confidence = decision_data.get("confidence_score")

        # Hardening Sprint: deterministic financial + evidence safety gates (no silent fixes).
        try:
            from ai_engine.hardening import (
                apply_decision_safety,
                evaluate_evidence_verdict_gates,
                evaluate_financial_trust_gates,
            )

            arch = None
            if state.profile:
                arch = getattr(state.profile, "archetype", None)
            fin_gate = evaluate_financial_trust_gates(
                financial_results=state.financial_results or {},
                assumptions=state.assumptions,
                archetype=arch,
                language=lang or "en",
            )
            research_ctx = getattr(state, "research_context", None)
            research_quality = getattr(state, "research_quality", None)
            if research_quality is None and isinstance(research_ctx, dict):
                research_quality = research_ctx.get("research_quality")
            ev_gate = evaluate_evidence_verdict_gates(
                archetype=arch,
                claims=state.claims,
                research_quality=research_quality,
                language=lang or "en",
            )
            safe = apply_decision_safety(
                verdict=provisional_verdict,
                rationale=provisional_rationale,
                conditions=provisional_conditions,
                confidence=provisional_confidence if isinstance(provisional_confidence, (int, float)) else None,
                financial_gate=fin_gate,
                evidence_gate=ev_gate,
                language=lang or "en",
            )
            state.verdict = safe["verdict"]
            state.decision_rationale = safe["rationale"]
            state.decision_conditions = safe["conditions"]
            # Persist gate audit on financial results / state when possible (no migration).
            if isinstance(state.financial_results, dict):
                state.financial_results = {
                    **state.financial_results,
                    "trust_gates": fin_gate,
                }
            try:
                state.decision_safety = {
                    "financial": fin_gate,
                    "evidence": ev_gate,
                    "applied": {
                        "original_verdict": safe["original_verdict"],
                        "verdict": safe["verdict"],
                        "gate_codes": safe["gate_codes"],
                        "downgraded": safe["downgraded"],
                        "confidence": safe["confidence"],
                    },
                }
            except Exception:
                pass
        except Exception:
            state.verdict = provisional_verdict
            state.decision_rationale = provisional_rationale
            state.decision_conditions = provisional_conditions

        state.decision_risks = decision_data.get("key_risks", state.decision_risks)
        state.decision_version += 1
        state.phase = "REPORT_READY"
        state.error = None

    from ..utils.safe_messages import sanitize_chat_content

    public = sanitize_chat_content(
        response_text,
        language=lang,
        fallback=(
            "تم تحديث القرار. راجع لوحة الحكم والتقرير."
            if lang == "ar"
            else "Decision updated. Review the verdict panel and report."
        ),
    )
    if public:
        state.messages.append(AIMessage(content=public))
    state.next_action = "present_decision"
    return state


def _fallback_decision(state: StudyState) -> dict:
    fr = state.financial_results or {}
    npv = fr.get("npv")
    irr = fr.get("irr")
    risks = list(state.decision_risks or [])[:3] or ["Execution risk", "Market risk"]
    if isinstance(npv, (int, float)) and npv > 0:
        verdict = "GO_WITH_CONDITIONS"
        rationale = (
            f"Base-case NPV is positive ({npv}) with IRR={irr}. "
            "Proceed under staged conditions while monitoring critical risks."
        )
        conditions = [
            "Re-validate top assumptions after pilot / first operating period",
            "Keep contingency for the highest-impact critical risk",
        ]
    else:
        verdict = "DEFER"
        rationale = (
            f"Financial case is inconclusive (NPV={npv}, IRR={irr}). "
            "Defer full commitment until assumptions are de-risked."
        )
        conditions = ["Improve evidence quality on revenue and cost drivers"]
    return {
        "verdict": verdict,
        "rationale": rationale,
        "conditions": conditions,
        "key_risks": risks,
    }


def _extract_json(text: str) -> dict | None:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None
