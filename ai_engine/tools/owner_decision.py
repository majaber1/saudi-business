"""Owner response to a recommendation.

The engine verdict stays authoritative. An approval does not turn
INSUFFICIENT_EVIDENCE or NO_GO into GO. A rejection is not rewritten
into an approval of the same analysis.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

OWNER_ACTIONS = frozenset({"approve", "reject", "request_modification"})


def current_recommendation(state: Any) -> str | None:
    verdict = getattr(state, "verdict", None)
    if verdict:
        return str(verdict)
    financial = getattr(state, "financial_results", None) or {}
    if isinstance(financial, dict) and financial.get("verdict_override"):
        return str(financial["verdict_override"])
    return None


def mark_owner_decision_stale(state: Any) -> Any:
    current = getattr(state, "owner_decision", None)
    if isinstance(current, dict) and current:
        state.owner_decision = {**current, "stale": True}
    return state


def record_owner_decision(
    state: Any,
    action: str,
    *,
    note: str | None = None,
    now: datetime | None = None,
) -> Any:
    chosen = (action or "").strip().lower()
    if chosen not in OWNER_ACTIONS:
        raise ValueError("INVALID_ACTION")
    recommendation = current_recommendation(state)
    if not recommendation:
        raise ValueError("NO_RECOMMENDATION")
    financial = getattr(state, "financial_results", None) or {}
    if isinstance(financial, dict) and financial.get("stale"):
        raise ValueError("STALE_ANALYSIS")
    previous = getattr(state, "owner_decision", None) or {}
    analysis_version = int(getattr(state, "decision_version", 0) or 0)
    assumptions_version = int(getattr(state, "assumptions_version", 0) or 0)
    if (
        isinstance(previous, dict)
        and previous.get("action") == "reject"
        and chosen == "approve"
        and not previous.get("stale")
        and previous.get("analysis_version") == analysis_version
        and previous.get("assumptions_version") == assumptions_version
    ):
        raise ValueError("REJECTED_DECISION_UNCHANGED")
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    state.owner_decision = {
        "action": chosen,
        "note": (note or "").strip() or None,
        "decided_at": moment.astimezone(timezone.utc).isoformat(),
        "analysis_version": analysis_version,
        "assumptions_version": assumptions_version,
        "recommendation": recommendation,
        "stale": False,
    }
    if chosen == "request_modification":
        state.phase = "ASSUMPTIONS_REVIEW"
        state.assumptions_approved = False
        state.next_action = "review_assumptions"
    elif getattr(state, "phase", None) in {"ANALYZED", "DECISION_READY"}:
        state.phase = "REPORT_READY"
        state.next_action = "review_report"
    return state


def format_owner_decision_line(decision: Any, locale: str = "en") -> str:
    """Short report sentence. Missing decision stays explicit."""
    arabic = locale == "ar"
    if not isinstance(decision, dict) or not decision.get("action"):
        return "قرار المالك: غير مسجل" if arabic else "Owner decision: not recorded"
    labels = {
        "approve": ("Owner accepted this recommendation", "قبل المالك هذه التوصية"),
        "reject": ("Owner rejected this recommendation", "رفض المالك هذه التوصية"),
        "request_modification": ("Owner requested modification", "طلب المالك تعديلاً"),
    }
    english, arabic_label = labels.get(str(decision.get("action")), (str(decision.get("action")), str(decision.get("action"))))
    text = arabic_label if arabic else english
    if decision.get("stale"):
        text += " — لم يعد سارياً" if arabic else " — no longer current"
    recommendation = decision.get("recommendation") or ""
    recorded = decision.get("decided_at") or ""
    version = decision.get("analysis_version")
    if arabic:
        return f"{text}. التوصية: {recommendation}. وقت التسجيل: {recorded}. إصدار التحليل: {version}."
    return f"{text}. Recommendation: {recommendation}. Recorded: {recorded}. Analysis version: {version}."
