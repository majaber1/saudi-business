"""Reusable domain classes for commercial evidence acquisition.

Sector packs and evidence classes reference these *classes*, not raw domain
lists. Adding Scrap / SaaS / manufacturing reuses the same registry and only
adds new domain classes or evidence classes — no coffee-only allowlist patch.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DomainClass:
    id: str
    label: str
    domains: tuple[str, ...]
    notes: str = ""
    # When True, hosts discovered via trusted connectors (OSM website tags,
    # search hits) may be session-merged into the follow allowlist.
    allow_discovered_hosts: bool = False


DOMAIN_CLASSES: dict[str, DomainClass] = {
    "official_saudi": DomainClass(
        id="official_saudi",
        label="Official Saudi sources",
        domains=(
            "stats.gov.sa",
            "www.stats.gov.sa",
            "misa.gov.sa",
            "www.misa.gov.sa",
            "mc.gov.sa",
            "www.mc.gov.sa",
            "balady.gov.sa",
            "www.balady.gov.sa",
            "zatca.gov.sa",
            "www.zatca.gov.sa",
        ),
        notes="Macro / regulation / labor statistics — not ticket or rent alone.",
    ),
    "open_geo_encyclopedia": DomainClass(
        id="open_geo_encyclopedia",
        label="Open geographic + encyclopedia",
        domains=(
            "nominatim.openstreetmap.org",
            "openstreetmap.org",
            "www.openstreetmap.org",
            "overpass-api.de",
            "en.wikipedia.org",
            "ar.wikipedia.org",
            "wikipedia.org",
        ),
    ),
    "search_index": DomainClass(
        id="search_index",
        label="Governed search index hosts",
        domains=(
            "html.duckduckgo.com",
            "duckduckgo.com",
            "www.bing.com",
            "bing.com",
        ),
        notes="Discovery only; numeric claims require page follow + adapter.",
    ),
    "real_estate_listing": DomainClass(
        id="real_estate_listing",
        label="Commercial real-estate listings",
        domains=(
            "propertyfinder.sa",
            "www.propertyfinder.sa",
            "bayut.sa",
            "www.bayut.sa",
            "sa.aqar.fm",
            "aqar.fm",
            "www.aqar.fm",
            "wasalt.sa",
            "www.wasalt.sa",
            "sakan.co",
            "www.sakan.co",
            "haraj.com.sa",
        ),
        allow_discovered_hosts=True,
    ),
    "job_salary": DomainClass(
        id="job_salary",
        label="Employer / job / salary evidence",
        domains=(
            "bayt.com",
            "www.bayt.com",
            "sa.indeed.com",
            "indeed.com",
            "www.indeed.com",
            "linkedin.com",
            "www.linkedin.com",
            "glassdoor.com",
            "www.glassdoor.com",
            "drjobpro.com",
            "www.drjobpro.com",
        ),
        allow_discovered_hosts=True,
    ),
    "delivery_marketplace": DomainClass(
        id="delivery_marketplace",
        label="Delivery marketplace / menu pages",
        domains=(
            "hungerstation.com",
            "www.hungerstation.com",
            "jahez.net",
            "www.jahez.net",
            "jahez.com",
            "www.jahez.com",
            "keeta.com",
            "www.keeta.com",
            "thechefz.co",
            "www.thechefz.co",
        ),
        allow_discovered_hosts=True,
    ),
    "equipment_vendor": DomainClass(
        id="equipment_vendor",
        label="Equipment vendors / distributors / catalogs",
        domains=(
            "amazon.sa",
            "www.amazon.sa",
            "ikea.com",
            "www.ikea.com",
            "jarir.com",
            "www.jarir.com",
            "extra.com",
            "www.extra.com",
            "noon.com",
            "www.noon.com",
        ),
        allow_discovered_hosts=True,
    ),
    "fitout_vendor": DomainClass(
        id="fitout_vendor",
        label="Fit-out / construction / POS vendor pricing",
        domains=(
            "amazon.sa",
            "www.amazon.sa",
            "ikea.com",
            "www.ikea.com",
            "jarir.com",
            "www.jarir.com",
            "extra.com",
            "www.extra.com",
        ),
        allow_discovered_hosts=True,
    ),
    "market_report": DomainClass(
        id="market_report",
        label="Credible local market reports",
        domains=(
            "en.wikipedia.org",
            "ar.wikipedia.org",
            "www.stats.gov.sa",
            "stats.gov.sa",
        ),
        allow_discovered_hosts=True,
    ),
}


def domains_for_classes(class_ids: list[str] | tuple[str, ...]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for cid in class_ids:
        dc = DOMAIN_CLASSES.get(cid)
        if not dc:
            continue
        for d in dc.domains:
            key = d.lower()
            if key not in seen:
                seen.add(key)
                out.append(d)
    return out


def allows_discovered_hosts(class_ids: list[str] | tuple[str, ...]) -> bool:
    return any(
        DOMAIN_CLASSES[c].allow_discovered_hosts
        for c in class_ids
        if c in DOMAIN_CLASSES
    )


def domain_class_public_meta() -> list[dict[str, Any]]:
    return [
        {
            "id": dc.id,
            "label": dc.label,
            "domain_count": len(dc.domains),
            "allow_discovered_hosts": dc.allow_discovered_hosts,
            "notes": dc.notes,
        }
        for dc in DOMAIN_CLASSES.values()
    ]
