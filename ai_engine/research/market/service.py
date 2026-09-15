"""Phase 8B market research service — Research → Evidence → Knowledge → Insight."""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from ai_engine.research.market.competitor import research_competitors
from ai_engine.research.market.location_economics import extract_location_economics
from ai_engine.research.market.market_signal import research_market_signals
from ai_engine.research.market.operating_estimates import synthesize_operating_estimates
from ai_engine.research.market.planner import (
    build_market_plan,
    extract_market_context_from_state,
)
from ai_engine.research.market.pricing_signal import research_pricing_signals
from ai_engine.research.market.regulation import build_regulation_framework
from ai_engine.research.market.schemas import (
    EvidenceStatus,
    MarketInsight,
    MarketResearchResult,
)
from ai_engine.research.schemas import ResearchClaim

logger = logging.getLogger(__name__)

_MARKET_CACHE: dict[str, MarketResearchResult] = {}


def _make_cache_key(
    *,
    study_id: str,
    business_idea: str,
    sector: str,
    geography: str,
    research_types: list[str],
    evidence_fingerprint: str,
) -> str:
    raw = "|".join(
        [
            study_id,
            business_idea,
            sector,
            geography,
            ",".join(research_types),
            evidence_fingerprint,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _fingerprint_evidence(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for it in items:
        parts.append(
            f"{it.get('source_key')}:{it.get('document_id')}:{it.get('source_url')}:"
            f"{str(it.get('statement') or '')[:80]}"
        )
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def evidence_items_from_research_claims(claims: list[Any]) -> list[dict[str, Any]]:
    """Normalize ResearchClaim / Claim / dict into evidence item dicts."""
    import re

    items: list[dict[str, Any]] = []
    for c in claims or []:
        if isinstance(c, ResearchClaim):
            item = {
                "statement": c.statement,
                "source_type": c.source_type,
                "source_url": c.source_url,
                "source_key": c.source_key,
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "origin": c.origin,
                "confidence": c.confidence,
                "geography": c.geography,
            }
        elif isinstance(c, dict):
            item = dict(c)
        else:
            item = {
                "statement": str(getattr(c, "statement", "") or ""),
                "source_type": getattr(c, "source_type", None),
                "source_url": getattr(c, "source_url", None),
                "source_key": getattr(c, "source_key", None),
                "document_id": getattr(c, "document_id", None),
                "chunk_id": getattr(c, "chunk_id", None),
                "origin": getattr(c, "origin", None),
                "confidence": getattr(c, "confidence", 0.0),
                "geography": getattr(c, "geography", None),
            }
        stmt = str(item.get("statement") or "")
        if not item.get("competitor_name"):
            m = re.search(
                r"(?:Competitor\s*/\s*local venue evidence|Competitor POI)\s*:\s*([^\.\n:]+)",
                stmt,
                re.I,
            )
            if m:
                item["competitor_name"] = m.group(1).strip()
        if not item.get("evidence_kind"):
            low = stmt.lower()
            if "search exhaustion" in low:
                item["evidence_kind"] = "search_exhaustion"
            elif "competition density" in low:
                item["evidence_kind"] = "competition_density"
            elif "location economics / district" in low or low.startswith("location context:"):
                item["evidence_kind"] = "location_context"
            elif "competitor / local venue" in low or "competitor poi:" in low:
                item["evidence_kind"] = "competitor_poi"
            elif "observation:" in low:
                item["evidence_kind"] = "numeric_observation"
        # Recover structured numeric observation fields from adapter statements
        if item.get("metric") is None or item.get("value") is None:
            m = re.search(
                r"observation:\s*([^=\n]+?)\s*=\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([A-Za-z/%²0-9\-]*)",
                stmt,
                re.I,
            )
            if m:
                label = m.group(1).strip()
                try:
                    item["value"] = float(m.group(2).replace(",", ""))
                except ValueError:
                    pass
                unit = (m.group(3) or "").strip() or "SAR"
                item["unit"] = unit
                # Map label/unit heuristics to metric ids used by bands.
                # Order matters: salary/COGS/menu before generic SAR/month→rent.
                low_label = label.lower().strip()
                # Prefer the explicit metric token after "observation:" — never let the
                # evidence_class prefix (e.g. "salary_labor observation: staff_foh…")
                # reclassify staffing/density/COGS rows as salary.
                known_metrics = {
                    "salary_monthly_sar",
                    "staff_foh_guests_per",
                    "staff_boh_share_of_foh",
                    "staff_mgr_per_shift",
                    "dining_m2_per_seat",
                    "food_cost_pct",
                    "menu_item_sar",
                    "rent_monthly_sar",
                    "rent_sar_per_m2_year",
                    "store_area_m2",
                    "equipment_item_sar",
                    "opening_item_sar",
                    "fitout_sar_per_m2",
                    "fitout_total_sar",
                    "seats_capacity",
                    "operating_hours_day",
                    "input_cost_sar",
                }
                if low_label in known_metrics:
                    item["metric"] = low_label
                elif "rent_sar_per_m2" in low_label or "sar/m2/year" in unit.lower():
                    item["metric"] = "rent_sar_per_m2_year"
                elif any(
                    k in low_label
                    for k in (
                        "salary",
                        "wage",
                        "minimum_wage",
                        "statutory_minimum",
                        "راتب",
                    )
                ):
                    item["metric"] = "salary_monthly_sar"
                elif "rent_monthly" in low_label or (
                    "rent" in low_label
                    and unit.lower() in {"sar/month", "sar/mo", "sar"}
                ):
                    item["metric"] = "rent_monthly_sar"
                elif "store_area" in low_label or unit.lower() in {"m2", "m²"}:
                    item["metric"] = "store_area_m2"
                elif "menu" in low_label or low_label == "menu_item":
                    item["metric"] = "menu_item_sar"
                elif "equipment" in low_label:
                    item["metric"] = "equipment_item_sar"
                elif "opening" in low_label or "furniture" in low_label or "pos" in low_label:
                    item["metric"] = "opening_item_sar"
                elif "fitout" in low_label and "m2" in unit.lower():
                    item["metric"] = "fitout_sar_per_m2"
                elif "fitout" in low_label:
                    item["metric"] = "fitout_total_sar"
                elif "food_cost" in low_label or (
                    unit.lower() in {"percent", "%"} and "food" in low_label
                ):
                    item["metric"] = "food_cost_pct"
                elif unit.lower() in {"sar/month", "sar/mo"} and "rent" in low_label:
                    item["metric"] = "rent_monthly_sar"
                else:
                    # Use role_or_item / label as metric fallback for equipment package
                    item["metric"] = re.sub(r"\s+", "_", low_label)[:64]
                    if "espresso" in low_label or "grinder" in low_label or "machine" in low_label:
                        item["metric"] = "equipment_item_sar"
                    elif any(k in low_label for k in ("table", "chair", "pos", "register")):
                        item["metric"] = "opening_item_sar"
                # Recover role/item when adapters emitted it into the statement.
                rm = re.search(r"Role/item:\s*([^.\n]+)", stmt, re.I)
                if rm and not item.get("role_or_item"):
                    item["role_or_item"] = rm.group(1).strip()
        if item.get("metric") and item.get("value") is not None:
            item.setdefault("evidence_kind", "numeric_observation")
        items.append(item)
    return items


def market_result_to_research_claims(
    result: MarketResearchResult,
) -> list[ResearchClaim]:
    """Map verified market insights into ResearchClaim for Evidence Pack merge."""
    claims: list[ResearchClaim] = []
    for insight in result.insights:
        # Merge evidence-backed insights into study claims.
        # NOT_FOUND stays in market_research payload for transparency.
        if insight.status not in {"VERIFIED", "CONFLICT", "PARTIAL"}:
            continue
        if insight.status == "PARTIAL" and insight.research_type not in {
            "LOCATION",
            "PRICING",
            "COMPETITOR",
            "SECTOR_SIGNAL",
        }:
            continue
        source_type = "official" if insight.source_key in {"gastat", "misa"} else "document"
        if insight.status == "CONFLICT":
            source_type = "document"
        claims.append(
            ResearchClaim(
                statement=insight.insight,
                source_type=source_type,  # type: ignore[arg-type]
                source_url=insight.official_url,
                confidence=float(insight.confidence),
                metric_key=insight.research_type,
                source_key=insight.source_key,
                document_id=insight.document_id,
                chunk_id=insight.chunk_id,
                origin="market_research",
            )
        )
    return claims


def _build_insights(result: MarketResearchResult) -> list[MarketInsight]:
    insights: list[MarketInsight] = []

    for c in result.competitors:
        if not c.name and c.status == "NOT_FOUND":
            insights.append(
                MarketInsight(
                    insight="No sourced competitor evidence found (NOT_FOUND).",
                    research_type="COMPETITOR",
                    source="none",
                    official_url=None,
                    evidence_reference=c.evidence_reference,
                    confidence=0.0,
                    status="NOT_FOUND",
                )
            )
            continue
        if not c.name:
            continue
        insights.append(
            MarketInsight(
                insight=(
                    f"Competitor mention: {c.name} ({c.status})"
                    + (f" — {c.relevance_reason}" if c.relevance_reason else "")
                ),
                research_type="COMPETITOR",
                source=c.source_key or "evidence",
                official_url=c.source_url,
                evidence_reference=c.evidence_reference,
                confidence=c.confidence,
                status=c.status,
                source_key=c.source_key,
                document_id=c.document_id,
                chunk_id=c.chunk_id,
            )
        )

    for s in result.market_signals:
        insights.append(
            MarketInsight(
                insight=f"{s.metric}={s.value}" + (f" ({s.period})" if s.period else ""),
                research_type="SECTOR_SIGNAL",
                source=s.source,
                official_url=s.source_url,
                evidence_reference=s.evidence_reference,
                confidence=s.confidence,
                status=s.status,
                source_key=s.source_key,
                document_id=s.document_id,
                chunk_id=s.chunk_id,
            )
        )

    for p in result.pricing_signals:
        if p.status == "NOT_FOUND" or p.price is None:
            insights.append(
                MarketInsight(
                    insight="Pricing evidence not found (NOT_FOUND).",
                    research_type="PRICING",
                    source="none",
                    official_url=None,
                    evidence_reference=p.evidence_reference,
                    confidence=0.0,
                    status="NOT_FOUND",
                )
            )
            continue
        insights.append(
            MarketInsight(
                insight=f"Price signal: {p.item} = {p.price} {p.currency or ''}".strip(),
                research_type="PRICING",
                source=p.source_key or "evidence",
                official_url=p.source_url,
                evidence_reference=p.evidence_reference,
                confidence=p.confidence,
                status=p.status,
                source_key=p.source_key,
                document_id=p.document_id,
                chunk_id=p.chunk_id,
            )
        )

    for r in result.regulation_signals:
        insights.append(
            MarketInsight(
                insight=f"{r.authority}: {r.requirement}",
                research_type="REGULATION",
                source=r.source_key or r.authority,
                official_url=r.source_url,
                evidence_reference=r.source_reference,
                confidence=r.confidence,
                status=r.status,
                source_key=r.source_key,
            )
        )

    for loc in result.location_economics:
        if loc.status == "NOT_FOUND" or loc.factor == "none":
            insights.append(
                MarketInsight(
                    insight="Location economics evidence not found (NOT_FOUND).",
                    research_type="LOCATION",
                    source="none",
                    official_url=None,
                    evidence_reference=loc.evidence_reference,
                    confidence=0.0,
                    status="NOT_FOUND",
                )
            )
            continue
        insights.append(
            MarketInsight(
                insight=(
                    f"Location economics ({loc.factor}) @ {loc.geography}: "
                    f"{loc.value if loc.value is not None else (loc.notes or '')}"
                ),
                research_type="LOCATION",
                source=loc.source_key or "evidence",
                official_url=loc.source_url,
                evidence_reference=loc.evidence_reference,
                confidence=loc.confidence,
                status=loc.status,
                source_key=loc.source_key,
                document_id=loc.document_id,
                chunk_id=loc.chunk_id,
            )
        )

    for est in result.operating_estimates:
        if not isinstance(est, dict):
            continue
        insights.append(
            MarketInsight(
                insight=(
                    f"SYSTEM_ESTIMATE {est.get('key')}={est.get('value')} "
                    f"({est.get('geography')}, {est.get('as_of')})"
                ),
                research_type="PRICING"
                if str(est.get("key") or "") in {"avg_ticket", "food_cost_pct"}
                else "LOCATION"
                if "rent" in str(est.get("key") or "")
                else "SECTOR_SIGNAL",
                source="commercial_discovery",
                official_url=(est.get("source_urls") or [None])[0],
                evidence_reference=str(est.get("reasoning") or "")[:240],
                confidence=float(est.get("confidence") or 0.4),
                status="PARTIAL",
                source_key="commercial_discovery",
            )
        )

    for conflict in result.conflicts:
        insights.append(
            MarketInsight(
                insight=(
                    f"Conflict on {conflict.get('metric')} "
                    f"({conflict.get('period')}): values {conflict.get('values')}"
                ),
                research_type="SECTOR_SIGNAL",
                source=",".join(conflict.get("sources") or []),
                official_url=None,
                evidence_reference=";".join(conflict.get("evidence_references") or []),
                confidence=0.4,
                status="CONFLICT",
            )
        )

    return insights


def _overall_status(result: MarketResearchResult) -> EvidenceStatus:
    if result.conflicts:
        return "CONFLICT"
    statuses = [i.status for i in result.insights]
    if not statuses:
        return "NOT_FOUND"
    if any(s == "VERIFIED" for s in statuses) and any(
        s in {"NOT_FOUND", "PARTIAL", "NOT_VERIFIED"} for s in statuses
    ):
        return "PARTIAL"
    if all(s == "NOT_FOUND" for s in statuses):
        return "NOT_FOUND"
    if any(s == "VERIFIED" for s in statuses):
        return "VERIFIED"
    if any(s == "PARTIAL" for s in statuses):
        return "PARTIAL"
    return "NOT_VERIFIED"


def execute_market_research(
    *,
    study_id: str,
    business_idea: str = "",
    sector: str = "",
    geography: str = "Saudi Arabia",
    gaps: list[str] | None = None,
    evidence_items: list[dict[str, Any]] | None = None,
    use_cache: bool = True,
) -> MarketResearchResult:
    """
    Controlled market research over already-approved evidence (GASTAT/MISA/etc).

    Does not open arbitrary URLs. Does not invent competitors, prices, or market size.
    """
    started = time.perf_counter()
    plan = build_market_plan(
        study_id=study_id,
        business_idea=business_idea,
        sector=sector,
        geography=geography,
        gaps=gaps,
    )
    items = list(evidence_items or [])
    fp = _fingerprint_evidence(items)
    key = _make_cache_key(
        study_id=study_id,
        business_idea=business_idea,
        sector=sector,
        geography=geography,
        research_types=list(plan.research_types),
        evidence_fingerprint=fp,
    )
    if use_cache and key in _MARKET_CACHE:
        cached = _MARKET_CACHE[key]
        cached.cache_hits = int(cached.cache_hits or 0) + 1
        return cached

    attempts: list[dict[str, Any]] = [
        {
            "step": "plan",
            "research_types": list(plan.research_types),
            "selected_sources": list(plan.selected_sources),
            "placeholder_sources": list(plan.placeholder_sources),
        }
    ]

    competitors = []
    market_signals = []
    pricing_signals = []
    regulation_signals = []
    location_economics = []
    operating_estimates: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    if "COMPETITOR" in plan.research_types:
        competitors, c_status = research_competitors(
            business_idea=business_idea,
            sector=sector,
            geography=geography,
            evidence_items=items,
        )
        attempts.append(
            {"step": "competitors", "status": c_status, "count": len(competitors)}
        )

    if any(t in plan.research_types for t in ("SECTOR_SIGNAL", "MARKET_SIZE")):
        market_signals, conflicts, m_status = research_market_signals(items)
        attempts.append(
            {
                "step": "market_signals",
                "status": m_status,
                "count": len(market_signals),
                "conflicts": len(conflicts),
            }
        )

    if "PRICING" in plan.research_types:
        pricing_signals, p_status = research_pricing_signals(items)
        attempts.append(
            {"step": "pricing", "status": p_status, "count": len(pricing_signals)}
        )

    if "REGULATION" in plan.research_types:
        regulation_signals, r_status = build_regulation_framework(
            sector=sector, evidence_items=items
        )
        attempts.append(
            {
                "step": "regulation",
                "status": r_status,
                "count": len(regulation_signals),
            }
        )

    if "LOCATION" in plan.research_types:
        location_economics, loc_status = extract_location_economics(
            evidence_items=items, geography=geography
        )
        attempts.append(
            {
                "step": "location_economics",
                "status": loc_status,
                "count": len(location_economics),
            }
        )

    # Evidence-backed SYSTEM_ESTIMATE candidates (never invent without numerics)
    estimates = synthesize_operating_estimates(
        evidence_items=items, geography=geography
    )
    operating_estimates = [e.to_public_dict() for e in estimates]

    # Coverage recovery: targeted re-fetch for material numeric gaps (once)
    try:
        from ai_engine.research.evidence.coverage import (
            MATERIAL_NUMERIC_KEYS,
            validate_numeric_coverage,
        )
        from ai_engine.research.evidence.demand import derive_capacity_and_demand

        cov = validate_numeric_coverage(
            estimate_keys=[e.get("key") for e in operating_estimates if e.get("key")],
            required_keys=list(MATERIAL_NUMERIC_KEYS),
        )
        attempts.append(
            {
                "step": "numeric_coverage",
                "status": cov.get("status"),
                "gaps": cov.get("gaps"),
                "present": cov.get("present"),
            }
        )
        gaps = list(cov.get("gaps") or [])
        # daily_covers / working_capital are derived — don't treat as retrieval gaps first
        retrieval_gaps = [
            g
            for g in gaps
            if g
            not in {
                "daily_covers",
                "working_capital",
                "other_capex",
            }
        ]
        if retrieval_gaps:
            try:
                from ai_engine.research.service import _live_fetch

                recovery_query = (
                    f"{business_idea} {geography} "
                    + " ".join(retrieval_gaps[:6])
                )
                geo_bits = [p.strip() for p in (geography or "").split(",") if p.strip()]
                city = geo_bits[-2] if len(geo_bits) >= 2 else (geo_bits[0] if geo_bits else "")
                district = geo_bits[0] if len(geo_bits) >= 3 else ""
                live_claims, attempt, _docs = _live_fetch(
                    "commercial_discovery",
                    query=recovery_query,
                    city=city,
                    district=district,
                    sector=sector,
                    missing_keys=retrieval_gaps,
                    archetype="fnb" if "food" in (sector or "").lower() or "fnb" in (sector or "").lower() or "coffee" in (business_idea or "").lower() else None,
                )
                attempts.append({"step": "coverage_recovery_fetch", **attempt})
                if live_claims:
                    extra_items = evidence_items_from_research_claims(live_claims)
                    items = list(items) + extra_items
                    estimates = synthesize_operating_estimates(
                        evidence_items=items, geography=geography
                    )
                    operating_estimates = [e.to_public_dict() for e in estimates]
                    cov2 = validate_numeric_coverage(
                        estimate_keys=[
                            e.get("key") for e in operating_estimates if e.get("key")
                        ],
                        required_keys=list(MATERIAL_NUMERIC_KEYS),
                    )
                    attempts.append(
                        {
                            "step": "numeric_coverage_after_recovery",
                            "status": cov2.get("status"),
                            "gaps": cov2.get("gaps"),
                            "present": cov2.get("present"),
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                attempts.append(
                    {"step": "coverage_recovery_fetch", "status": "error", "error": str(exc)}
                )

        # CAPACITY vs DEMAND — never copy capacity into expected demand blindly
        dens = None
        for it in items:
            if isinstance(it, dict) and it.get("density_count") is not None:
                dens = int(it["density_count"])
                break
            stmt = str((it or {}).get("statement") or "") if isinstance(it, dict) else ""
            if "competition density" in stmt.lower():
                import re as _re

                m = _re.search(r"approximately\s+(\d+)", stmt, _re.I)
                if m:
                    dens = int(m.group(1))
                    break
        # seats/hours only from estimate or explicit evidence — never invent
        seats = None
        hours = None
        for e in operating_estimates:
            key = e.get("key")
            if key == "seats_capacity":
                try:
                    seats = float(e.get("base") or e.get("value"))
                except (TypeError, ValueError):
                    pass
            elif key == "operating_hours_day":
                try:
                    hours = float(e.get("base") or e.get("value"))
                except (TypeError, ValueError):
                    pass
        throughput = derive_capacity_and_demand(
            seats=seats,
            operating_hours=hours,
            competitor_density_count=dens,
        )
        attempts.append(
            {
                "step": "capacity_demand",
                "capacity": bool(throughput.get("capacity")),
                "demand": bool(throughput.get("demand")),
                "notes": throughput.get("notes"),
            }
        )
        demand = throughput.get("demand")
        if demand and not any(e.get("key") == "daily_covers" for e in operating_estimates):
            operating_estimates.append(
                {
                    "key": "daily_covers",
                    "value": str(demand.get("base")),
                    "low": str(demand.get("low")),
                    "base": str(demand.get("base")),
                    "high": str(demand.get("high")),
                    "currency": "",
                    "geography": geography,
                    "as_of": "",
                    "confidence": float(demand.get("confidence") or 0.4),
                    "reasoning": demand.get("derivation"),
                    "source_urls": [],
                    "provenance_class": "SYSTEM_ESTIMATE",
                    "estimate_basis": "DEMAND_ESTIMATE",
                    "capacity_estimate": throughput.get("capacity"),
                }
            )
    except Exception as exc:  # noqa: BLE001
        attempts.append({"step": "coverage_recovery", "status": "skipped", "error": str(exc)})

    if operating_estimates:
        attempts.append(
            {
                "step": "operating_estimates",
                "status": "PARTIAL",
                "count": len(operating_estimates),
                "keys": [e.get("key") for e in operating_estimates],
            }
        )

    result = MarketResearchResult(
        plan=plan,
        status="PARTIAL",
        competitors=competitors,
        market_signals=market_signals,
        pricing_signals=pricing_signals,
        regulation_signals=regulation_signals,
        location_economics=location_economics,
        operating_estimates=operating_estimates,
        conflicts=conflicts,
        attempts=attempts,
        knowledge_hits=sum(
            1 for i in items if i.get("from_knowledge") or i.get("document_id")
        ),
        live_fetches=sum(
            1
            for i in items
            if i.get("source_key") in {"gastat", "misa", "commercial_discovery"}
            and i.get("source_url")
        ),
        duration_ms=0.0,
    )
    result.insights = _build_insights(result)
    result.status = _overall_status(result)
    result.duration_ms = (time.perf_counter() - started) * 1000.0

    if use_cache:
        _MARKET_CACHE[key] = result
    return result


def execute_market_research_from_state(
    state: Any,
    *,
    research_claims: list[Any] | None = None,
    use_cache: bool = True,
) -> MarketResearchResult:
    ctx = extract_market_context_from_state(state)
    items = evidence_items_from_research_claims(research_claims or [])
    existing = getattr(state, "claims", None)
    if existing is None and isinstance(state, dict):
        existing = state.get("claims")
    if existing:
        items.extend(evidence_items_from_research_claims(list(existing)))
    return execute_market_research(
        study_id=str(ctx["study_id"]),
        business_idea=str(ctx["business_idea"]),
        sector=str(ctx["sector"]),
        geography=str(ctx["geography"]),
        gaps=list(ctx["gaps"]),
        evidence_items=items,
        use_cache=use_cache,
    )


def clear_market_cache() -> None:
    _MARKET_CACHE.clear()
