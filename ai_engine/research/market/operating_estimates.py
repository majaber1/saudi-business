"""Evidence-backed operating SYSTEM_ESTIMATE synthesizer.

Produces defensible estimates ONLY when sourced evidence contains numeric
signals. Never invents rent, labor, ticket, CAPEX, or COGS. Generic across
archetypes — key matching is by assumption key / semantic family.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

_NUMBER = re.compile(
    r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w.])"
)

# Maps assumption keys → evidence keyword families (generic, not coffee-only).
_KEY_EVIDENCE_HINTS: dict[str, tuple[str, ...]] = {
    "rent_monthly": ("rent", "lease", "إيجار", "commercial rent", "per month"),
    "avg_ticket": ("ticket", "average price", "menu", "price signal", "sar", "سعر"),
    "labor_monthly": ("salary", "labor", "wage", "barista", "staff cost", "راتب"),
    "food_cost_pct": ("cogs", "food cost", "cost of goods", "cogs%"),
    "fitout_capex": ("fit out", "fit-out", "fitout", "renovation", "fit out cost"),
    "equipment_capex": ("equipment", "machinery", "espresso", "capex equipment"),
    "utilities_monthly": ("utilities", "electricity", "utility cost"),
    "marketing_monthly": ("marketing", "cac", "advertising"),
    "store_area_m2": ("sqm", "m2", "m²", "square meter", "area"),
}


@dataclass
class OperatingEstimate:
    key: str
    value: str
    low: Optional[str]
    base: Optional[str]
    high: Optional[str]
    currency: str
    geography: str
    as_of: str
    confidence: float
    reasoning: str
    source_urls: list[str]
    provenance_class: str = "SYSTEM_ESTIMATE"
    estimate_basis: str = "evidence_numeric_synthesis"

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nums_near_keywords(text: str, keywords: tuple[str, ...]) -> list[float]:
    low = text.lower()
    if not any(k in low for k in keywords):
        return []
    out: list[float] = []
    for m in _NUMBER.finditer(text.replace("\u066c", ",")):
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        # Skip years
        if val in {2023, 2024, 2025, 2026, 2027, 2030}:
            continue
        out.append(val)
    return out


def _plausible_for_key(key: str, values: list[float]) -> list[float]:
    """Filter to plausible ranges so we do not misuse unrelated numbers."""
    if not values:
        return []
    if key == "rent_monthly":
        return [v for v in values if 3_000 <= v <= 400_000]
    if key == "avg_ticket":
        return [v for v in values if 5 <= v <= 250]
    if key == "labor_monthly":
        return [v for v in values if 3_000 <= v <= 200_000]
    if key == "food_cost_pct":
        # Prefer percents; if raw 0-1 scale multiply later
        pcts = [v for v in values if 5 <= v <= 70]
        fracs = [v * 100 for v in values if 0.05 <= v <= 0.7]
        return pcts or fracs
    if key in {"fitout_capex", "equipment_capex"}:
        return [v for v in values if 5_000 <= v <= 5_000_000]
    if key in {"utilities_monthly", "marketing_monthly"}:
        return [v for v in values if 200 <= v <= 100_000]
    if key == "store_area_m2":
        return [v for v in values if 20 <= v <= 2_000]
    return []


def synthesize_operating_estimates(
    *,
    evidence_items: list[dict[str, Any]],
    target_keys: list[str] | None = None,
    geography: str = "Saudi Arabia",
) -> list[OperatingEstimate]:
    """
    Build SYSTEM_ESTIMATE candidates from evidence numerics.

    Returns only keys with at least one plausible sourced number.
    """
    keys = target_keys or list(_KEY_EVIDENCE_HINTS.keys())
    buckets: dict[str, list[tuple[float, str, str]]] = {k: [] for k in keys}
    as_of = datetime.now(timezone.utc).date().isoformat()

    for item in evidence_items or []:
        if not isinstance(item, dict):
            continue
        text = str(
            item.get("statement")
            or item.get("content")
            or item.get("claim")
            or item.get("title")
            or ""
        )
        url = str(item.get("source_url") or item.get("url") or item.get("canonical_url") or "")
        # Require some provenance — URL or document id or commercial_discovery source
        has_prov = bool(
            url
            or item.get("document_id")
            or item.get("source_key") in {"commercial_discovery", "gastat", "misa"}
        )
        if not has_prov or not text:
            continue
        geo = str(item.get("geography") or geography)
        for key in keys:
            hints = _KEY_EVIDENCE_HINTS.get(key, ())
            nums = _plausible_for_key(key, _nums_near_keywords(text, hints))
            for n in nums:
                buckets[key].append((n, url, geo))

    estimates: list[OperatingEstimate] = []
    for key, samples in buckets.items():
        if not samples:
            continue
        vals = [s[0] for s in samples]
        urls = sorted({s[1] for s in samples if s[1]})
        geos = [s[2] for s in samples if s[2]]
        geo = geos[0] if geos else geography
        low_v, high_v = min(vals), max(vals)
        # Prefer median-ish base
        sorted_v = sorted(vals)
        base_v = sorted_v[len(sorted_v) // 2]
        conf = min(0.75, 0.35 + 0.1 * min(len(vals), 4) + (0.1 if urls else 0.0))
        reasoning = (
            f"SYSTEM_ESTIMATE for '{key}' derived from {len(vals)} numeric mention(s) "
            f"in sourced commercial/official evidence for geography '{geo}'. "
            f"Observed range {low_v:g}–{high_v:g}; base uses median {base_v:g}. "
            f"Sources: {', '.join(urls[:4]) or 'document-backed commercial discovery'}. "
            f"Not a verified contracted value — owner should confirm with primary quotes."
        )
        estimates.append(
            OperatingEstimate(
                key=key,
                value=f"{base_v:g}",
                low=f"{low_v:g}",
                base=f"{base_v:g}",
                high=f"{high_v:g}",
                currency="SAR",
                geography=geo,
                as_of=as_of,
                confidence=conf,
                reasoning=reasoning,
                source_urls=urls[:6],
            )
        )
    return estimates


def apply_estimates_to_assumptions(
    assumptions: list[Any],
    estimates: list[OperatingEstimate],
) -> list[Any]:
    """Fill UNKNOWN / empty assumptions with evidence-backed SYSTEM_ESTIMATE only."""
    by_key = {e.key: e for e in estimates}
    out = []
    for a in assumptions:
        key = getattr(a, "key", None) if not isinstance(a, dict) else a.get("key")
        val = getattr(a, "value", None) if not isinstance(a, dict) else a.get("value")
        est = by_key.get(str(key)) if key else None
        if est is None:
            out.append(a)
            continue
        current = str(val or "").strip().upper()
        if current and current != "UNKNOWN":
            # Do not overwrite user or already-filled values
            origin = getattr(a, "origin", None) if not isinstance(a, dict) else a.get("origin")
            if origin == "user":
                out.append(a)
                continue
            if current not in {"", "UNKNOWN", "NONE", "NULL"}:
                out.append(a)
                continue
        # Apply estimate
        if isinstance(a, dict):
            a = dict(a)
            a["value"] = est.value
            a["low"] = est.low
            a["base"] = est.base
            a["high"] = est.high
            a["origin"] = "ai_estimated"
            a["ai_estimated"] = True
            a["provenance_class"] = "SYSTEM_ESTIMATE"
            a["source"] = f"SYSTEM_ESTIMATE from evidence ({est.geography}, {est.as_of})"
            a["confidence"] = "medium" if est.confidence >= 0.55 else "low"
            a["estimate_basis"] = est.estimate_basis
            a["estimate_rationale"] = est.reasoning
            out.append(a)
        else:
            a.value = est.value
            a.low = est.low
            a.base = est.base
            a.high = est.high
            a.origin = "ai_estimated"
            a.ai_estimated = True
            a.provenance_class = "SYSTEM_ESTIMATE"
            a.source = f"SYSTEM_ESTIMATE from evidence ({est.geography}, {est.as_of})"
            a.confidence = "medium" if est.confidence >= 0.55 else "low"
            a.estimate_basis = est.estimate_basis
            a.estimate_rationale = est.reasoning
            out.append(a)
    return out
