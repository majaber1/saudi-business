"""Phase 8C.1 — Persistent Research Runs + durable evidence references.

Persistence / audit only. Does not change Research Planner, Market Research,
or Evidence Trust Gate business logic.

Canonical import: ``from app.services.research_persistence_service import ...``
(uses the single shared SQLAlchemy Base via ``app.models``).
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger(__name__)

PERSIST_STATUSES = frozenset(
    {
        "PLANNED",
        "RUNNING",
        "COMPLETE",
        "PARTIAL",
        "NOT_FOUND",
        "SOURCE_UNAVAILABLE",
        "FAILED",
    }
)

_RESULT_STATUS_MAP = {
    "not_started": "PLANNED",
    "planned": "PLANNED",
    "searching": "RUNNING",
    "partial": "PARTIAL",
    "complete": "COMPLETE",
    "blocked": "SOURCE_UNAVAILABLE",
    "failed": "FAILED",
    "PLANNED": "PLANNED",
    "RUNNING": "RUNNING",
    "COMPLETE": "COMPLETE",
    "PARTIAL": "PARTIAL",
    "NOT_FOUND": "NOT_FOUND",
    "SOURCE_UNAVAILABLE": "SOURCE_UNAVAILABLE",
    "FAILED": "FAILED",
}

_PERSIST_TO_API = {
    "PLANNED": "planned",
    "RUNNING": "searching",
    "COMPLETE": "complete",
    "PARTIAL": "partial",
    "NOT_FOUND": "partial",
    "SOURCE_UNAVAILABLE": "blocked",
    "FAILED": "failed",
}


def map_result_status(status: Optional[str]) -> str:
    if not status:
        return "FAILED"
    key = str(status).strip()
    mapped = _RESULT_STATUS_MAP.get(key) or _RESULT_STATUS_MAP.get(key.lower())
    return mapped if mapped in PERSIST_STATUSES else "FAILED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _user_scope(owner_id: int, user_id: Optional[str] = None) -> str:
    return (user_id if user_id is not None else str(owner_id)).strip()


def _idempotency_key(
    *,
    source_key: Optional[str],
    document_id: Optional[str],
    chunk_id: Optional[str],
    official_url: Optional[str],
    evidence_type: Optional[str],
) -> str:
    raw = "|".join(
        [
            str(source_key or ""),
            str(document_id or ""),
            str(chunk_id or ""),
            str(official_url or ""),
            str(evidence_type or ""),
        ]
    )
    if len(raw) <= 240:
        return raw
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        try:
            return datetime.fromisoformat(text[:10])
        except ValueError:
            return None


def _knowledge_doc_exists(db: Session, *, owner_id: int, document_id: str) -> bool:
    return (
        db.query(models.KnowledgeDocument.id)
        .filter(
            models.KnowledgeDocument.id == document_id,
            models.KnowledgeDocument.owner_id == owner_id,
        )
        .first()
        is not None
    )


def _knowledge_chunk_exists(db: Session, *, owner_id: int, chunk_id: str) -> bool:
    return (
        db.query(models.KnowledgeChunk.id)
        .filter(
            models.KnowledgeChunk.id == chunk_id,
            models.KnowledgeChunk.owner_id == owner_id,
        )
        .first()
        is not None
    )


def _lookup_source_meta(
    db: Session, source_key: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    if not source_key:
        return None, None
    try:
        row = (
            db.query(models.KnowledgeSource)
            .filter(models.KnowledgeSource.key == source_key)
            .first()
        )
        if row is None:
            return None, None
        return row.name, getattr(row, "authority_type", None)
    except Exception:  # noqa: BLE001
        return None, None


def create_run(
    db: Session,
    *,
    study_id: str,
    owner_id: int,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    research_type: str = "gap_research",
    question: Optional[str] = None,
    plan_json: Optional[dict] = None,
    source_keys: Optional[Sequence[str]] = None,
    run_id: Optional[str] = None,
    status: str = "PLANNED",
) -> models.ResearchRun:
    """Create a ResearchRun. Idempotent when ``run_id`` already exists for owner."""
    rid = run_id or str(uuid.uuid4())
    scope = _user_scope(owner_id, user_id)
    existing = (
        db.query(models.ResearchRun)
        .filter(models.ResearchRun.id == rid, models.ResearchRun.owner_id == owner_id)
        .first()
    )
    if existing is not None:
        return existing

    mapped = map_result_status(status)
    row = models.ResearchRun(
        id=rid,
        study_id=str(study_id),
        project_id=str(project_id) if project_id else None,
        owner_id=int(owner_id),
        user_id=scope,
        research_type=research_type or "gap_research",
        question=question,
        status=mapped,
        plan_json=plan_json,
        source_keys_json=list(source_keys) if source_keys is not None else None,
        knowledge_reused=False,
        live_fetch_count=0,
        started_at=_utcnow() if mapped in {"RUNNING", "PLANNED"} else None,
    )
    db.add(row)
    db.flush()
    return row


def start_run(
    db: Session,
    *,
    run_id: str,
    owner_id: int,
) -> Optional[models.ResearchRun]:
    row = get_run(db, run_id=run_id, owner_id=owner_id)
    if row is None:
        return None
    row.status = "RUNNING"
    row.started_at = row.started_at or _utcnow()
    db.flush()
    return row


def update_run_status(
    db: Session,
    *,
    run_id: str,
    owner_id: int,
    status: str,
    sanitized_error_code: Optional[str] = None,
    sanitized_error_message: Optional[str] = None,
) -> Optional[models.ResearchRun]:
    row = get_run(db, run_id=run_id, owner_id=owner_id)
    if row is None:
        return None
    row.status = map_result_status(status)
    if sanitized_error_code is not None:
        row.sanitized_error_code = sanitized_error_code
    if sanitized_error_message is not None:
        row.sanitized_error_message = sanitized_error_message
    db.flush()
    return row


def complete_run(
    db: Session,
    *,
    run_id: str,
    owner_id: int,
    status: str,
    result_json: Optional[dict] = None,
    knowledge_reused: bool = False,
    live_fetch_count: int = 0,
    source_keys: Optional[Sequence[str]] = None,
    sanitized_error_code: Optional[str] = None,
    sanitized_error_message: Optional[str] = None,
) -> Optional[models.ResearchRun]:
    row = get_run(db, run_id=run_id, owner_id=owner_id)
    if row is None:
        return None
    row.status = map_result_status(status)
    row.result_json = result_json
    row.knowledge_reused = bool(knowledge_reused)
    row.live_fetch_count = int(live_fetch_count or 0)
    if source_keys is not None:
        row.source_keys_json = list(source_keys)
    row.completed_at = _utcnow()
    if sanitized_error_code is not None:
        row.sanitized_error_code = sanitized_error_code
    if sanitized_error_message is not None:
        row.sanitized_error_message = sanitized_error_message
    db.flush()
    return row


def fail_run(
    db: Session,
    *,
    run_id: str,
    owner_id: int,
    error_code: str = "RESEARCH_FAILED",
    error_message: str = "Research persistence recorded a failure.",
    result_json: Optional[dict] = None,
) -> Optional[models.ResearchRun]:
    return complete_run(
        db,
        run_id=run_id,
        owner_id=owner_id,
        status="FAILED",
        result_json=result_json,
        sanitized_error_code=error_code,
        sanitized_error_message=error_message,
    )


def get_run(
    db: Session,
    *,
    run_id: str,
    owner_id: int,
) -> Optional[models.ResearchRun]:
    return (
        db.query(models.ResearchRun)
        .filter(
            models.ResearchRun.id == run_id,
            models.ResearchRun.owner_id == owner_id,
        )
        .first()
    )


def list_runs_for_study(
    db: Session,
    *,
    study_id: str,
    owner_id: int,
    user_id: Optional[str] = None,
) -> List[models.ResearchRun]:
    q = db.query(models.ResearchRun).filter(
        models.ResearchRun.study_id == study_id,
        models.ResearchRun.owner_id == owner_id,
    )
    if user_id is not None:
        q = q.filter(models.ResearchRun.user_id == _user_scope(owner_id, user_id))
    return q.order_by(
        models.ResearchRun.created_at.desc(), models.ResearchRun.id.desc()
    ).all()


def load_latest_run(
    db: Session,
    *,
    study_id: str,
    owner_id: int,
    user_id: Optional[str] = None,
) -> Optional[models.ResearchRun]:
    runs = list_runs_for_study(
        db, study_id=study_id, owner_id=owner_id, user_id=user_id
    )
    return runs[0] if runs else None


def load_run_evidence(
    db: Session,
    *,
    run_id: str,
    owner_id: int,
) -> List[models.ResearchEvidenceRef]:
    return (
        db.query(models.ResearchEvidenceRef)
        .filter(
            models.ResearchEvidenceRef.research_run_id == run_id,
            models.ResearchEvidenceRef.owner_id == owner_id,
        )
        .order_by(models.ResearchEvidenceRef.created_at.asc())
        .all()
    )


def attach_evidence_refs(
    db: Session,
    *,
    run: models.ResearchRun,
    refs: Sequence[Dict[str, Any]],
) -> List[models.ResearchEvidenceRef]:
    """Attach evidence references idempotently within a run.

    Never invents document/chunk IDs. IDs that are not present in the Knowledge
    Layer for this owner are omitted from FK columns and recorded in
    provenance_json as unresolved_* when provided by the caller.
    """
    attached: List[models.ResearchEvidenceRef] = []
    for raw in refs:
        if not isinstance(raw, dict):
            continue
        source_key = raw.get("source_key")
        source_key_s = str(source_key).strip() if source_key else None
        official_url = raw.get("official_url") or raw.get("source_url")
        official_url_s = str(official_url).strip() if official_url else None
        evidence_type = raw.get("evidence_type") or raw.get("source_type")
        evidence_type_s = str(evidence_type).strip() if evidence_type else None

        raw_doc = raw.get("source_document_id") or raw.get("document_id")
        raw_chunk = raw.get("chunk_id")
        raw_doc_s = str(raw_doc).strip() if raw_doc else None
        raw_chunk_s = str(raw_chunk).strip() if raw_chunk else None

        resolved_doc: Optional[str] = None
        resolved_chunk: Optional[str] = None
        unresolved: Dict[str, Any] = {}

        if raw_doc_s:
            if _knowledge_doc_exists(db, owner_id=run.owner_id, document_id=raw_doc_s):
                resolved_doc = raw_doc_s
            else:
                unresolved["unresolved_document_id"] = raw_doc_s
        if raw_chunk_s:
            if _knowledge_chunk_exists(db, owner_id=run.owner_id, chunk_id=raw_chunk_s):
                resolved_chunk = raw_chunk_s
            else:
                unresolved["unresolved_chunk_id"] = raw_chunk_s

        if not any(
            [source_key_s, resolved_doc, resolved_chunk, official_url_s, unresolved]
        ):
            continue

        idem = raw.get("idempotency_key") or _idempotency_key(
            source_key=source_key_s,
            document_id=resolved_doc or raw_doc_s,
            chunk_id=resolved_chunk or raw_chunk_s,
            official_url=official_url_s,
            evidence_type=evidence_type_s,
        )

        existing = (
            db.query(models.ResearchEvidenceRef)
            .filter(
                models.ResearchEvidenceRef.research_run_id == run.id,
                models.ResearchEvidenceRef.owner_id == run.owner_id,
                models.ResearchEvidenceRef.idempotency_key == idem,
            )
            .first()
        )
        if existing is not None:
            attached.append(existing)
            continue

        source_name = raw.get("source_name")
        authority = raw.get("authority_type")
        if not source_name or not authority:
            reg_name, reg_auth = _lookup_source_meta(db, source_key_s)
            source_name = source_name or reg_name
            authority = authority or reg_auth

        provenance = dict(raw.get("provenance_json") or {})
        provenance.update(unresolved)
        if raw.get("statement"):
            provenance.setdefault("statement", str(raw["statement"])[:500])
        if raw.get("from_knowledge") is not None:
            provenance.setdefault("from_knowledge", bool(raw["from_knowledge"]))

        conf = raw.get("confidence")
        try:
            conf_f = float(conf) if conf is not None else None
        except (TypeError, ValueError):
            conf_f = None

        row = models.ResearchEvidenceRef(
            id=str(uuid.uuid4()),
            research_run_id=run.id,
            study_id=run.study_id,
            owner_id=run.owner_id,
            user_id=run.user_id,
            source_key=source_key_s,
            source_name=str(source_name) if source_name else None,
            source_document_id=resolved_doc,
            chunk_id=resolved_chunk,
            official_url=official_url_s,
            authority_type=str(authority) if authority else None,
            published_at=_parse_dt(raw.get("published_at")),
            retrieved_at=_parse_dt(
                raw.get("retrieved_at") or raw.get("retrieved_date")
            ),
            evidence_type=evidence_type_s,
            confidence=conf_f,
            provenance_json=provenance or None,
            idempotency_key=idem,
        )
        try:
            with db.begin_nested():
                db.add(row)
                db.flush()
        except IntegrityError:
            existing = (
                db.query(models.ResearchEvidenceRef)
                .filter(
                    models.ResearchEvidenceRef.research_run_id == run.id,
                    models.ResearchEvidenceRef.owner_id == run.owner_id,
                    models.ResearchEvidenceRef.idempotency_key == idem,
                )
                .first()
            )
            if existing is not None:
                attached.append(existing)
            continue
        attached.append(row)
    return attached


def evidence_refs_from_claims(claims: Sequence[Any]) -> List[Dict[str, Any]]:
    """Build attach payloads from ResearchClaim objects or claim dicts."""
    refs: List[Dict[str, Any]] = []
    for c in claims or []:
        if isinstance(c, dict):
            d = c
            from_knowledge = bool(d.get("from_knowledge"))
        else:
            d = {
                "statement": getattr(c, "statement", None),
                "source_type": getattr(c, "source_type", None),
                "source_url": getattr(c, "source_url", None),
                "retrieved_date": getattr(c, "retrieved_date", None),
                "confidence": getattr(c, "confidence", None),
                "source_key": getattr(c, "source_key", None),
                "document_id": getattr(c, "document_id", None),
                "chunk_id": getattr(c, "chunk_id", None),
                "metric_key": getattr(c, "metric_key", None),
                "origin": getattr(c, "origin", None),
            }
            from_knowledge = bool(getattr(c, "from_knowledge", False))
        refs.append(
            {
                "source_key": d.get("source_key"),
                "source_url": d.get("source_url"),
                "official_url": d.get("source_url") or d.get("official_url"),
                "document_id": d.get("document_id"),
                "chunk_id": d.get("chunk_id"),
                "evidence_type": d.get("source_type") or d.get("evidence_type"),
                "confidence": d.get("confidence"),
                "retrieved_date": d.get("retrieved_date"),
                "retrieved_at": d.get("retrieved_at"),
                "published_at": d.get("published_at"),
                "authority_type": d.get("authority_type"),
                "source_name": d.get("source_name"),
                "statement": d.get("statement"),
                "from_knowledge": from_knowledge,
                "provenance_json": {
                    "origin": d.get("origin"),
                    "metric_key": d.get("metric_key"),
                },
            }
        )
    return refs


def persist_research_result(
    db: Session,
    *,
    study_id: str,
    owner_id: int,
    result: Any,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    research_type: Optional[str] = None,
) -> Optional[models.ResearchRun]:
    """Atomically persist a ResearchResult + evidence refs.

    On any failure the transaction is rolled back and ``None`` is returned so
    the Study path is never left with a COMPLETE run missing its evidence graph.
    """
    try:
        plan = getattr(result, "plan", None)
        plan_dict = None
        if plan is not None:
            for meth in ("to_public_dict", "to_dict", "as_dict"):
                if hasattr(plan, meth):
                    plan_dict = getattr(plan, meth)()
                    break

        source_keys: List[str] = []
        sources = getattr(plan, "sources", None) if plan is not None else None
        if sources:
            source_keys = [
                getattr(s, "source_key", None)
                or (s.get("source_key") if isinstance(s, dict) else None)
                for s in sources
            ]
            source_keys = [k for k in source_keys if k]

        question = None
        if plan is not None and getattr(plan, "gaps", None):
            question = " | ".join(str(g) for g in plan.gaps[:5])
        elif plan is not None and getattr(plan, "queries", None):
            question = " | ".join(str(q) for q in plan.queries[:5])

        market = getattr(result, "market_research", None)
        rtype = research_type or (
            "market_research" if isinstance(market, dict) and market else "gap_research"
        )

        public: Dict[str, Any]
        if hasattr(result, "to_public_dict"):
            public = result.to_public_dict()
        elif isinstance(result, dict):
            public = dict(result)
        else:
            public = {}

        status_raw = getattr(result, "status", None) or public.get("status")
        claims = list(getattr(result, "claims", None) or public.get("claims") or [])
        mapped = map_result_status(str(status_raw))
        if mapped == "FAILED" and not claims:
            attempts = list(
                getattr(result, "attempts", None) or public.get("attempts") or []
            )
            if attempts and all(
                (a or {}).get("outcome")
                in {
                    "empty",
                    "blocked",
                    "knowledge_context_seed",
                    "unavailable",
                    "knowledge_hit",
                }
                for a in attempts
                if isinstance(a, dict)
            ):
                mapped = "NOT_FOUND"

        knowledge_hits = int(
            getattr(result, "knowledge_hits", 0) or public.get("knowledge_hits") or 0
        )
        live_fetches = int(
            getattr(result, "live_fetches", 0) or public.get("live_fetches") or 0
        )

        rid = run_id or str(uuid.uuid4())
        run = create_run(
            db,
            study_id=study_id,
            owner_id=owner_id,
            user_id=user_id,
            project_id=project_id,
            research_type=rtype,
            question=question,
            plan_json=plan_dict,
            source_keys=source_keys,
            run_id=rid,
            status="RUNNING",
        )
        start_run(db, run_id=run.id, owner_id=owner_id)

        refs = evidence_refs_from_claims(claims)
        attach_evidence_refs(db, run=run, refs=refs)

        complete_run(
            db,
            run_id=run.id,
            owner_id=owner_id,
            status=mapped,
            result_json=public,
            knowledge_reused=bool(knowledge_hits),
            live_fetch_count=live_fetches,
            source_keys=source_keys,
        )
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:  # noqa: BLE001
        logger.warning("research persistence failed (study unaffected): %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass
        return None


def run_to_api_projection(
    run: models.ResearchRun,
    *,
    evidence: Optional[Sequence[models.ResearchEvidenceRef]] = None,
) -> Dict[str, Any]:
    """Project a ResearchRun into existing API research_* fields."""
    result = run.result_json if isinstance(run.result_json, dict) else {}
    if isinstance(result, dict) and result.get("status"):
        status_api = result.get("status")
    else:
        status_api = _PERSIST_TO_API.get(run.status, "failed")

    if result:
        research_context = dict(result)
        research_context["persisted_run_id"] = run.id
    else:
        research_context = {
            "plan": run.plan_json,
            "status": status_api,
            "knowledge_hits": 1 if run.knowledge_reused else 0,
            "live_fetches": run.live_fetch_count,
            "attempts": [],
            "claims": [],
            "market_research": None,
            "persisted_run_id": run.id,
        }

    attempts: List[Any] = []
    market = None
    if isinstance(result, dict):
        attempts = list(result.get("attempts") or [])
        market = result.get("market_research")

    return {
        "research_status": status_api,
        "research_context": research_context,
        "research_attempts": attempts,
        "market_research_context": market,
        "research_run_id": run.id,
        "research_evidence_count": len(list(evidence or [])),
    }


def hydrate_research_into_state(
    db: Session,
    *,
    study_id: str,
    user_id: str,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """Prefer dedicated ResearchRun rows; leave snapshot values if none exist.

    Tenant isolation: owner_id derived from user_id (int) AND user_id string match.
    """
    try:
        owner_id = int(str(user_id).strip())
    except (TypeError, ValueError):
        return state

    run = load_latest_run(
        db, study_id=study_id, owner_id=owner_id, user_id=str(user_id)
    )
    if run is None:
        return state

    evidence = load_run_evidence(db, run_id=run.id, owner_id=owner_id)
    projection = run_to_api_projection(run, evidence=evidence)
    for key in (
        "research_status",
        "research_context",
        "research_attempts",
        "market_research_context",
    ):
        if projection.get(key) is not None:
            state[key] = projection[key]
    return state
