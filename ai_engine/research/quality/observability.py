"""Phase 8C.3 — Research Quality observability projection.

Presentation-only layer over frozen Phase 8C.2 quality results.
Does NOT recompute authority, freshness, conflicts, or preference.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

OBSERVABILITY_VERSION = "8c3-v1"

_SOURCE_LABELS: dict[str, dict[str, str]] = {
    "gastat": {"en": "GASTAT", "ar": "الهيئة العامة للإحصاء"},
    "misa": {"en": "MISA", "ar": "وزارة الاستثمار"},
    "monshaat": {"en": "Monsha'at", "ar": "منشآت"},
    "sama": {"en": "SAMA", "ar": "البنك المركزي السعودي"},
    "zatca": {"en": "ZATCA", "ar": "هيئة الزكاة والضريبة والجمارك"},
    "nca": {"en": "NCA", "ar": "الهيئة الوطنية للأمن السيبراني"},
    "saudi_open_data": {"en": "Saudi Open Data", "ar": "البيانات المفتوحة السعودية"},
}

_STATUS_LABELS: dict[str, dict[str, str]] = {
    "high_confidence": {"en": "High confidence", "ar": "ثقة عالية"},
    "medium_confidence": {"en": "Medium confidence", "ar": "ثقة متوسطة"},
    "low_confidence": {"en": "Low confidence", "ar": "ثقة منخفضة"},
    "conflict": {"en": "Conflict", "ar": "تعارض"},
    "unresolved": {"en": "Unresolved", "ar": "غير محسوم"},
    "stale": {"en": "Stale", "ar": "قديم"},
    "freshness_unknown": {"en": "Freshness unknown", "ar": "حداثة غير معروفة"},
}

_FRESHNESS_LABELS: dict[str, dict[str, str]] = {
    "CURRENT": {"en": "Current", "ar": "حديث"},
    "ACCEPTABLE": {"en": "Acceptable", "ar": "مقبول"},
    "STALE": {"en": "Stale", "ar": "قديم"},
    "UNKNOWN": {"en": "Publication date unavailable", "ar": "تاريخ النشر غير متوفر"},
    "NOT_APPLICABLE": {"en": "Freshness not applicable", "ar": "الحداثة غير منطبقة"},
}

_AUTHORITY_LABELS: dict[str, dict[str, str]] = {
    "PRIMARY": {"en": "Primary authority", "ar": "جهة رسمية أساسية"},
    "SECONDARY": {"en": "Secondary authority", "ar": "جهة رسمية ثانوية"},
    "RELATED": {"en": "Related authority", "ar": "جهة ذات صلة"},
    "UNRELATED": {"en": "Unrelated source", "ar": "مصدر غير ذي صلة"},
    "INELIGIBLE": {"en": "Ineligible source", "ar": "مصدر غير مؤهل"},
    "UNKNOWN": {"en": "Authority unknown", "ar": "سلطة غير معروفة"},
}

_PROVENANCE_LABELS: dict[str, dict[str, str]] = {
    "official_source": {"en": "Official source", "ar": "مصدر رسمي"},
    "knowledge_document": {"en": "Knowledge document", "ar": "وثيقة معرفة"},
    "knowledge_chunk": {"en": "Knowledge chunk", "ar": "جزء معرفة"},
    "retrieved_web": {"en": "Retrieved web evidence", "ar": "دليل مسترجع من الويب"},
    "user_document": {"en": "User-provided document", "ar": "وثيقة من المستخدم"},
    "unknown": {"en": "Provenance unknown", "ar": "مصدر غير معروف"},
}

_ROLE_LABELS: dict[str, dict[str, str]] = {
    "PREFERRED": {"en": "Preferred", "ar": "مفضل"},
    "ALTERNATE": {"en": "Alternate", "ar": "بديل"},
    "CONFLICT_UNRESOLVED": {"en": "Unresolved conflict", "ar": "تعارض غير محسوم"},
    "REJECTED_INELIGIBLE": {"en": "Rejected (ineligible)", "ar": "مرفوض (غير مؤهل)"},
    "REJECTED_AI_ASSUMPTION": {"en": "Rejected (AI assumption)", "ar": "مرفوض (افتراض ذكاء اصطناعي)"},
    "UNRANKED": {"en": "Unranked", "ar": "غير مُرتَّب"},
}


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _bilingual(table: Mapping[str, Mapping[str, str]], key: str | None) -> dict[str, str]:
    if not key:
        return {"en": "", "ar": ""}
    row = table.get(str(key)) or {}
    return {
        "en": row.get("en") or str(key),
        "ar": row.get("ar") or row.get("en") or str(key),
    }


def source_display_name(source_key: str | None) -> dict[str, str]:
    key = (source_key or "").strip().lower() or None
    if key and key in _SOURCE_LABELS:
        return _bilingual(_SOURCE_LABELS, key)
    if key:
        pretty = key.replace("_", " ").upper()
        return {"en": pretty, "ar": pretty}
    return {"en": "Unknown source", "ar": "مصدر غير معروف"}


def _evidence_index(claims: Sequence[Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for claim in claims or []:
        d = _as_dict(claim)
        eid = str(
            d.get("evidence_id")
            or d.get("id")
            or d.get("chunk_id")
            or d.get("document_id")
            or ""
        ).strip()
        if eid:
            out[eid] = d
    return out


def _provenance_kind(claim: Mapping[str, Any], evaluation: Mapping[str, Any]) -> str:
    origin = str(claim.get("origin") or "").lower()
    source_type = str(claim.get("source_type") or "").lower()
    authority = str(evaluation.get("authority_fit") or "").upper()
    if origin in {"user", "user_document"} or source_type in {"user_input", "user"}:
        return "user_document"
    if claim.get("chunk_id"):
        return "knowledge_chunk"
    if claim.get("document_id") or claim.get("from_knowledge"):
        return "knowledge_document"
    if authority in {"PRIMARY", "SECONDARY"}:
        return "official_source"
    if claim.get("source_url") or origin in {"research", "web", "live"}:
        return "retrieved_web"
    return "unknown"


def _claim_status(
    *,
    evaluation: Mapping[str, Any] | None,
    conflict: Mapping[str, Any] | None,
) -> str:
    if conflict and str(conflict.get("status") or "").upper() == "UNRESOLVED":
        return "unresolved"
    selection = str((evaluation or {}).get("selection_status") or "").upper()
    if selection == "CONFLICT_UNRESOLVED":
        return "unresolved"
    freshness = str((evaluation or {}).get("freshness") or "").upper()
    if conflict and str(conflict.get("status") or "").upper() == "RESOLVED_PREFERRED_SOURCE":
        if freshness == "STALE":
            return "stale"
        if freshness == "UNKNOWN":
            return "freshness_unknown"
        return "conflict"
    if freshness == "STALE":
        return "stale"
    if freshness == "UNKNOWN":
        return "freshness_unknown"
    qstate = str((evaluation or {}).get("quality_state") or "").upper()
    if qstate == "HIGH":
        return "high_confidence"
    if qstate == "MEDIUM":
        return "medium_confidence"
    return "low_confidence"


def _selection_reason(
    *,
    evaluation: Mapping[str, Any] | None,
    conflict: Mapping[str, Any] | None,
    source_key: str | None,
    claim_type: str | None,
) -> dict[str, str]:
    ev = evaluation or {}
    codes = [str(c) for c in (ev.get("selection_reason_codes") or [])]
    ranking = [str(c) for c in (ev.get("ranking_reason") or [])]
    authority = str(ev.get("authority_fit") or "").upper()
    freshness = str(ev.get("freshness") or "").upper()
    selection = str(ev.get("selection_status") or "").upper()
    src = source_display_name(source_key)
    ctype = (claim_type or "").replace("_", " ").title() or "this claim"

    if conflict and str(conflict.get("status") or "").upper() == "UNRESOLVED":
        return {
            "en": "This claim remains unresolved because two equally credible sources report different values.",
            "ar": "يبقى هذا الادعاء غير محسوم لأن مصدرين موثوقين بشكل متكافئ يوردان قيمتين مختلفتين.",
        }

    if selection == "PREFERRED" and authority == "PRIMARY":
        return {
            "en": f"{src['en']} is the primary authority for {ctype} data.",
            "ar": f"{src['ar']} هي الجهة الرسمية الأساسية لبيانات {ctype}.",
        }

    if (
        conflict
        and str(conflict.get("status") or "").upper() == "RESOLVED_PREFERRED_SOURCE"
        and selection == "PREFERRED"
    ):
        auth = _bilingual(_AUTHORITY_LABELS, authority)
        return {
            "en": f"This source was selected because it has stronger authority fit ({auth['en']}).",
            "ar": f"تم اختيار هذا المصدر لأن ملاءمة سلطته أقوى ({auth['ar']}).",
        }

    if any("newer" in r or "fresher" in r or "within_current_window" in r for r in ranking) and selection == "PREFERRED":
        return {
            "en": "This source is newer than the alternate evidence.",
            "ar": "هذا المصدر أحدث من الأدلة البديلة.",
        }

    if any("period" in r or "geography" in r or "relevance=EXACT" in r for r in ranking):
        return {
            "en": "This evidence matches the requested period and geography.",
            "ar": "يطابق هذا الدليل الفترة والجغرافيا المطلوبتين.",
        }

    if selection == "ALTERNATE":
        return {
            "en": "This is alternate evidence kept for auditability beside the preferred source.",
            "ar": "هذا دليل بديل محفوظ لأغراض التدقيق إلى جانب المصدر المفضل.",
        }

    if freshness == "STALE":
        return {
            "en": "Evidence is stale relative to the freshness policy window.",
            "ar": "الدليل قديم نسبةً إلى نافذة سياسة الحداثة.",
        }

    if freshness == "UNKNOWN":
        return {
            "en": "Publication date unavailable; freshness cannot be confirmed.",
            "ar": "تاريخ النشر غير متوفر؛ لا يمكن تأكيد الحداثة.",
        }

    if codes:
        return {
            "en": "Selected using deterministic research-quality policy.",
            "ar": "تم الاختيار وفق سياسة جودة البحث الحتمية.",
        }
    return {
        "en": "No additional selection detail available.",
        "ar": "لا تتوفر تفاصيل إضافية عن سبب الاختيار.",
    }


def _project_evidence_card(
    *,
    evidence_id: str,
    evaluation: Mapping[str, Any],
    claim: Mapping[str, Any] | None,
    conflict: Mapping[str, Any] | None,
) -> dict[str, Any]:
    claim = claim or {}
    source_key = evaluation.get("source_key") or claim.get("source_key")
    selection = str(evaluation.get("selection_status") or "UNRANKED").upper()
    freshness = str(evaluation.get("freshness") or "UNKNOWN").upper()
    authority = str(evaluation.get("authority_fit") or "UNKNOWN").upper()
    provenance_kind = _provenance_kind(claim, evaluation)
    published_at = evaluation.get("published_at") or claim.get("published_at")
    retrieved_at = (
        evaluation.get("retrieved_at")
        or claim.get("retrieved_date")
        or claim.get("retrieved_at")
    )
    source_url = claim.get("source_url") or claim.get("official_url") or claim.get("url")
    if source_url is not None:
        source_url = str(source_url).strip() or None

    official_validated = authority in {"PRIMARY", "SECONDARY"} and provenance_kind in {
        "official_source",
        "knowledge_document",
        "knowledge_chunk",
    }

    return {
        "evidence_id": evidence_id,
        "role": selection,
        "role_label": _bilingual(_ROLE_LABELS, selection),
        "source_key": source_key,
        "source_name": source_display_name(str(source_key) if source_key else None),
        "source_url": source_url,
        "authority_fit": authority,
        "authority_label": _bilingual(_AUTHORITY_LABELS, authority),
        "freshness": freshness,
        "freshness_label": _bilingual(_FRESHNESS_LABELS, freshness),
        "published_at": published_at,
        "retrieved_at": retrieved_at,
        "geography": claim.get("geography") or claim.get("geography_code"),
        "period": claim.get("period") or claim.get("period_key"),
        "unit": claim.get("unit"),
        "value": claim.get("value"),
        "statement": claim.get("statement") or claim.get("text"),
        "quality_state": evaluation.get("quality_state"),
        "quality_score": evaluation.get("quality_score"),
        "document_id": claim.get("document_id"),
        "chunk_id": claim.get("chunk_id"),
        "provenance_kind": provenance_kind,
        "provenance_label": _bilingual(_PROVENANCE_LABELS, provenance_kind),
        "selection_reason": _selection_reason(
            evaluation=evaluation,
            conflict=conflict,
            source_key=str(source_key) if source_key else None,
            claim_type=str(evaluation.get("claim_type") or ""),
        ),
        "selection_reason_codes": list(evaluation.get("selection_reason_codes") or []),
        "official_validated": official_validated,
    }


def _conflict_view(
    conflict: Mapping[str, Any],
    evaluations_by_id: Mapping[str, Mapping[str, Any]],
    claims_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    status = str(conflict.get("status") or "").upper()
    candidates = []
    for eid in conflict.get("candidates") or []:
        eid_s = str(eid)
        ev = evaluations_by_id.get(eid_s) or {}
        claim = claims_by_id.get(eid_s) or {}
        candidates.append(
            {
                "evidence_id": eid_s,
                "source_key": ev.get("source_key") or claim.get("source_key"),
                "source_name": source_display_name(
                    str(ev.get("source_key") or claim.get("source_key") or "") or None
                ),
                "value": claim.get("value"),
                "period": conflict.get("period") or claim.get("period"),
                "geography": conflict.get("geography") or claim.get("geography"),
                "unit": conflict.get("unit") or claim.get("unit"),
                "published_at": ev.get("published_at") or claim.get("published_at"),
                "authority_fit": ev.get("authority_fit"),
                "authority_label": _bilingual(
                    _AUTHORITY_LABELS, str(ev.get("authority_fit") or "")
                ),
                "quality_state": ev.get("quality_state"),
                "quality_score": ev.get("quality_score"),
                "role": ev.get("selection_status"),
                "role_label": _bilingual(_ROLE_LABELS, str(ev.get("selection_status") or "")),
                "is_preferred": eid_s == conflict.get("preferred_evidence_ref")
                and status == "RESOLVED_PREFERRED_SOURCE",
            }
        )
    return {
        "conflict_group_id": conflict.get("conflict_group_id"),
        "status": status,
        "resolved": status == "RESOLVED_PREFERRED_SOURCE",
        "unresolved": status == "UNRESOLVED",
        "metric": conflict.get("metric"),
        "period": conflict.get("period"),
        "geography": conflict.get("geography"),
        "unit": conflict.get("unit"),
        "values": list(conflict.get("values") or []),
        "preferred_evidence_ref": conflict.get("preferred_evidence_ref")
        if status == "RESOLVED_PREFERRED_SOURCE"
        else None,
        "explanation": conflict.get("explanation") or "",
        "unresolved_message": {
            "en": "Conflicting evidence remains unresolved.",
            "ar": "يبقى التعارض في الأدلة غير محسوم.",
        }
        if status == "UNRESOLVED"
        else None,
        "candidates": candidates,
    }


def project_research_quality_observability(
    research_context: Mapping[str, Any] | None,
    *,
    top_level_claims: Sequence[Any] | None = None,
) -> dict[str, Any] | None:
    """Build additive UI projection from persisted research_context quality."""
    if not isinstance(research_context, Mapping):
        return None
    quality = research_context.get("research_quality")
    if not isinstance(quality, Mapping) or not quality:
        return None

    context_claims = list(research_context.get("claims") or [])
    claims_by_id = _evidence_index(context_claims)
    top_claims = [_as_dict(c) for c in (top_level_claims or [])]

    evaluations = [
        _as_dict(e) for e in (quality.get("evaluations") or []) if isinstance(e, Mapping)
    ]
    evaluations_by_id = {
        str(e.get("evidence_id")): e for e in evaluations if e.get("evidence_id")
    }
    conflicts = [
        _as_dict(c) for c in (quality.get("conflicts") or []) if isinstance(c, Mapping)
    ]
    preferred_ids = [str(x) for x in (quality.get("preferred_evidence_ids") or [])]

    conflict_by_eid: dict[str, dict[str, Any]] = {}
    for conflict in conflicts:
        for eid in conflict.get("candidates") or []:
            conflict_by_eid[str(eid)] = conflict

    evidence_cards = [
        _project_evidence_card(
            evidence_id=eid,
            evaluation=evaluation,
            claim=claims_by_id.get(eid),
            conflict=conflict_by_eid.get(eid),
        )
        for eid, evaluation in evaluations_by_id.items()
    ]

    unresolved_eids = {
        str(eid)
        for conflict in conflicts
        if str(conflict.get("status") or "").upper() == "UNRESOLVED"
        for eid in (conflict.get("candidates") or [])
    }

    preferred = [
        c
        for c in evidence_cards
        if (c["evidence_id"] in preferred_ids or c["role"] == "PREFERRED")
        and c["evidence_id"] not in unresolved_eids
    ]
    preferred_id_set = {c["evidence_id"] for c in preferred}
    alternates = [
        c
        for c in evidence_cards
        if c["evidence_id"] not in preferred_id_set
        and c["role"] not in {"REJECTED_INELIGIBLE", "REJECTED_AI_ASSUMPTION"}
    ]

    claim_rows: list[dict[str, Any]] = []
    consumed: set[str] = set()

    for conflict in conflicts:
        view = _conflict_view(conflict, evaluations_by_id, claims_by_id)
        pref = None
        if view["preferred_evidence_ref"] and not view["unresolved"]:
            pref = next(
                (c for c in evidence_cards if c["evidence_id"] == view["preferred_evidence_ref"]),
                None,
            )
        cand_ids = {c["evidence_id"] for c in view["candidates"]}
        alts = [
            c
            for c in evidence_cards
            if c["evidence_id"] in cand_ids
            and (pref is None or c["evidence_id"] != pref["evidence_id"])
        ]
        statement = (pref or {}).get("statement") if pref else None
        if not statement and alts:
            statement = alts[0].get("statement")
        reason_source = pref or (alts[0] if alts else None)
        status = "unresolved" if view["unresolved"] else "conflict"
        claim_rows.append(
            {
                "claim_key": f"conflict:{view.get('conflict_group_id')}",
                "statement": statement,
                "claim_type": quality.get("claim_type"),
                "status": status,
                "status_label": _bilingual(_STATUS_LABELS, status),
                "preferred_evidence": None if view["unresolved"] else pref,
                "alternate_evidence": alts,
                "conflict": view,
                "selection_reason": (reason_source or {}).get("selection_reason")
                or _selection_reason(
                    evaluation=None,
                    conflict=conflict,
                    source_key=None,
                    claim_type=str(quality.get("claim_type") or ""),
                ),
            }
        )
        consumed.update(str(x) for x in (conflict.get("candidates") or []))

    for card in evidence_cards:
        if card["evidence_id"] in consumed:
            continue
        if card["role"] != "PREFERRED" and card["evidence_id"] not in preferred_id_set:
            continue
        status = _claim_status(
            evaluation=evaluations_by_id.get(card["evidence_id"]),
            conflict=conflict_by_eid.get(card["evidence_id"]),
        )
        claim_rows.append(
            {
                "claim_key": f"evidence:{card['evidence_id']}",
                "statement": card.get("statement"),
                "claim_type": quality.get("claim_type"),
                "status": status,
                "status_label": _bilingual(_STATUS_LABELS, status),
                "preferred_evidence": card,
                "alternate_evidence": [
                    a
                    for a in alternates
                    if a["evidence_id"] != card["evidence_id"]
                    and a.get("period") == card.get("period")
                    and a.get("geography") == card.get("geography")
                ],
                "conflict": None,
                "selection_reason": card.get("selection_reason"),
            }
        )

    if top_claims:
        for row in claim_rows:
            if row.get("statement"):
                continue
            for tc in top_claims:
                stmt = tc.get("statement")
                if stmt:
                    row["statement"] = stmt
                    break

    summary = {
        "preferred_count": len(preferred_id_set),
        "alternate_count": len({c["evidence_id"] for c in alternates}),
        "unresolved_conflict_count": sum(
            1 for c in conflicts if str(c.get("status") or "").upper() == "UNRESOLVED"
        ),
        "resolved_conflict_count": sum(
            1
            for c in conflicts
            if str(c.get("status") or "").upper() == "RESOLVED_PREFERRED_SOURCE"
        ),
        "stale_count": sum(
            1 for e in evaluations if str(e.get("freshness") or "").upper() == "STALE"
        ),
        "unknown_freshness_count": sum(
            1 for e in evaluations if str(e.get("freshness") or "").upper() == "UNKNOWN"
        ),
        "low_quality_count": sum(
            1 for e in evaluations if str(e.get("quality_state") or "").upper() == "LOW"
        ),
        "official_source_count": sum(1 for c in preferred if c.get("official_validated")),
        "total_evaluated": len(evaluations),
    }

    return {
        "observability_version": OBSERVABILITY_VERSION,
        "policy_version": quality.get("policy_version"),
        "claim_type": quality.get("claim_type"),
        "as_of": quality.get("as_of"),
        "summary": summary,
        "claims": claim_rows,
        "preferred_evidence": preferred,
        "alternate_evidence": alternates,
        "conflicts": [
            _conflict_view(c, evaluations_by_id, claims_by_id) for c in conflicts
        ],
        "evidence": evidence_cards,
    }


def attach_observability_to_research_context(
    research_context: Any,
    *,
    top_level_claims: Sequence[Any] | None = None,
) -> Any:
    """Return research_context with additive research_quality_observability field."""
    if not isinstance(research_context, dict):
        return research_context
    projection = project_research_quality_observability(
        research_context, top_level_claims=top_level_claims
    )
    if projection is None:
        return research_context
    out = dict(research_context)
    out["research_quality_observability"] = projection
    return out
