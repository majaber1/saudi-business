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


def test_request_modification_after_rejection_does_not_approve():
    state = _state(phase="REPORT_READY")
    record_owner_decision(state, "reject")
    record_owner_decision(state, "request_modification", note="Confirm the rent")
    assert state.owner_decision["action"] == "request_modification"
    assert state.owner_decision["note"] == "Confirm the rent"
    assert state.phase == "ASSUMPTIONS_REVIEW"
    assert state.assumptions_approved is False
    assert state.verdict == "INSUFFICIENT_EVIDENCE"


def test_report_exports_repeat_the_persisted_operating_statement():
    import io
    import zipfile
    from xml.etree import ElementTree

    from pypdf import PdfReader

    from backend.app.services.reporting_v2 import (
        build_v2_report_context,
        generate_v2_docx,
        generate_v2_pdf,
        operating_statement_lines,
    )

    financial = {
        "investment_grade": False,
        "cash_flow_basis": "PRE_TAX_OPERATING_PROJECTION",
        "verdict_override": "INSUFFICIENT_EVIDENCE",
        "capex": 400000,
        "monthly_net": -1600,
        "annual_cash_flows": [-19200],
        "lines": [
            {"id": "revenue", "monthly": 52000, "annual": 624000},
            {"id": "rent", "monthly": 20000, "annual": 240000},
            {"id": "payroll", "monthly": 18000, "annual": 216000},
            {"id": "operating_cost", "monthly": 15600, "annual": 187200},
        ],
    }
    state = {
        "profile": {"archetype": "fnb"},
        "language": "en",
        "phase": "REPORT_READY",
        "verdict": None,
        "financial_results": financial,
        "owner_decision": {
            "action": "reject",
            "recommendation": "INSUFFICIENT_EVIDENCE",
            "decided_at": "2026-10-28T21:41:25+00:00",
            "analysis_version": 0,
        },
    }
    ctx = build_v2_report_context(state)
    statement = operating_statement_lines(financial, "en")
    assert "Monthly net: -1600 SAR" in statement
    assert "Revenue: 52000 SAR monthly / 624000 SAR annual" in statement
    assert ctx["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert "Monthly net: -1600 SAR" in "\n".join(ctx["operating_statement"])

    pdf_text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(io.BytesIO(generate_v2_pdf(ctx, "en"))).pages
    )
    for token in ("52000", "20000", "18000", "15600", "-1600", "-19200", "400000", "INSUFFICIENT_EVIDENCE", "Owner rejected"):
        assert token in pdf_text

    xml = zipfile.ZipFile(io.BytesIO(generate_v2_docx(ctx, "ar"))).read("word/document.xml")
    root = ElementTree.fromstring(xml)
    doc_text = "".join(
        node.text or ""
        for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
    )
    for token in ("52000", "20000", "18000", "15600", "-1600", "-19200", "INSUFFICIENT_EVIDENCE", "رفض المالك"):
        assert token in doc_text


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
