"""Owner decision stays separate from the engine verdict."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from ai_engine.tools.owner_decision import (
    format_owner_decision_line,
    mark_owner_decision_stale,
    record_owner_decision,
)


def _state(**overrides):
    values = {
        "verdict": "INSUFFICIENT_EVIDENCE",
        "financial_results": {"investment_grade": False, "stale": False},
        "decision_version": 2,
        "assumptions_version": 3,
        "phase": "ANALYZED",
        "assumptions_approved": True,
        "next_action": None,
        "owner_decision": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_approve_records_version_without_changing_verdict():
    state = _state()
    record_owner_decision(
        state,
        "approve",
        now=datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc),
    )
    assert state.verdict == "INSUFFICIENT_EVIDENCE"
    assert state.owner_decision["action"] == "approve"
    assert state.owner_decision["analysis_version"] == 2
    assert state.owner_decision["assumptions_version"] == 3
    assert state.owner_decision["decided_at"].startswith("2026-10-28")
    assert state.phase == "REPORT_READY"


def test_rejected_analysis_is_not_rewritten_to_approved():
    state = _state()
    record_owner_decision(state, "reject")
    with pytest.raises(ValueError, match="REJECTED_DECISION_UNCHANGED"):
        record_owner_decision(state, "approve")
    assert state.owner_decision["action"] == "reject"


def test_request_modification_returns_to_assumption_review():
    state = _state()
    record_owner_decision(state, "request_modification", note="Confirm rent")
    assert state.phase == "ASSUMPTIONS_REVIEW"
    assert state.assumptions_approved is False
    assert state.next_action == "review_assumptions"
    assert state.verdict == "INSUFFICIENT_EVIDENCE"
    assert state.owner_decision["note"] == "Confirm rent"


def test_stale_projection_cannot_be_decided():
    state = _state(financial_results={"stale": True, "verdict_override": "NO_GO"})
    with pytest.raises(ValueError, match="STALE_ANALYSIS"):
        record_owner_decision(state, "approve")
    assert state.owner_decision is None


def test_ceiling_is_recorded_when_engine_verdict_is_empty():
    state = _state(
        verdict=None,
        financial_results={"verdict_override": "INSUFFICIENT_EVIDENCE", "stale": False},
    )
    record_owner_decision(state, "reject")
    assert state.verdict is None
    assert state.owner_decision["recommendation"] == "INSUFFICIENT_EVIDENCE"


def test_owner_edit_marks_the_recorded_decision_stale():
    state = _state()
    record_owner_decision(state, "approve")
    mark_owner_decision_stale(state)
    assert state.owner_decision["action"] == "approve"
    assert state.owner_decision["stale"] is True


def test_report_line_states_when_the_owner_has_not_decided():
    assert format_owner_decision_line(None, "en") == "Owner decision: not recorded"
    assert "غير مسجل" in format_owner_decision_line(None, "ar")
    line = format_owner_decision_line(
        {
            "action": "reject",
            "recommendation": "NO_GO",
            "decided_at": "2026-10-28T12:00:00+00:00",
            "analysis_version": 4,
        },
        "en",
    )
    assert "rejected" in line
    assert "NO_GO" in line
    assert "4" in line


def test_report_context_uses_financial_ceiling_and_owner_decision():
    from backend.app.services.reporting_v2 import build_v2_report_context

    ctx = build_v2_report_context(
        {
            "profile": {},
            "financial_results": {
                "verdict_override": "INSUFFICIENT_EVIDENCE",
                "investment_grade": False,
                "cash_flow_basis": "PRE_TAX_OPERATING_PROJECTION",
            },
            "owner_decision": {"action": "reject", "recommendation": "INSUFFICIENT_EVIDENCE"},
        }
    )
    assert ctx["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert ctx["investment_grade"] is False
    assert ctx["owner_decision"]["action"] == "reject"
