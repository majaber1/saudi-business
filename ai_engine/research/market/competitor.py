"""Controlled competitor intelligence — evidence required, never invent."""

from __future__ import annotations

import re
from typing import Any

from ai_engine.research.market.schemas import CompetitorEvidence, EvidenceStatus

_NAME_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9&.\-]+(?:\s+[A-Z][A-Za-z0-9&.\-]+){0,4})\b"
)

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
}


def _is_plausible_competitor_name(name: str) -> bool:
    parts = name.split()
    if len(name) < 3 or len(name) > 80:
        return False
    if name in _STOP_NAMES:
        return False
    if all(p in _STOP_NAMES for p in parts):
        return False
    return any(p not in _STOP_NAMES and len(p) > 2 for p in parts)


_ISO_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?$"
)

_SAUDI_CITIES = (
    "riyadh",
    "jeddah",
    "dammam",
    "khobar",
    "makkah",
    "mecca",
    "madinah",
    "medina",
    "tabuk",
    "abha",
)

_FOREIGN_PLACE = (
    "dubai",
    "abu dhabi",
    "united arab",
    "uae",
    "bahrain",
    "kuwait",
    "qatar",
    "egypt",
    "united states",
    " u.s.",
    "usa",
)


def _http_url(url: Any) -> str | None:
    if not isinstance(url, str):
        return None
    value = url.strip()
    lower = value.lower()
    if lower.startswith("https://") or lower.startswith("http://"):
        return value
    return None


def _valid_timestamp(value: Any) -> str | None:
    """Return the original timestamp text when it is a real ISO date. Never invent one."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or not _ISO_TIMESTAMP.match(text):
        return None
    from datetime import datetime

    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return text


def _normalize_name(name: str) -> str:
    text = name.casefold()
    text = re.sub(r"[^0-9a-z\u0600-\u06ff\s]", " ", text)
    text = re.sub(r"\b(co|company|ltd|limited|inc|llc|the)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _stated_location(item: dict[str, Any]) -> str | None:
    for key in ("location", "city", "stated_geography"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _geography_mismatch(requested: str, stated: str | None) -> bool:
    if not stated:
        return False
    req = requested.casefold()
    loc = stated.casefold()
    expects_saudi = "saudi" in req or any(city in req for city in _SAUDI_CITIES)
    if expects_saudi and any(token in loc for token in _FOREIGN_PLACE):
        return True
    req_cities = [city for city in _SAUDI_CITIES if city in req]
    loc_cities = [city for city in _SAUDI_CITIES if city in loc]
    if req_cities and loc_cities and set(req_cities).isdisjoint(loc_cities):
        return True
    return False


def _dedupe_competitors(records: list[CompetitorEvidence]) -> list[CompetitorEvidence]:
    """Merge reliable duplicates. Conflicting locations are not merged into a verified record."""
    grouped: dict[str, list[CompetitorEvidence]] = {}
    order: list[str] = []
    for record in records:
        key = _normalize_name(record.name) or f"unnamed:{id(record)}"
        if key not in grouped:
            order.append(key)
            grouped[key] = []
        grouped[key].append(record)

    merged: list[CompetitorEvidence] = []
    for key in order:
        group = grouped[key]
        if key.startswith("unnamed:") or len(group) == 1:
            merged.extend(group)
            continue
        locations = {item.location.casefold() for item in group if item.location}
        if len(locations) > 1:
            for item in group:
                item.status = "NOT_VERIFIED"
                item.record_kind = "unverified_mention"
                item.confidence = 0.0
                item.rejection_reason = "geographic_or_identity_conflict"
            merged.extend(group)
            continue
        verified = [item for item in group if item.status == "VERIFIED"]
        merged.append(verified[0] if verified else group[0])
    return merged


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
    _ = sector
    found: list[CompetitorEvidence] = []

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
        explicit = str(item.get("competitor_name") or item.get("name") or "").strip()

        candidates: list[str] = []
        if explicit:
            candidates.append(explicit)
        elif source_url or document_id:
            lower = text.lower()
            if any(
                k in lower
                for k in ("competitor", "competes", "rival", "player", "company", "firm")
            ):
                for m in _NAME_PATTERN.finditer(text[:800]):
                    name = m.group(1).strip(" .,;:")
                    if _is_plausible_competitor_name(name):
                        candidates.append(name)

        for name in candidates:
            stated_location = _stated_location(item)
            publisher = item.get("publisher") or item.get("source_name")
            raw_timestamp = item.get("retrieved_at") or item.get("retrieved_date")
            timestamp = _valid_timestamp(raw_timestamp)
            http_url = _http_url(source_url)
            supporting = text or None
            reason = None
            if not _is_plausible_competitor_name(name):
                reason = "unidentifiable_name"
            elif _geography_mismatch(geography, stated_location):
                reason = "geographic_mismatch"
            elif not http_url:
                reason = "missing_url"
            elif raw_timestamp not in (None, "") and timestamp is None:
                reason = "invalid_timestamp"
            elif timestamp is None:
                reason = "missing_timestamp"
            verified = reason is None
            found.append(
                CompetitorEvidence(
                    name=name,
                    source_url=http_url,
                    evidence_type="verified_record" if verified else "unverified_mention",
                    geography=geography,
                    confidence=0.7 if verified else 0.0,
                    evidence_reference=str(
                        document_id or http_url or chunk_id or "missing_source"
                    ),
                    status="VERIFIED" if verified else "NOT_VERIFIED",
                    source_key=str(source_key) if source_key else None,
                    document_id=str(document_id) if document_id else None,
                    chunk_id=str(chunk_id) if chunk_id else None,
                    publisher=str(publisher).strip() if isinstance(publisher, str) and publisher.strip() else None,
                    location=stated_location,
                    retrieved_at=timestamp,
                    supporting_claim=supporting,
                    record_kind="verified_record" if verified else "unverified_mention",
                    rejection_reason=reason,
                )
            )

    return _dedupe_competitors(found)


def research_competitors(
    *,
    business_idea: str,
    sector: str,
    geography: str = "Saudi Arabia",
    evidence_items: list[dict[str, Any]] | None = None,
) -> tuple[list[CompetitorEvidence], EvidenceStatus]:
    """
    Controlled competitor research.

    Without sourced evidence → NOT_FOUND (never invent).
    A verified record needs an identifiable name, an http(s) URL, and a real
    retrieval timestamp. Missing fields stay missing.
    """
    _ = business_idea
    items = list(evidence_items or [])
    competitors = extract_competitors_from_evidence(
        evidence_items=items, geography=geography, sector=sector
    )
    named = [c for c in competitors if c.name]
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
                )
            ],
            "NOT_FOUND",
        )
    if any(c.status == "VERIFIED" for c in named):
        return named, "VERIFIED"
    if any(c.status == "NOT_VERIFIED" for c in named):
        return named, "NOT_VERIFIED"
    return named, "PARTIAL"
