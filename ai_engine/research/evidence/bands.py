"""Derive LOW/BASE/HIGH SYSTEM_ESTIMATE bands from normalized observations.

A SYSTEM_ESTIMATE without upstream observations is forbidden.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from statistics import median
from typing import Any, Optional

from ai_engine.research.evidence.observations import NumericObservation

# Maps assumption keys → observation metrics that can feed them.
METRIC_TO_ASSUMPTION: dict[str, str] = {
    "rent_monthly_sar": "rent_monthly",
    "rent_sar_per_m2_year": "rent_monthly",  # needs area to convert — handled specially
    "store_area_m2": "store_area_m2",
    "menu_item_sar": "avg_ticket",
    "salary_monthly_sar": "labor_monthly",
    "equipment_item_sar": "equipment_capex",
    "opening_item_sar": "other_capex",
    "fitout_sar_per_m2": "fitout_capex",
    "fitout_total_sar": "fitout_capex",
    "food_cost_pct": "food_cost_pct",
}


@dataclass
class EstimateBand:
    key: str
    low: float
    base: float
    high: float
    unit: str
    currency: str
    geography: str
    as_of: str
    observation_count: int
    source_count: int
    source_urls: list[str]
    derivation: str
    confidence: float
    provenance_class: str = "SYSTEM_ESTIMATE"
    estimate_basis: str = "evidence_observation_band"
    recency: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_operating_estimate_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": f"{self.base:g}",
            "low": f"{self.low:g}",
            "base": f"{self.base:g}",
            "high": f"{self.high:g}",
            "currency": self.currency,
            "geography": self.geography,
            "as_of": self.as_of,
            "confidence": self.confidence,
            "reasoning": self.derivation,
            "source_urls": self.source_urls,
            "provenance_class": "SYSTEM_ESTIMATE",
            "estimate_basis": self.estimate_basis,
            "observation_count": self.observation_count,
            "source_diversity": self.source_count,
        }


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        raise ValueError("empty")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def derive_estimate_band(
    *,
    key: str,
    values: list[float],
    observations: list[NumericObservation],
    geography: str = "Saudi Arabia",
    unit: str = "SAR",
    derivation_prefix: str = "",
    min_observations: int = 2,
) -> Optional[EstimateBand]:
    """Build LOW/BASE/HIGH from values. Requires min_observations (default 2)."""
    vals = [float(v) for v in values if v is not None]
    if len(vals) < min_observations:
        # Single URL-backed observation may still form a narrow band (±15%)
        if len(vals) == 1 and any(o.source_url for o in observations):
            v = vals[0]
            vals = [v * 0.85, v, v * 1.15]
            derivation_prefix = (
                derivation_prefix
                or "Single URL-backed observation expanded ±15% pending more comparables. "
            )
        else:
            return None
    sorted_v = sorted(vals)
    low_v = _percentile(sorted_v, 0.25) if len(sorted_v) >= 4 else min(sorted_v)
    high_v = _percentile(sorted_v, 0.75) if len(sorted_v) >= 4 else max(sorted_v)
    base_v = float(median(sorted_v))
    urls = sorted({o.source_url for o in observations if o.source_url})
    hosts = sorted({(o.source_url or "").split("/")[2] for o in observations if o.source_url})
    as_of = datetime.now(timezone.utc).date().isoformat()
    dates = [o.retrieved_at[:10] for o in observations if o.retrieved_at]
    recency = max(dates) if dates else as_of
    conf = min(
        0.78,
        0.35
        + 0.08 * min(len(vals), 6)
        + 0.05 * min(len(hosts), 4)
        + (0.05 if urls else 0.0),
    )
    derivation = (
        f"{derivation_prefix}"
        f"SYSTEM_ESTIMATE '{key}' from {len(observations)} observation(s) "
        f"({len(vals)} numeric samples); geography '{geography}'. "
        f"Robust stats: min={min(sorted_v):g}, p25/low={low_v:g}, median/base={base_v:g}, "
        f"p75/high={high_v:g}, max={max(sorted_v):g}. "
        f"Source diversity: {len(hosts)} host(s). Recency: {recency}. "
        f"Not VERIFIED_FACT — owner should confirm with primary quotes."
    )
    return EstimateBand(
        key=key,
        low=round(low_v, 2),
        base=round(base_v, 2),
        high=round(high_v, 2),
        unit=unit,
        currency="SAR" if "percent" not in unit else "",
        geography=geography,
        as_of=as_of,
        observation_count=len(observations),
        source_count=len(hosts),
        source_urls=urls[:8],
        derivation=derivation,
        confidence=conf,
        recency=recency,
        metadata={"sample_min": min(sorted_v), "sample_max": max(sorted_v)},
    )


def bands_from_observations(
    observations: list[NumericObservation],
    *,
    geography: str = "Saudi Arabia",
    store_area_m2: float | None = None,
    staffing_roles: int | None = None,
) -> list[EstimateBand]:
    """Aggregate observations into assumption-key estimate bands."""
    by_metric: dict[str, list[NumericObservation]] = {}
    for o in observations or []:
        by_metric.setdefault(o.metric, []).append(o)

    bands: list[EstimateBand] = []

    # avg_ticket from menu items — use median basket proxy (middle of observed items)
    menu = by_metric.get("menu_item_sar") or []
    if menu:
        vals = [o.value for o in menu]
        # Ticket ≈ sum of a small comparable basket proxy: p25+p50 of items as low/base-ish
        # More defensible: treat item distribution percentiles as ticket band
        band = derive_estimate_band(
            key="avg_ticket",
            values=vals,
            observations=menu,
            geography=geography,
            unit="SAR",
            derivation_prefix=(
                "Menu-item observations used as comparable ticket evidence "
                "(item-level prices; basket not owner-specified). "
            ),
        )
        if band:
            bands.append(band)

    # rent monthly direct
    rent_m = by_metric.get("rent_monthly_sar") or []
    rent_m2 = by_metric.get("rent_sar_per_m2_year") or []
    area_obs = by_metric.get("store_area_m2") or []
    area = store_area_m2
    if area is None and area_obs:
        area = float(median([o.value for o in area_obs]))
        ab = derive_estimate_band(
            key="store_area_m2",
            values=[o.value for o in area_obs],
            observations=area_obs,
            geography=geography,
            unit="m2",
        )
        if ab:
            bands.append(ab)

    rent_vals: list[float] = [o.value for o in rent_m]
    rent_obs = list(rent_m)
    if rent_m2 and area:
        for o in rent_m2:
            monthly = (o.value * area) / 12.0
            rent_vals.append(monthly)
            rent_obs.append(o)
    if rent_vals:
        band = derive_estimate_band(
            key="rent_monthly",
            values=rent_vals,
            observations=rent_obs,
            geography=geography,
            unit="SAR/month",
            derivation_prefix=(
                f"Commercial rent comparables"
                + (f" using area {area:g} m² for m²-year quotes" if area else "")
                + ". "
            ),
        )
        if band:
            bands.append(band)

    # labor: role salaries → if multiple roles, sum medians * headcount heuristic only when
    # staffing_roles provided; else treat as one-role monthly labor cost band
    sal = by_metric.get("salary_monthly_sar") or []
    if sal:
        vals = [o.value for o in sal]
        if staffing_roles and staffing_roles > 1:
            # Scale median role salary by role count — labeled as staffing-model estimate
            med = float(median(vals))
            scaled = [med * staffing_roles * f for f in (0.85, 1.0, 1.2)]
            band = derive_estimate_band(
                key="labor_monthly",
                values=scaled,
                observations=sal,
                geography=geography,
                unit="SAR/month",
                derivation_prefix=(
                    f"Role salary observations (n={len(sal)}); staffing model uses "
                    f"{staffing_roles} roles × median role salary {med:g} with ± band. "
                ),
                min_observations=1,
            )
        else:
            band = derive_estimate_band(
                key="labor_monthly",
                values=vals,
                observations=sal,
                geography=geography,
                unit="SAR/month",
                derivation_prefix=(
                    "Role salary observations aggregated as monthly labor evidence "
                    "(single-role / unscaled unless staffing model provided). "
                ),
            )
        if band:
            bands.append(band)

    # equipment: sum of component references OR band of catalog prices for a package
    equip = by_metric.get("equipment_item_sar") or []
    if equip:
        vals = [o.value for o in equip]
        # Component package: low=sum of cheapest 3 distinct, high=sum of dearest 3,
        # base=median*3 as a small-shop package proxy — only when enough items
        sorted_v = sorted(vals)
        if len(sorted_v) >= 3:
            package_low = sum(sorted_v[:3])
            package_high = sum(sorted_v[-3:])
            package_base = float(median(sorted_v)) * 3
            package_vals = [package_low, package_base, package_high]
            band = derive_estimate_band(
                key="equipment_capex",
                values=package_vals,
                observations=equip,
                geography=geography,
                unit="SAR",
                derivation_prefix=(
                    f"Equipment CAPEX package from {len(equip)} vendor catalog "
                    f"observations: low=sum(3 cheapest), base=3×median, high=sum(3 dearest). "
                ),
                min_observations=1,
            )
        else:
            band = derive_estimate_band(
                key="equipment_capex",
                values=vals,
                observations=equip,
                geography=geography,
                unit="SAR",
                derivation_prefix="Equipment catalog observations (insufficient for package sum). ",
            )
        if band:
            bands.append(band)

    opening = by_metric.get("opening_item_sar") or []
    if opening:
        vals = [o.value for o in opening]
        sorted_v = sorted(vals)
        if len(sorted_v) >= 4:
            package = [
                sum(sorted_v[:4]),
                float(median(sorted_v)) * 4,
                sum(sorted_v[-4:]),
            ]
            band = derive_estimate_band(
                key="other_capex",
                values=package,
                observations=opening,
                geography=geography,
                unit="SAR",
                derivation_prefix=(
                    "Furniture/POS/opening package from vendor observations "
                    "(4-item package low/base/high). "
                ),
                min_observations=1,
            )
        else:
            band = derive_estimate_band(
                key="other_capex",
                values=vals,
                observations=opening,
                geography=geography,
                unit="SAR",
            )
        if band:
            bands.append(band)

    fit_m2 = by_metric.get("fitout_sar_per_m2") or []
    fit_tot = by_metric.get("fitout_total_sar") or []
    fit_vals: list[float] = [o.value for o in fit_tot]
    fit_obs = list(fit_tot)
    if fit_m2 and area:
        for o in fit_m2:
            fit_vals.append(o.value * area)
            fit_obs.append(o)
    if fit_vals:
        band = derive_estimate_band(
            key="fitout_capex",
            values=fit_vals,
            observations=fit_obs,
            geography=geography,
            unit="SAR",
            derivation_prefix="Fit-out evidence (total and/or SAR/m²×area). ",
        )
        if band:
            bands.append(band)

    cogs = by_metric.get("food_cost_pct") or []
    if cogs:
        band = derive_estimate_band(
            key="food_cost_pct",
            values=[o.value for o in cogs],
            observations=cogs,
            geography=geography,
            unit="percent",
            derivation_prefix="Sourced COGS / food-cost percent mentions. ",
        )
        if band:
            bands.append(band)

    return bands
