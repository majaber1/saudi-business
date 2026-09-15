"""Research service — Knowledge-first, then MCP/connector live fetch."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from ai_engine.research.planner import build_research_plan
from ai_engine.research.schemas import ResearchClaim, ResearchPlan, ResearchResult

logger = logging.getLogger(__name__)


def _trace(name: str, metadata: dict[str, Any] | None = None) -> None:
    """Best-effort Langfuse observation; never raises."""
    try:
        from ai_engine.config import get_langfuse

        lf = get_langfuse()
        if lf is None:
            return
        if hasattr(lf, "start_as_current_span"):
            with lf.start_as_current_span(name=name, metadata=metadata or {}):
                pass
        elif hasattr(lf, "trace"):
            lf.trace(name=name, metadata=metadata or {})
    except Exception as exc:  # noqa: BLE001
        logger.debug("langfuse research trace skipped: %s", exc)


def _knowledge_retrieve(
    *,
    owner_id: int | None,
    query: str,
    source_key: str,
    db: Any | None,
    study_id: str | None = None,
) -> list[ResearchClaim]:
    if owner_id is None or db is None:
        return []
    try:
        from backend.app.services.knowledge_service import retrieve_evidence
    except ImportError:
        try:
            from app.services.knowledge_service import retrieve_evidence  # type: ignore
        except ImportError:
            return []

    try:
        pack = retrieve_evidence(
            db,
            owner_id=int(owner_id),
            query=query,
            study_id=study_id,
            top_k=6,
            query_profile={"source_key": source_key},
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("knowledge retrieve skipped: %s", exc)
        return []

    claims: list[ResearchClaim] = []
    for cite in (pack or {}).get("citations") or []:
        if not isinstance(cite, dict):
            continue
        statement = str(
            cite.get("claim") or cite.get("content") or cite.get("snippet") or ""
        ).strip()
        if not statement:
            continue
        source = str(cite.get("source") or "")
        conf = float(cite.get("confidence") or 0.7)
        claims.append(
            ResearchClaim(
                statement=statement[:500],
                source_type=(
                    "official"
                    if "external" in source or source_key in statement.lower()
                    else "document"
                ),
                source_url=cite.get("source_url") or cite.get("url"),
                confidence=min(0.9, max(0.5, conf)),
                source_key=source_key,
                from_knowledge=True,
                document_id=(
                    str(cite.get("document_id")) if cite.get("document_id") else None
                ),
                chunk_id=str(cite.get("chunk_id")) if cite.get("chunk_id") else None,
                origin="knowledge",
            )
        )
    if not claims:
        for hit in (pack or {}).get("hits") or []:
            if not isinstance(hit, dict):
                continue
            content = str(hit.get("content") or "").strip()
            if not content:
                continue
            claims.append(
                ResearchClaim(
                    statement=content[:500],
                    source_type="document",
                    confidence=float(hit.get("score") or 0.6),
                    source_key=source_key,
                    from_knowledge=True,
                    document_id=(
                        str(hit.get("document_id")) if hit.get("document_id") else None
                    ),
                    chunk_id=str(hit.get("chunk_id")) if hit.get("chunk_id") else None,
                    origin="knowledge",
                )
            )
    return claims


def _claims_from_mcp_documents(
    source_key: str, documents: list[dict[str, Any]]
) -> list[ResearchClaim]:
    retrieved = datetime.now(timezone.utc).date().isoformat()
    claims: list[ResearchClaim] = []
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        title = str(doc.get("title") or doc.get("source_name") or source_key).strip()
        preview = str(
            doc.get("content")
            or doc.get("content_preview")
            or ""
        ).strip()
        url = doc.get("canonical_url") or doc.get("url")
        statement = f"{title}: {preview}" if preview else title
        if not statement:
            continue
        # Commercial discovery needs longer statements for competitor name extraction.
        limit = 2500 if source_key == "commercial_discovery" else 500
        meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        claims.append(
            ResearchClaim(
                statement=statement[:limit],
                source_type="official" if source_key in {"gastat", "misa"} else "document",
                source_url=url,
                retrieved_date=retrieved,
                confidence=float(doc.get("confidence") or 0.85),
                metric_key=title,
                source_key=source_key,
                document_id=str(doc.get("source_id") or doc.get("id") or "") or None,
                origin="research",
                geography=str(doc.get("geography") or "") or None,
            )
        )
        # Stash competitor_name on statement when present in metadata (via title already)
        _ = meta
    return claims


def _claims_from_typed_docs(source_key: str, typed_docs: list[Any]) -> list[ResearchClaim]:
    """Build richer claims from normalized SourceDocument objects."""
    retrieved = datetime.now(timezone.utc).date().isoformat()
    claims: list[ResearchClaim] = []
    for doc in typed_docs or []:
        title = str(getattr(doc, "title", None) or source_key)
        content = str(getattr(doc, "content", None) or "")
        url = getattr(doc, "canonical_url", None) or getattr(doc, "url", None)
        meta = getattr(doc, "metadata", None) or {}
        if not isinstance(meta, dict):
            meta = {}
        competitor_name = meta.get("competitor_name")
        statement = f"{title}: {content}" if content else title
        if competitor_name and competitor_name not in statement:
            statement = f"Competitor / local venue evidence: {competitor_name}. {statement}"
        # Preserve structured numeric observations for band derivation
        if meta.get("metric") is not None and meta.get("value") is not None:
            statement = (
                f"{meta.get('evidence_kind') or 'numeric'} observation: "
                f"{meta.get('metric')} = {meta.get('value')} {meta.get('unit') or 'SAR'}. "
                f"{statement}"
            )
        limit = 2500 if source_key == "commercial_discovery" else 800
        claims.append(
            ResearchClaim(
                statement=statement[:limit],
                source_type="official" if source_key in {"gastat", "misa"} else "document",
                source_url=str(url) if url else None,
                retrieved_date=retrieved,
                confidence=float(getattr(doc, "confidence", None) or 0.7),
                metric_key=str(meta.get("metric") or title),
                source_key=source_key,
                document_id=str(getattr(doc, "source_id", None) or "") or None,
                origin="research",
                geography=str(getattr(doc, "geography", None) or "") or None,
            )
        )
    return claims


def _live_fetch(
    source_key: str,
    query: str | None = None,
    **fetch_kwargs: Any,
) -> tuple[list[ResearchClaim], dict[str, Any], list[Any]]:
    """Fetch via MCP boundary. Returns claims, attempt metadata, typed docs for ingest."""
    try:
        from backend.app.integrations.mcp.boundary import (
            connector_for_key,
            source_status_payload,
        )
    except ImportError:
        from app.integrations.mcp.boundary import (  # type: ignore
            connector_for_key,
            source_status_payload,
        )

    attempt: dict[str, Any] = {
        "source_key": source_key,
        "at": datetime.now(timezone.utc).isoformat(),
        "path": "mcp_live",
    }
    status = source_status_payload(source_key)
    attempt["status"] = {
        "ok": status.get("ok"),
        "health": status.get("status"),
        "detail": status.get("detail"),
        "connector_id": status.get("connector_id"),
    }
    health = str(status.get("status") or "").lower()
    if health in {"unavailable", "disabled", "unknown"}:
        attempt["outcome"] = "unavailable"
        return [], attempt, []

    typed_docs: list[Any] = []
    try:
        conn = connector_for_key(source_key)
        typed_docs = list(conn.retrieve(query=query, **fetch_kwargs) or [])
    except Exception as exc:  # noqa: BLE001
        attempt["outcome"] = "fetch_failed"
        attempt["error"] = str(exc)
        return [], attempt, []

    claims = _claims_from_typed_docs(source_key, typed_docs)
    attempt["fetch_ok"] = True
    attempt["outcome"] = "ok" if claims else "empty"
    attempt["claim_count"] = len(claims)
    attempt["document_count"] = len(typed_docs)
    if fetch_kwargs:
        attempt["fetch_kwargs"] = {
            k: fetch_kwargs[k]
            for k in ("city", "district", "sector", "missing_keys", "archetype")
            if k in fetch_kwargs
        }
    return claims, attempt, typed_docs


def _maybe_ingest(
    *,
    db: Any | None,
    owner_id: int | None,
    typed_docs: list[Any],
) -> int:
    if not db or owner_id is None or not typed_docs:
        return 0
    try:
        from backend.app.integrations.sources.knowledge_adapter import (
            ingest_source_document,
        )
    except ImportError:
        try:
            from app.integrations.sources.knowledge_adapter import (  # type: ignore
                ingest_source_document,
            )
        except ImportError:
            return 0

    ingested = 0
    for doc in typed_docs:
        try:
            ingest_source_document(db, owner_id=int(owner_id), document=doc)
            ingested += 1
        except Exception as exc:  # noqa: BLE001
            logger.info("knowledge ingest skipped: %s", exc)
    return ingested


def claims_from_knowledge_context(
    knowledge_context: dict[str, Any] | None,
) -> list[ResearchClaim]:
    """Lift existing Evidence Pack citations into research claims."""
    if not knowledge_context:
        return []
    claims: list[ResearchClaim] = []
    for cite in knowledge_context.get("citations") or []:
        if not isinstance(cite, dict):
            continue
        statement = str(cite.get("claim") or cite.get("content") or "").strip()
        if not statement:
            continue
        claims.append(
            ResearchClaim(
                statement=statement[:500],
                source_type="document",
                source_url=cite.get("source_url"),
                confidence=float(cite.get("confidence") or 0.65),
                from_knowledge=True,
                source_key="knowledge_context",
            )
        )
    return claims


def _persist_research_run(
    *,
    db: Any | None,
    owner_id: int | None,
    result: ResearchResult,
    project_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """Best-effort Phase 8C.1 dual-write. Never raises into the study path.

    Import policy (Phase 8C.1): prefer the canonical runtime path
    ``app.services...`` (``sys.path`` includes ``backend/`` under CI and the
    FastAPI process). The ``backend.app...`` fallback exists only for scripts
    that put the repo root on ``PYTHONPATH`` without ``backend/``. Both resolve
    to the same module object when ``backend/`` is already on ``sys.path``;
    we never import both ORM registries.
    """
    if db is None or owner_id is None:
        return
    try:
        try:
            from app.services.research_persistence_service import (  # type: ignore
                persist_research_result,
            )
        except ImportError:  # pragma: no cover - script/layout fallback only
            from backend.app.services.research_persistence_service import (
                persist_research_result,
            )

        persist_research_result(
            db,
            study_id=str(result.plan.study_id),
            owner_id=int(owner_id),
            result=result,
            user_id=user_id or str(owner_id),
            project_id=project_id,
            research_type=(
                "market_research"
                if isinstance(getattr(result, "market_research", None), dict)
                and result.market_research
                else "gap_research"
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("research run persistence skipped: %s", exc)


def execute_research(
    plan: ResearchPlan,
    *,
    owner_id: int | None = None,
    db: Any | None = None,
    knowledge_context: dict[str, Any] | None = None,
    project_id: str | None = None,
    user_id: str | None = None,
    sector: str = "",
    geography: str = "Saudi Arabia",
    business_idea: str = "",
) -> ResearchResult:
    """
    Knowledge-first research execution.

    Order per source: Knowledge retrieve → if thin, MCP live fetch → ingest.
    Blocked sources are recorded but never fail the study.
    """
    _trace(
        "phase8a_research_execute",
        {"study_id": plan.study_id, "sources": [s.source_key for s in plan.sources]},
    )

    claims: list[ResearchClaim] = []
    attempts: list[dict[str, Any]] = []
    blocked: list[str] = []
    unavailable: list[str] = []
    errors: list[str] = []
    knowledge_hits = 0
    live_fetches = 0

    seed = claims_from_knowledge_context(knowledge_context)
    if seed:
        knowledge_hits += len(seed)
        claims.extend(seed)
        attempts.append(
            {
                "source_key": "knowledge_context",
                "outcome": "knowledge_context_seed",
                "claim_count": len(seed),
                "path": "knowledge",
            }
        )

    query = " | ".join(plan.queries) if plan.queries else "Saudi Arabia official statistics"

    for src in plan.sources:
        if src.blocked:
            blocked.append(src.source_key)
            attempts.append(
                {
                    "source_key": src.source_key,
                    "outcome": "blocked",
                    "reason": src.block_reason,
                    "path": "skipped",
                }
            )
            continue

        k_claims = _knowledge_retrieve(
            owner_id=owner_id,
            query=f"{query} {src.source_key}",
            source_key=src.source_key,
            db=db,
            study_id=plan.study_id,
        )
        # Commercial discovery must always attempt live multi-source search for depth.
        # Knowledge hits alone are not sufficient research breadth for competitors/location.
        always_live = src.source_key == "commercial_discovery"
        if k_claims and not always_live:
            knowledge_hits += len(k_claims)
            claims.extend(k_claims)
            attempts.append(
                {
                    "source_key": src.source_key,
                    "outcome": "knowledge_hit",
                    "claim_count": len(k_claims),
                    "path": "knowledge",
                }
            )
            continue
        if k_claims and always_live:
            knowledge_hits += len(k_claims)
            claims.extend(k_claims)
            attempts.append(
                {
                    "source_key": src.source_key,
                    "outcome": "knowledge_hit_plus_live",
                    "claim_count": len(k_claims),
                    "path": "knowledge",
                }
            )

        try:
            # Prefer multi-query commercial depth when available
            live_query = query
            fetch_kwargs: dict[str, Any] = {}
            if src.source_key == "commercial_discovery":
                if plan.queries:
                    live_query = " | ".join(plan.queries[:6])
                # Pass geography tokens so evidence-class strategy can seed catalogs
                geo_text = f"{geography or ''} {live_query or ''}"
                try:
                    from app.integrations.sources.commercial_discovery import (
                        infer_city_district,
                    )
                except ImportError:
                    try:
                        from backend.app.integrations.sources.commercial_discovery import (
                            infer_city_district,
                        )
                    except ImportError:
                        infer_city_district = None  # type: ignore
                if infer_city_district:
                    c, d = infer_city_district(geo_text)
                    if c:
                        fetch_kwargs["city"] = c
                    if d:
                        fetch_kwargs["district"] = d
                if sector:
                    fetch_kwargs["sector"] = sector
                if business_idea:
                    fetch_kwargs.setdefault("sector", business_idea)
            live_claims, attempt, typed_docs = _live_fetch(
                src.source_key, query=live_query, **fetch_kwargs
            )
            attempts.append(attempt)
            if attempt.get("outcome") in {"unavailable", "fetch_failed"}:
                unavailable.append(src.source_key)
                if attempt.get("error"):
                    errors.append(f"{src.source_key}: {attempt['error']}")
            elif live_claims:
                live_fetches += 1
                claims.extend(live_claims)
                _maybe_ingest(db=db, owner_id=owner_id, typed_docs=typed_docs)
            elif attempt.get("outcome") == "empty":
                unavailable.append(src.source_key)
        except Exception as exc:  # noqa: BLE001
            unavailable.append(src.source_key)
            errors.append(f"{src.source_key}: {exc}")
            attempts.append(
                {
                    "source_key": src.source_key,
                    "outcome": "error",
                    "error": str(exc),
                    "path": "mcp_live",
                }
            )

    live_sources = [s for s in plan.sources if not s.blocked]
    if claims:
        status: str = "partial" if unavailable else "complete"
    elif blocked and not live_sources:
        status = "blocked"
    elif unavailable and not claims:
        status = "failed"
    else:
        status = "partial" if attempts else "failed"

    # Phase 8B — Controlled Market Research over collected official/document evidence.
    # Never invents competitors/prices; never opens arbitrary URLs.
    market_payload: dict[str, Any] | None = None
    try:
        from ai_engine.research.market.service import (
            evidence_items_from_research_claims,
            execute_market_research,
            market_result_to_research_claims,
        )

        idea = business_idea or (" | ".join(plan.gaps[:3]) if plan.gaps else "")
        market = execute_market_research(
            study_id=plan.study_id,
            business_idea=idea,
            sector=sector or "",
            geography=geography or "Saudi Arabia",
            gaps=list(plan.gaps),
            evidence_items=evidence_items_from_research_claims(claims),
            use_cache=True,
        )
        market_payload = market.to_public_dict()
        market_claims = market_result_to_research_claims(market)
        if market_claims:
            claims.extend(market_claims)
        attempts.append(
            {
                "source_key": "market_research",
                "outcome": str(market.status),
                "claim_count": len(market_claims),
                "path": "market_8b",
                "duration_ms": market.duration_ms,
                "cache_hits": market.cache_hits,
                "conflicts": len(market.conflicts),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("market research skipped: %s", exc)
        errors.append(f"market_research: {exc}")
        attempts.append(
            {
                "source_key": "market_research",
                "outcome": "error",
                "error": str(exc),
                "path": "market_8b",
            }
        )

    # Phase 8C.2 — deterministic quality / ranking / conflict (no LLM, no extra I/O)
    research_quality_payload: dict[str, Any] | None = None
    try:
        from ai_engine.research.quality import (
            enrich_claims_with_quality,
            evaluate_research_quality,
        )

        question_text = " | ".join(
            [*(plan.gaps or []), *(plan.queries or [])]
        ).strip()
        quality = evaluate_research_quality(
            claims,
            question=question_text or None,
            db=db,
            owner_id=owner_id,
        )
        research_quality_payload = quality.to_public_dict()
        enriched = enrich_claims_with_quality(claims, quality)
        by_eid = {
            str(item.get("evidence_id")): item.get("research_quality")
            for item in enriched
            if isinstance(item, dict) and item.get("evidence_id")
        }
        for claim, enriched_item in zip(claims, enriched):
            rq = None
            if isinstance(enriched_item, dict):
                rq = enriched_item.get("research_quality")
            if rq is None:
                continue
            try:
                claim.research_quality = rq
            except Exception:  # noqa: BLE001
                pass
        _ = by_eid  # reserved for future claim-id alignment helpers
    except Exception as exc:  # noqa: BLE001
        logger.info("research quality evaluation skipped: %s", exc)
        errors.append(f"research_quality: {exc}")

    result = ResearchResult(
        plan=plan,
        status=status,  # type: ignore[arg-type]
        claims=claims,
        knowledge_hits=knowledge_hits,
        live_fetches=live_fetches,
        blocked_sources=blocked,
        unavailable_sources=unavailable,
        errors=errors,
        attempts=attempts,
        market_research=market_payload,
        research_quality=research_quality_payload,
    )
    _trace(
        "phase8a_research_result",
        {
            "study_id": plan.study_id,
            "status": result.status,
            "claim_count": len(claims),
            "blocked": blocked,
            "unavailable": unavailable,
            "market_status": (market_payload or {}).get("status"),
            "quality_claim_type": (research_quality_payload or {}).get("claim_type"),
        },
    )
    _persist_research_run(
        db=db,
        owner_id=owner_id,
        result=result,
        project_id=project_id,
        user_id=user_id,
    )
    return result


def research_gaps(
    *,
    study_id: str,
    gaps: list[str],
    owner_id: int | None = None,
    db: Any | None = None,
    queries: list[str] | None = None,
    knowledge_context: dict[str, Any] | None = None,
    project_id: str | None = None,
    user_id: str | None = None,
    sector: str = "",
    geography: str = "Saudi Arabia",
    business_idea: str = "",
) -> ResearchResult:
    plan = build_research_plan(
        study_id=study_id,
        gaps=gaps,
        queries=queries,
        sector=sector,
        geography=geography,
        business_idea=business_idea,
    )
    return execute_research(
        plan,
        owner_id=owner_id,
        db=db,
        knowledge_context=knowledge_context,
        project_id=project_id,
        user_id=user_id,
        sector=sector,
        geography=geography,
        business_idea=business_idea,
    )


def content_hash_for_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
