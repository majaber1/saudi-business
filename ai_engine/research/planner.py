"""Research Planner — maps study gaps to Phase 8A live / blocked sources."""

from __future__ import annotations

from typing import Any

from ai_engine.research.schemas import ResearchPlan, ResearchSourceRef

# Phase 8A live governed sources (post MISA merge). Monsha'at is blocked.
PHASE8A_LIVE_SOURCES: dict[str, dict[str, Any]] = {
    "gastat": {
        "connector_id": "live.gastat",
        "gap_keywords": (
            "inflation",
            "cpi",
            "gdp",
            "unemployment",
            "labor",
            "population",
            "statistics",
            "indicator",
            "macro",
            "economic indicator",
            "consumer price",
        ),
    },
    "misa": {
        "connector_id": "live.misa",
        "gap_keywords": (
            "investment",
            "fdi",
            "foreign direct",
            "investor",
            "license",
            "misa",
            "inflow",
            "capital inflow",
            "investment climate",
        ),
    },
    "commercial_discovery": {
        "connector_id": "live.commercial_discovery",
        "gap_keywords": (
            "competitor",
            "competition",
            "pricing",
            "price",
            "ticket",
            "menu",
            "rent",
            "location",
            "district",
            "footfall",
            "salary",
            "labor",
            "capex",
            "fit-out",
            "fitout",
            "cogs",
            "operating",
            "venue",
            "local business",
            "poi",
            "إيجار",
            "منافس",
            "موقع",
        ),
        # Always prefer live fetch for commercial depth (do not stop at knowledge hits).
        "always_live": True,
    },
}

BLOCKED_SOURCES: dict[str, dict[str, Any]] = {
    "monshaat": {
        "connector_id": "live.monshaat",
        "reason": "BLOCKED_EXTERNAL_REACHABILITY",
        "gap_keywords": (
            "sme",
            "msme",
            "monshaat",
            "small business",
            "medium enterprise",
            "entrepreneur",
        ),
    },
}

_LOCAL_ARCHETYPE_HINTS = (
    "fnb",
    "f&b",
    "food",
    "retail",
    "restaurant",
    "cafe",
    "café",
    "coffee",
    "clinic",
    "gym",
    "hotel",
    "salon",
    "shop",
)


def classify_gap(gap: str) -> list[str]:
    """Return source keys relevant to a gap string (may include blocked)."""
    text = (gap or "").lower()
    matched: list[str] = []
    for key, meta in PHASE8A_LIVE_SOURCES.items():
        if any(k in text for k in meta["gap_keywords"]):
            matched.append(key)
    for key, meta in BLOCKED_SOURCES.items():
        if any(k in text for k in meta["gap_keywords"]):
            matched.append(key)
    if not matched:
        matched = ["gastat", "misa"]
    return matched


def build_research_plan(
    *,
    study_id: str,
    gaps: list[str],
    queries: list[str] | None = None,
    sector: str = "",
    geography: str = "Saudi Arabia",
    business_idea: str = "",
) -> ResearchPlan:
    source_keys: list[str] = []
    for gap in gaps:
        for key in classify_gap(gap):
            if key not in source_keys:
                source_keys.append(key)

    if not source_keys and not gaps:
        source_keys = ["gastat", "misa", "commercial_discovery"]

    # Local/commercial studies always need commercial discovery depth.
    blob = " ".join([*(gaps or []), sector, business_idea, geography]).lower()
    if any(h in blob for h in _LOCAL_ARCHETYPE_HINTS) or "saudi arabia" in geography.lower():
        if "commercial_discovery" not in source_keys:
            # Prefer commercial when city/district or venue markers present
            if any(
                k in blob
                for k in (
                    "competitor",
                    "rent",
                    "location",
                    "district",
                    "pricing",
                    "ticket",
                    "riyadh",
                    "jeddah",
                    "cafe",
                    "fnb",
                    "retail",
                    *_LOCAL_ARCHETYPE_HINTS,
                )
            ):
                source_keys.append("commercial_discovery")

    sources: list[ResearchSourceRef] = []
    for key in source_keys:
        if key in BLOCKED_SOURCES:
            meta = BLOCKED_SOURCES[key]
            sources.append(
                ResearchSourceRef(
                    source_key=key,
                    connector_id=str(meta["connector_id"]),
                    reason=f"Gap matched blocked source {key}",
                    status="blocked",
                    blocked=True,
                    block_reason=str(meta["reason"]),
                )
            )
        else:
            meta = PHASE8A_LIVE_SOURCES[key]
            sources.append(
                ResearchSourceRef(
                    source_key=key,
                    connector_id=str(meta["connector_id"]),
                    reason=f"Phase 8A live source for gaps: {', '.join(gaps) or 'default'}",
                    status="planned",
                    blocked=False,
                )
            )

    plan_queries = list(queries or gaps or ["Saudi Arabia macroeconomic indicators"])
    # Multi-angle commercial queries for research depth (not a single shallow search)
    if any(s.source_key == "commercial_discovery" for s in sources):
        extras = [
            f"competitors and local venues {geography} {sector or business_idea}".strip(),
            f"commercial rent location economics {geography}",
            f"pricing ticket menu signals {geography} {sector or business_idea}".strip(),
            f"labor salary operating costs {sector or 'business'} Saudi Arabia",
        ]
        for q in extras:
            if q and q not in plan_queries:
                plan_queries.append(q)

    return ResearchPlan(
        study_id=study_id,
        gaps=list(gaps),
        sources=sources,
        queries=plan_queries,
        status="planned",
    )


def extract_gaps_from_state(state: Any) -> list[str]:
    """Derive research gaps from study profile / structured answers / claims."""
    gaps: list[str] = []

    if isinstance(state, dict):
        profile = state.get("profile") or {}
        answers = state.get("structured_answers") or {}
        existing_claims = state.get("claims") or []
        if isinstance(profile, dict):
            sector = str(profile.get("sector") or "").strip()
            archetype = str(profile.get("archetype") or "").strip()
            missing = list(profile.get("missing_information") or [])
            idea = str(profile.get("decision_goal") or "")
        else:
            sector = str(getattr(profile, "sector", "") or "").strip()
            archetype = str(getattr(profile, "archetype", "") or "").strip()
            missing = list(getattr(profile, "missing_information", None) or [])
            idea = str(getattr(profile, "decision_goal", "") or "")
    else:
        profile = getattr(state, "profile", None)
        answers = getattr(state, "structured_answers", None) or {}
        existing_claims = getattr(state, "claims", None) or []
        sector = str(getattr(profile, "sector", "") or "").strip() if profile else ""
        archetype = str(getattr(profile, "archetype", "") or "").strip() if profile else ""
        missing = list(getattr(profile, "missing_information", None) or []) if profile else []
        idea = str(getattr(profile, "decision_goal", "") or "") if profile else ""

    if sector:
        gaps.append(f"Sector market context for {sector} in Saudi Arabia")
    else:
        gaps.append("Saudi Arabia macroeconomic and investment context")

    if archetype and archetype != "unknown":
        gaps.append(f"Official indicators relevant to {archetype.replace('_', ' ')} ventures")

    city = ""
    district = ""
    if isinstance(answers, dict):
        city = str(
            answers.get("city")
            or answers.get("location")
            or answers.get("location_city")
            or ""
        ).strip()
        district = str(
            answers.get("district")
            or answers.get("neighborhood")
            or answers.get("area")
            or ""
        ).strip()
        if not idea:
            idea = str(answers.get("business_idea") or answers.get("idea") or "")
    # If location_city embeds district, keep as city string for gap text
    if city and not district and "," in city:
        # e.g. "Olaya, Riyadh, Saudi Arabia"
        district = city.split(",")[0].strip()
    if city:
        gaps.append(f"Regional economic indicators relevant to {city}")
        gaps.append(
            f"Location economics, commercial rent, and footfall proxies for "
            f"{district + ', ' if district and district.lower() not in city.lower() else ''}{city}"
        )
        gaps.append(
            f"Local competitors and pricing near {district or city} for "
            f"{sector or idea or archetype or 'the proposed business'}"
        )

    # Always request commercial operating evidence for local archetypes
    arch_l = (archetype or "").lower()
    sector_l = (sector or idea or "").lower()
    if any(h in arch_l or h in sector_l for h in _LOCAL_ARCHETYPE_HINTS) or city:
        gaps.append(
            "Competitor discovery, ticket/pricing signals, rent and labor operating "
            f"estimates for {sector or idea or 'local business'} in "
            f"{city or 'Saudi Arabia'}"
        )

    for m in missing[:5]:
        if m:
            gaps.append(str(m))

    if not any(
        any(k in g.lower() for k in ("inflation", "gdp", "statistic", "labor", "cpi"))
        for g in gaps
    ):
        gaps.append("Official inflation / GDP / labor statistics for Saudi Arabia")
    if not any(any(k in g.lower() for k in ("investment", "fdi", "misa")) for g in gaps):
        gaps.append("Official FDI / investment climate indicators for Saudi Arabia")

    claim_types: list[str] = []
    for c in existing_claims:
        if isinstance(c, dict):
            claim_types.append(str(c.get("source_type") or ""))
        else:
            claim_types.append(str(getattr(c, "source_type", "") or ""))
    if claim_types and all(t == "ai_assumption" for t in claim_types):
        gaps.append(
            "Replace provisional ai_assumption with official source evidence where available"
        )

    return gaps


def extract_research_context_from_state(state: Any) -> dict[str, str]:
    """Sector / geography / idea for market research wiring."""
    try:
        from ai_engine.research.market.planner import extract_market_context_from_state

        ctx = extract_market_context_from_state(state)
        return {
            "sector": str(ctx.get("sector") or ""),
            "geography": str(ctx.get("geography") or "Saudi Arabia"),
            "business_idea": str(ctx.get("business_idea") or ""),
        }
    except Exception:  # noqa: BLE001
        return {"sector": "", "geography": "Saudi Arabia", "business_idea": ""}
