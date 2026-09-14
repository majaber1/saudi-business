"""Controlled competitor intelligence — evidence required, never invent."""

from __future__ import annotations

import re
from typing import Any

from ai_engine.research.market.schemas import CompetitorEvidence, EvidenceStatus

_NAME_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9&.\-]+(?:\s+[A-Z][A-Za-z0-9&.\-]+){0,4})\b"
)
# Explicit competitor line from commercial discovery connector
_EXPLICIT_COMPETITOR_RE = re.compile(
    r"(?:Competitor\s*/\s*local venue evidence|Competitor POI|Competitor mention)\s*:\s*([^\.\n]+)",
    re.I,
)
_ARABIC_NAME_RE = re.compile(r"([\u0600-\u06FF][\u0600-\u06FF\s]{1,40})")

_STOP_NAMES = {
    "Saudi",
    "Arabia",
    "Kingdom",
    "GASTAT",
    "MISA",
    "Ministry",
    "Investment",
    "Statistics",
    "General",
    "Authority",
    "National",
    "Strategy",
    "Development",
    "Consumer",
    "Price",
    "Index",
    "Inflation",
    "March",
    "April",
    "January",
    "February",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "Quarter",
    "Annual",
    "Table",
    "Figure",
    "Page",
    "Home",
    "News",
    "English",
    "Arabic",
    "OpenStreetMap",
    "Nominatim",
    "DuckDuckGo",
    "Wikipedia",
    "Location",
    "Competition",
    "Commercial",
    "Discovery",
}


def _is_plausible_competitor_name(name: str) -> bool:
    parts = name.split()
    if len(name) < 2 or len(name) > 80:
        return False
    if name in _STOP_NAMES:
        return False
    if all(p in _STOP_NAMES for p in parts):
        return False
    # Allow Arabic-only names
    if re.fullmatch(r"[\u0600-\u06FF\s]+", name):
        return len(name.strip()) >= 3
    return any(p not in _STOP_NAMES and len(p) > 2 for p in parts)


def _extract_exhaustion(evidence_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in evidence_items:
        text = str(item.get("statement") or item.get("content") or "")
        if "search exhaustion" in text.lower() or "multi-source search" in text.lower():
            return {
                "evidence_reference": str(
                    item.get("document_id") or item.get("source_url") or "exhaustion_log"
                ),
                "source_key": item.get("source_key"),
                "summary": text[:800],
            }
    return None


def extract_competitors_from_evidence(
    *,
    evidence_items: list[dict[str, Any]],
    geography: str = "Saudi Arabia",
    sector: str = "",
) -> list[CompetitorEvidence]:
    """
    Extract competitors only when sourced evidence exists.

    Never fabricates companies, market share, or pricing.
    """
    found: list[CompetitorEvidence] = []
    seen: set[str] = set()
    sector_blob = f"{sector} {geography}".lower()
    venue_context = any(
        k in sector_blob
        for k in (
            "coffee",
            "café",
            "cafe",
            "fnb",
            "restaurant",
            "retail",
            "shop",
            "clinic",
            "gym",
            "riyadh",
            "jeddah",
            "قهوة",
            "مقهى",
            "مطعم",
        )
    )

    for item in evidence_items:
        if not isinstance(item, dict):
            continue
        text = str(
            item.get("statement")
            or item.get("content")
            or item.get("claim")
            or item.get("title")
            or ""
        ).strip()
        source_url = item.get("source_url") or item.get("url") or item.get("canonical_url")
        document_id = item.get("document_id") or item.get("source_id")
        chunk_id = item.get("chunk_id")
        source_key = item.get("source_key")
        explicit = str(
            item.get("competitor_name") or item.get("name") or ""
        ).strip()
        relevance = str(item.get("relevance") or "").strip() or None
        if not relevance and "Relevance:" in text:
            relevance = text.split("Relevance:", 1)[-1].strip()[:300]

        candidates: list[str] = []
        if explicit:
            candidates.append(explicit)
        # Commercial discovery structured lines
        for m in _EXPLICIT_COMPETITOR_RE.finditer(text):
            candidates.append(m.group(1).strip(" .,;:"))
        if source_url or document_id or source_key == "commercial_discovery":
            lower = text.lower()
            markers = (
                "competitor",
                "competes",
                "rival",
                "player",
                "venue evidence",
                "poi",
                "company",
                "firm",
                "café",
                "cafe",
                "coffee shop",
                "specialty coffee",
                "restaurant",
                "مقهى",
                "قهوة",
                "مطعم",
            )
            if any(k in lower for k in markers) or (
                venue_context
                and any(k in lower for k in ("coffee", "café", "cafe", "restaurant", "shop"))
            ):
                for m in _NAME_PATTERN.finditer(text[:1500]):
                    name = m.group(1).strip(" .,;:")
                    if _is_plausible_competitor_name(name):
                        candidates.append(name)
                # Arabic venue names often appear after "Competitor ... evidence:"
                if "competitor" in lower or "مقهى" in text or "قهوة" in text:
                    for m in _ARABIC_NAME_RE.finditer(text[:800]):
                        name = m.group(1).strip()
                        if _is_plausible_competitor_name(name):
                            candidates.append(name)

        for name in candidates:
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            if not _is_plausible_competitor_name(name):
                continue
            why = relevance or (
                f"Sourced local venue/competitor mention near {geography} "
                f"for sector context '{sector or 'local business'}'."
            )
            if not source_url and not document_id and source_key != "commercial_discovery":
                found.append(
                    CompetitorEvidence(
                        name=name,
                        source_url=None,
                        evidence_type="unsupported_mention",
                        geography=geography,
                        confidence=0.0,
                        evidence_reference="missing_source",
                        status="NOT_VERIFIED",
                        source_key=str(source_key) if source_key else None,
                        relevance_reason=why,
                    )
                )
                continue
            found.append(
                CompetitorEvidence(
                    name=name,
                    source_url=str(source_url) if source_url else None,
                    evidence_type="sourced_mention",
                    geography=geography,
                    confidence=0.7 if source_url else 0.5,
                    evidence_reference=str(
                        document_id or source_url or chunk_id or "sourced_text"
                    ),
                    status="VERIFIED" if source_url else "NOT_VERIFIED",
                    source_key=str(source_key) if source_key else None,
                    document_id=str(document_id) if document_id else None,
                    chunk_id=str(chunk_id) if chunk_id else None,
                    relevance_reason=why,
                )
            )

    return found


def research_competitors(
    *,
    business_idea: str,
    sector: str,
    geography: str = "Saudi Arabia",
    evidence_items: list[dict[str, Any]] | None = None,
) -> tuple[list[CompetitorEvidence], EvidenceStatus]:
    """
    Controlled competitor research.

    Without sourced evidence → NOT_FOUND only after exhaustion is documented.
    Mentions lacking URL → NOT_VERIFIED.
    URL/document reference → VERIFIED (sourced mention only).
    """
    _ = business_idea
    items = list(evidence_items or [])
    competitors = extract_competitors_from_evidence(
        evidence_items=items, geography=geography, sector=sector
    )
    named = [c for c in competitors if c.name]
    exhaustion = _extract_exhaustion(items)
    if not named:
        return (
            [
                CompetitorEvidence(
                    name="",
                    source_url=None,
                    evidence_type="none",
                    geography=geography,
                    confidence=0.0,
                    evidence_reference="no_sourced_competitor_evidence",
                    status="NOT_FOUND",
                    search_exhaustion=exhaustion
                    or {
                        "summary": (
                            "NOT_FOUND after reviewing available evidence items; "
                            "no named competitor with provenance."
                        )
                    },
                )
            ],
            "NOT_FOUND",
        )
    # Attach exhaustion log to first competitor for audit trail when present
    if exhaustion and named:
        named[0].search_exhaustion = exhaustion
    if any(c.status == "VERIFIED" for c in named):
        return named, "VERIFIED"
    if any(c.status == "NOT_VERIFIED" for c in named):
        return named, "NOT_VERIFIED"
    return named, "PARTIAL"
