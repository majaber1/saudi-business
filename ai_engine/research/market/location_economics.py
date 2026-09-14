"""Location economics extractor — evidence-backed district/city operating context.

Generic across business types. Never invents rent or footfall figures.
"""
from __future__ import annotations

import re
from typing import Any

from ai_engine.research.market.schemas import EvidenceStatus, LocationEconomicsSignal

_RENT_RE = re.compile(
    r"(?:SAR|SR|ر\.?\s*س|ريال)\s*([0-9][0-9,]{2,6})|"
    r"([0-9][0-9,]{2,6})\s*(?:SAR|SR|ر\.?\s*س|ريال)",
    re.I,
)
_DENSITY_RE = re.compile(
    r"approximately\s+(\d+)\s+OpenStreetMap|competition density[^\d]*(\d+)",
    re.I,
)


def extract_location_economics(
    *,
    evidence_items: list[dict[str, Any]],
    geography: str = "Saudi Arabia",
) -> tuple[list[LocationEconomicsSignal], EvidenceStatus]:
    signals: list[LocationEconomicsSignal] = []
    seen: set[str] = set()

    for item in evidence_items or []:
        if not isinstance(item, dict):
            continue
        text = str(
            item.get("statement")
            or item.get("content")
            or item.get("claim")
            or item.get("title")
            or ""
        ).strip()
        if not text:
            continue
        lower = text.lower()
        source_url = item.get("source_url") or item.get("url") or item.get("canonical_url")
        source_key = item.get("source_key")
        document_id = item.get("document_id") or item.get("source_id")
        kind_hint = str(item.get("document_type") or item.get("evidence_kind") or "")

        is_location = any(
            k in lower
            for k in (
                "location economics",
                "district",
                "competition density",
                "footfall",
                "commercial rent",
                "operating context",
                "neighbourhood",
                "neighborhood",
                "حي",
                "إيجار",
            )
        ) or kind_hint in {"location_context", "competition_density", "rent_signal"}
        if not is_location:
            continue

        factor = "district_context"
        value: Any = None
        unit = None
        if "competition density" in lower or "amenities within" in lower:
            factor = "competition_density"
            m = _DENSITY_RE.search(text)
            if m:
                value = int(m.group(1) or m.group(2))
                unit = "osm_amenities"
        elif "rent" in lower or "إيجار" in lower:
            factor = "commercial_rent_signal"
            rents = []
            for m in _RENT_RE.finditer(text):
                raw = (m.group(1) or m.group(2) or "").replace(",", "")
                try:
                    rents.append(float(raw))
                except ValueError:
                    continue
            if rents:
                value = {"min": min(rents), "max": max(rents), "samples": rents[:5]}
                unit = "SAR"
        elif "customer" in lower or "landmark" in lower or "business district" in lower:
            factor = "customer_profile_proxy"

        key = f"{factor}:{str(value)[:40]}:{str(source_url)[:60]}"
        if key in seen:
            continue
        seen.add(key)

        status: EvidenceStatus = "VERIFIED" if source_url else "NOT_VERIFIED"
        if factor == "commercial_rent_signal" and value is None:
            status = "PARTIAL"
        signals.append(
            LocationEconomicsSignal(
                geography=str(item.get("geography") or geography),
                factor=factor,
                value=value,
                unit=unit,
                source_url=str(source_url) if source_url else None,
                evidence_reference=str(document_id or source_url or "location_text")[:240],
                status=status,
                source_key=str(source_key) if source_key else None,
                document_id=str(document_id) if document_id else None,
                confidence=0.7 if source_url and value is not None else 0.55 if source_url else 0.35,
                notes=text[:400],
            )
        )

    if not signals:
        return (
            [
                LocationEconomicsSignal(
                    geography=geography,
                    factor="none",
                    value=None,
                    unit=None,
                    source_url=None,
                    evidence_reference="no_sourced_location_economics",
                    status="NOT_FOUND",
                    confidence=0.0,
                    notes="No district/city economics evidence after multi-source search.",
                )
            ],
            "NOT_FOUND",
        )
    if any(s.status == "VERIFIED" for s in signals):
        return signals, "VERIFIED"
    if any(s.status == "PARTIAL" for s in signals):
        return signals, "PARTIAL"
    return signals, "NOT_VERIFIED"
