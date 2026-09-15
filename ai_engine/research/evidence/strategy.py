"""Resolve follow-allowlists, queries, and seed URLs from evidence classes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from ai_engine.research.evidence.domain_classes import (
    DOMAIN_CLASSES,
    allows_discovered_hosts,
    domains_for_classes,
)
from ai_engine.research.evidence.evidence_classes import (
    EVIDENCE_CLASSES,
    SECTOR_EVIDENCE_CLASSES,
    EvidenceClassSpec,
    build_render_context,
    render_template,
)


@dataclass
class ResolvedStrategy:
    evidence_class_ids: list[str]
    domain_class_ids: list[str]
    allowlist_domains: list[str]
    queries: list[str]
    seed_urls: list[str]
    adapters: dict[str, str]  # evidence_class_id → adapter_id
    allow_discovered_hosts: bool
    meta: dict[str, Any] = field(default_factory=dict)


def evidence_classes_for_sector(sector: str | None, *, archetype: str | None = None) -> list[str]:
    blob = f"{sector or ''} {archetype or ''}".lower()
    if any(t in blob for t in ("fnb", "f&b", "food", "restaurant", "cafe", "café", "coffee", "bakery")):
        return list(SECTOR_EVIDENCE_CLASSES["fnb"])
    if any(t in blob for t in ("manufactur", "industrial", "factory", "مصنع")):
        return list(SECTOR_EVIDENCE_CLASSES["manufacturing"])
    if any(t in blob for t in ("saas", "software", "digital", "platform")):
        return list(SECTOR_EVIDENCE_CLASSES["saas"])
    return list(SECTOR_EVIDENCE_CLASSES["default"])


def allowlist_for_classes(evidence_class_ids: list[str]) -> list[str]:
    domain_ids: list[str] = []
    seen: set[str] = set()
    # Always include geo/encyclopedia + search for discovery scaffolding
    for required in ("open_geo_encyclopedia", "search_index", "official_saudi"):
        if required not in seen:
            seen.add(required)
            domain_ids.append(required)
    for eid in evidence_class_ids:
        spec = EVIDENCE_CLASSES.get(eid)
        if not spec:
            continue
        for dc in spec.domain_classes:
            if dc not in seen:
                seen.add(dc)
                domain_ids.append(dc)
    return domains_for_classes(domain_ids)


def query_templates_for_classes(
    evidence_class_ids: list[str],
    *,
    city: str = "",
    district: str = "",
    sector: str = "",
    query: str = "",
    amenity: str = "",
    max_queries: int = 10,
) -> list[str]:
    ctx = build_render_context(
        city=city, district=district, sector=sector, query=query, amenity=amenity
    )
    out: list[str] = []
    for eid in evidence_class_ids:
        spec = EVIDENCE_CLASSES.get(eid)
        if not spec:
            continue
        for tmpl in spec.query_templates:
            q = render_template(tmpl, ctx=ctx).strip()
            q = " ".join(q.split())
            if q and q not in out:
                out.append(q)
            if len(out) >= max_queries:
                return out
    return out


def seed_urls_for_classes(
    evidence_class_ids: list[str],
    *,
    city: str = "",
    district: str = "",
    sector: str = "",
    query: str = "",
    amenity: str = "",
    max_urls: int = 24,
    prioritize_class_ids: list[str] | None = None,
) -> list[str]:
    ctx = build_render_context(
        city=city, district=district, sector=sector, query=query, amenity=amenity
    )
    # When recovering gaps, ensure each prioritized class contributes at least one
    # seed before rent/equipment catalogs consume the entire budget.
    ordered = list(evidence_class_ids)
    if prioritize_class_ids:
        head = [c for c in prioritize_class_ids if c in ordered]
        tail = [c for c in ordered if c not in head]
        ordered = head + tail

    out: list[str] = []

    def _append_from(eid: str, *, limit: int | None = None) -> int:
        spec = EVIDENCE_CLASSES.get(eid)
        if not spec:
            return 0
        added = 0
        for tmpl in spec.seed_url_templates:
            url = render_template(tmpl, ctx=ctx).strip()
            if "{" in url or "}" in url:
                continue
            if url and url not in out:
                out.append(url)
                added += 1
            if len(out) >= max_urls:
                return added
            if limit is not None and added >= limit:
                return added
        return added

    if prioritize_class_ids:
        for eid in prioritize_class_ids:
            if eid in ordered:
                _append_from(eid, limit=2)
                if len(out) >= max_urls:
                    return out
    # Round-robin first pass so salary/menu seed growth cannot starve
    # equipment / fit-out / COGS catalogs under the default budget.
    for eid in ordered:
        _append_from(eid, limit=3)
        if len(out) >= max_urls:
            return out
    for eid in ordered:
        _append_from(eid)
        if len(out) >= max_urls:
            return out
    return out


def merge_session_hosts(
    base_allowlist: list[str],
    discovered_urls: list[str],
    *,
    evidence_class_ids: list[str],
    max_extra: int = 12,
) -> list[str]:
    """Session-merge discovered commercial hosts when evidence classes allow it."""
    if not allows_discovered_hosts(
        list(
            {
                dc
                for eid in evidence_class_ids
                for dc in (EVIDENCE_CLASSES.get(eid).domain_classes if EVIDENCE_CLASSES.get(eid) else ())
            }
        )
    ):
        return list(base_allowlist)
    out = list(base_allowlist)
    seen = {d.lower() for d in out}
    added = 0
    for url in discovered_urls:
        try:
            host = (urlparse(url).hostname or "").lower()
        except Exception:
            continue
        if not host or host in seen:
            continue
        # Basic safety: no IPs, no localhost
        if host in {"localhost", "127.0.0.1"} or host.replace(".", "").isdigit():
            continue
        if any(host == d or host.endswith("." + d) for d in seen):
            continue
        out.append(host)
        seen.add(host)
        added += 1
        if added >= max_extra:
            break
    return out


def resolve_strategy(
    *,
    sector: str | None = None,
    archetype: str | None = None,
    evidence_class_ids: list[str] | None = None,
    city: str = "",
    district: str = "",
    query: str = "",
    amenity: str = "",
    missing_keys: list[str] | None = None,
) -> ResolvedStrategy:
    classes = list(evidence_class_ids or evidence_classes_for_sector(sector, archetype=archetype))
    # Targeted recovery: if missing_keys provided, prefer classes that cover them
    if missing_keys:
        needed: list[str] = []
        miss = set(missing_keys)
        for eid, spec in EVIDENCE_CLASSES.items():
            if miss.intersection(spec.assumption_keys) and eid not in needed:
                needed.append(eid)
        if needed:
            # Keep originals then append targeted
            for eid in needed:
                if eid not in classes:
                    classes.append(eid)

    domain_ids: list[str] = []
    seen_dc: set[str] = set()
    for req in ("open_geo_encyclopedia", "search_index", "official_saudi"):
        seen_dc.add(req)
        domain_ids.append(req)
    adapters: dict[str, str] = {}
    for eid in classes:
        spec = EVIDENCE_CLASSES.get(eid)
        if not spec:
            continue
        adapters[eid] = spec.adapter_id
        for dc in spec.domain_classes:
            if dc not in seen_dc:
                seen_dc.add(dc)
                domain_ids.append(dc)

    allow = domains_for_classes(domain_ids)
    prioritize: list[str] = []
    miss_set = set(missing_keys or [])
    if miss_set:
        for eid, spec in EVIDENCE_CLASSES.items():
            if miss_set.intersection(spec.assumption_keys) and eid not in prioritize:
                prioritize.append(eid)
        # Prefer gap classes ahead of already-satisfied catalog-heavy classes.
        if prioritize:
            head = [c for c in prioritize if c in classes]
            tail = [c for c in classes if c not in head]
            classes = head + tail
            # Rebuild adapters/domain order is already done; class order mainly
            # affects seed/query budget allocation below.

    seed_budget = 32 if prioritize else 28
    query_budget = 18 if prioritize else 14
    queries = query_templates_for_classes(
        classes,
        city=city,
        district=district,
        sector=sector or amenity or "",
        query=query,
        amenity=amenity,
        max_queries=query_budget,
    )
    seeds = seed_urls_for_classes(
        classes,
        city=city,
        district=district,
        sector=sector or amenity or "",
        query=query,
        amenity=amenity,
        max_urls=seed_budget,
        prioritize_class_ids=prioritize or None,
    )
    # Preserve which evidence class owns each seed (for adapter scoping)
    seed_owners: dict[str, list[str]] = {}
    ctx = build_render_context(
        city=city,
        district=district,
        sector=sector or amenity or "",
        query=query,
        amenity=amenity,
    )
    for eid in classes:
        spec = EVIDENCE_CLASSES.get(eid)
        if not spec:
            continue
        for tmpl in spec.seed_url_templates:
            url = render_template(tmpl, ctx=ctx).strip()
            if "{" in url or "}" in url:
                continue
            seed_owners.setdefault(url, []).append(eid)

    return ResolvedStrategy(
        evidence_class_ids=classes,
        domain_class_ids=domain_ids,
        allowlist_domains=allow,
        queries=queries,
        seed_urls=seeds,
        adapters=adapters,
        allow_discovered_hosts=allows_discovered_hosts(domain_ids),
        meta={
            "sector": sector,
            "archetype": archetype,
            "city": city,
            "district": district,
            "amenity": amenity,
            "domain_class_count": len(domain_ids),
            "allowlist_count": len(allow),
            "query_count": len(queries),
            "seed_count": len(seeds),
            "seed_owners": seed_owners,
        },
    )


def adapter_for_evidence_class(evidence_class_id: str) -> str | None:
    spec = EVIDENCE_CLASSES.get(evidence_class_id)
    return spec.adapter_id if spec else None


def specs_for_ids(ids: list[str]) -> list[EvidenceClassSpec]:
    return [EVIDENCE_CLASSES[i] for i in ids if i in EVIDENCE_CLASSES]
