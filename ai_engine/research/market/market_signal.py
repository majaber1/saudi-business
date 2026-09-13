"""Market signals from official evidence only — never estimate missing values."""

from __future__ import annotations

import re
from typing import Any

from ai_engine.research.market.schemas import EvidenceStatus, MarketSignal

_METRIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "cpi_inflation",
        re.compile(
            r"(?:inflation|cpi|consumer price)[^\d%]{0,40}(\d+(?:\.\d+)?)\s*%",
            re.I,
        ),
    ),
    (
        "gdp_growth",
        re.compile(r"(?:gdp|gross domestic)[^\d%]{0,40}(\d+(?:\.\d+)?)\s*%", re.I),
    ),
    (
        "fdi_inflow",
        re.compile(
            r"(?:fdi|foreign direct investment)[^\d]{0,40}(\d+(?:\.\d+)?)",
            re.I,
        ),
    ),
    (
        "unemployment",
        re.compile(r"(?:unemployment)[^\d%]{0,40}(\d+(?:\.\d+)?)\s*%", re.I),
    ),
]


def _period_from_text(text: str) -> str | None:
    m = re.search(
        r"(Q[1-4]\s*(?:of\s*)?20\d{2}|20\d{2}|January|February|March|April|May|June|"
        r"July|August|September|October|November|December\s+20\d{2})",
        text,
        re.I,
    )
    return m.group(1) if m else None


def extract_market_signals(
    evidence_items: list[dict[str, Any]],
) -> list[MarketSignal]:
    """Extract numeric market signals only when present in sourced evidence."""
    signals: list[MarketSignal] = []
    seen: set[tuple[str, str | None, str]] = set()

    for item in evidence_items:
        if not isinstance(item, dict):
            continue
        text = str(
            item.get("statement") or item.get("content") or item.get("claim") or ""
        )
        source_url = item.get("source_url") or item.get("url")
        source_key = str(item.get("source_key") or item.get("source") or "unknown")
        source_type = str(item.get("source_type") or "")
        if source_type and source_type not in {"official", "document"}:
            continue
        if not source_url and not item.get("document_id"):
            continue

        period = _period_from_text(text)
        for metric, pattern in _METRIC_PATTERNS:
            m = pattern.search(text)
            if not m:
                continue
            value = m.group(1)
            key = (metric, period, str(value))
            if key in seen:
                continue
            seen.add(key)
            geo = item.get("geography") or item.get("country") or item.get("geo")
            unit = item.get("unit")
            signals.append(
                MarketSignal(
                    metric=metric,
                    value=float(value) if "." in value else int(value),
                    period=period,
                    source=source_key,
                    evidence_reference=str(
                        item.get("document_id")
                        or item.get("chunk_id")
                        or source_url
                        or "sourced_text"
                    ),
                    source_url=str(source_url) if source_url else None,
                    status="VERIFIED",
                    source_key=source_key,
                    document_id=(
                        str(item["document_id"]) if item.get("document_id") else None
                    ),
                    chunk_id=str(item["chunk_id"]) if item.get("chunk_id") else None,
                    confidence=0.85 if source_type == "official" else 0.7,
                    geography=str(geo).strip() if geo else None,
                    unit=str(unit).strip() if unit else None,
                )
            )
    return signals


def _norm_geo(geo: str | None) -> str | None:
    if geo is None or not str(geo).strip():
        return None
    g = str(geo).strip().upper()
    if g in {"SA", "SAU", "KSA", "SAUDI", "SAUDI ARABIA", "KINGDOM OF SAUDI ARABIA"}:
        return "SA"
    return g


def _norm_unit(unit: str | None) -> str | None:
    if unit is None or not str(unit).strip():
        return None
    u = str(unit).strip().lower()
    return {
        "%": "percent",
        "pct": "percent",
        "percent": "percent",
        "percentage": "percent",
    }.get(u, u)


def detect_signal_conflicts(signals: list[MarketSignal]) -> list[dict[str, Any]]:
    """Flag comparable metric conflicts — never silent override.

    Phase 8C.2: require matching period + geography + unit when present.
    Different period/geography/unit is NOT a numeric conflict.
    """
    by_key: dict[tuple[str, str | None, str | None, str | None], list[MarketSignal]] = {}
    for s in signals:
        by_key.setdefault(
            (s.metric, s.period, _norm_geo(s.geography), _norm_unit(s.unit)),
            [],
        ).append(s)

    conflicts: list[dict[str, Any]] = []
    for (metric, period, geography, unit), group in by_key.items():
        values = {str(s.value) for s in group}
        if len(values) > 1:
            for s in group:
                s.status = "CONFLICT"
            conflicts.append(
                {
                    "metric": metric,
                    "period": period,
                    "geography": geography,
                    "unit": unit,
                    "values": sorted(values),
                    "sources": [s.source for s in group],
                    "evidence_references": [s.evidence_reference for s in group],
                    "status": "CONFLICT",
                    "candidates": [s.evidence_reference for s in group],
                }
            )
    return conflicts


def research_market_signals(
    evidence_items: list[dict[str, Any]],
) -> tuple[list[MarketSignal], list[dict[str, Any]], EvidenceStatus]:
    signals = extract_market_signals(evidence_items)
    conflicts = detect_signal_conflicts(signals)
    if conflicts:
        return signals, conflicts, "CONFLICT"
    if signals:
        return signals, conflicts, "VERIFIED"
    return signals, conflicts, "NOT_FOUND"
