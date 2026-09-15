"""Derive LOW/BASE/HIGH SYSTEM_ESTIMATE bands from normalized observations.

A SYSTEM_ESTIMATE without upstream observations is forbidden.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import math
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
    "seats_capacity": "seats_capacity",
    "operating_hours_day": "operating_hours_day",
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



def _pctile(vals: list[float], p: float) -> float:
    if not vals:
        raise ValueError("empty")
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def _role_bucket(role: str | None) -> str | None:
    r = (role or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not r or r in {"statutory_minimum_wage", "statutory_min_wage"}:
        return None
    if any(k in r for k in ("store_manager", "restaurant_manager", "cafe_manager", "coffee_shop_manager")):
        return "store_manager"
    if r == "manager":
        return "store_manager"
    if any(k in r for k in ("head_barista", "senior_barista", "assistant_manager", "shift_supervisor", "shift_manager")):
        return "head_barista"
    if "barista" in r:
        return "barista"
    if any(k in r for k in ("cashier", "support", "waiter", "server")):
        return "cashier"
    return None


def _role_salary_band(obs: list[NumericObservation]) -> dict[str, tuple[float, float, float]]:
    """Per-role low/base/high monthly salary from observations (outliers trimmed)."""
    by_role: dict[str, list[float]] = {}
    for o in obs:
        bucket = _role_bucket(getattr(o, "role_or_item", None))
        if not bucket:
            continue
        v = float(o.value)
        # Junior role >15k/mo is usually annual residue / bad scrape — drop.
        if bucket in {"barista", "cashier"} and v > 15_000:
            continue
        if bucket == "head_barista" and v > 12_000:
            continue  # asst-manager p75 scrapes often look like annual residue
        if bucket == "store_manager" and v > 18_000:
            continue  # KSA cafe-manager surveys above this are usually annual residue / bad scrapes
        if v < 800:
            continue
        by_role.setdefault(bucket, []).append(v)
    out: dict[str, tuple[float, float, float]] = {}
    for role, vals in by_role.items():
        if len(vals) == 1:
            v = vals[0]
            out[role] = (round(v * 0.85, 2), round(v, 2), round(v * 1.15, 2))
        else:
            out[role] = (
                round(_pctile(vals, 0.25), 2),
                round(_pctile(vals, 0.50), 2),
                round(_pctile(vals, 0.75), 2),
            )
    return out


def _derive_seats_from_area(
    area_m2: float,
    density_obs: list[NumericObservation],
) -> tuple[float, float, float, str] | None:
    """Customer area → seats using sourced m²/seat density (kitchen share 25–35%)."""
    dens = [float(o.value) for o in density_obs if 0.5 <= float(o.value) <= 5.0]
    if not dens or area_m2 <= 0:
        return None
    # Kitchen/back-of-house share 25–35% of total (Brave Calculator industry notes).
    # Customer-area fraction = complement midpoints → low uses more kitchen (fewer seats).
    cust_frac_low, cust_frac_base, cust_frac_high = 0.65, 0.70, 0.75
    d_low, d_base, d_high = _pctile(dens, 0.75), _pctile(dens, 0.50), _pctile(dens, 0.25)
    # Higher density m²/seat → fewer seats.
    seats_low = (area_m2 * cust_frac_low) / d_low
    seats_base = (area_m2 * cust_frac_base) / d_base
    seats_high = (area_m2 * cust_frac_high) / d_high
    ordered = sorted([seats_low, seats_base, seats_high])
    derivation = (
        f"SEATS from store area {area_m2:g} m² × customer-area fraction "
        f"(0.65–0.75; complement of sourced kitchen 25–35% share) ÷ dining density "
        f"{d_high:.2f}/{d_base:.2f}/{d_low:.2f} m²/seat (n={len(dens)}). "
        f"CAPACITY_ESTIMATE input — not demand."
    )
    return (round(ordered[0], 1), round(ordered[1], 1), round(ordered[2], 1), derivation)


def _derive_role_headcount(
    *,
    seats_base: float,
    hours_day: float | None,
    foh_guests_per: float,
    boh_share: float,
    mgr_per_shift: float,
) -> dict[str, float]:
    """Map café staffing-calculator ratios → role FTEs (evidence-derived)."""
    occupancy = 0.70  # default from sourced staffing calculator input
    days_open = 6.0
    max_hours = 40.0
    buffer = 1.20
    hours = float(hours_day) if hours_day and hours_day > 0 else 12.0
    avg_guests = max(1.0, seats_base * occupancy)
    foh_peak = max(1.0, math.ceil(avg_guests / max(foh_guests_per, 1.0)))
    boh_peak = max(1.0, math.ceil(foh_peak * max(boh_share, 0.05)))
    mgr_peak = max(1.0, mgr_per_shift)
    shifts_needed = max(1.0, (days_open * hours) / max_hours)
    total_foh = max(1.0, math.ceil(foh_peak * shifts_needed * buffer))
    total_boh = max(1.0, math.ceil(boh_peak * shifts_needed * buffer))
    total_mgr = max(1.0, math.ceil(mgr_peak * shifts_needed * buffer))
    # Label FOH as barista + cashier/support without inventing total FOH:
    # one support slot when FOH≥2; remainder baristas. BOH → head barista.
    cashier = 1.0 if total_foh >= 2 else 0.0
    barista = max(1.0, total_foh - cashier)
    return {
        "store_manager": float(total_mgr),
        "head_barista": float(total_boh),
        "barista": float(barista),
        "cashier": float(cashier),
    }



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

    # labor: role-based payroll from salary observations × sourced staffing ratios
    sal = by_metric.get("salary_monthly_sar") or []
    # Drop staffing-ratio / density residue that was historically mis-tagged as salary.
    sal = [o for o in sal if 800 <= float(o.value) <= 40_000]
    foh_ratio_obs = by_metric.get("staff_foh_guests_per") or []
    boh_share_obs = by_metric.get("staff_boh_share_of_foh") or []
    mgr_shift_obs = by_metric.get("staff_mgr_per_shift") or []
    hours_obs = by_metric.get("operating_hours_day") or by_metric.get("operating_hours_day") or []
    density_obs = by_metric.get("dining_m2_per_seat") or []
    seats_obs = by_metric.get("seats_capacity") or by_metric.get("seats_capacity") or []

    # Prefer OSM seats; else derive seats from area × dining density.
    seats_band_vals: tuple[float, float, float] | None = None
    seats_derivation = ""
    if seats_obs:
        svals = [float(o.value) for o in seats_obs if float(o.value) > 0]
        if svals:
            if len(svals) == 1:
                seats_band_vals = (svals[0] * 0.85, svals[0], svals[0] * 1.15)
            else:
                seats_band_vals = (_pctile(svals, 0.25), _pctile(svals, 0.50), _pctile(svals, 0.75))
            seats_derivation = "OSM/local venue seat or capacity tags."
    elif area and density_obs:
        derived = _derive_seats_from_area(float(area), density_obs)
        if derived:
            seats_band_vals = (derived[0], derived[1], derived[2])
            seats_derivation = derived[3]

    role_pay = _role_salary_band(sal) if sal else {}
    floor_obs = [
        o for o in sal
        if _role_bucket(getattr(o, "role_or_item", None)) is None
        and "minimum" in str(getattr(o, "role_or_item", "") or "").lower()
        or (o.metadata or {}).get("statutory_minimum_wage")
    ]
    # Also catch statutory role labels
    floor_obs = [
        o for o in sal
        if "statutory" in str(getattr(o, "role_or_item", "") or "").lower()
        or (o.metadata or {}).get("statutory_minimum_wage")
    ]
    wage_floor = float(median([o.value for o in floor_obs])) if floor_obs else None

    if role_pay and foh_ratio_obs and seats_band_vals:
        foh_g = float(median([o.value for o in foh_ratio_obs]))
        boh_s = float(median([o.value for o in boh_share_obs])) if boh_share_obs else 0.35
        mgr_s = float(median([o.value for o in mgr_shift_obs])) if mgr_shift_obs else 1.0
        hours_day = float(median([o.value for o in hours_obs])) if hours_obs else None
        head = _derive_role_headcount(
            seats_base=seats_band_vals[1],
            hours_day=hours_day,
            foh_guests_per=foh_g,
            boh_share=boh_s,
            mgr_per_shift=mgr_s,
        )
        # Need manager + barista at minimum to form payroll
        if "store_manager" in role_pay and "barista" in role_pay:
            low = base = high = 0.0
            parts: list[str] = []
            used_obs = list(sal) + list(foh_ratio_obs) + list(boh_share_obs) + list(mgr_shift_obs)
            for role, count in head.items():
                if count <= 0:
                    continue
                # Fallback mapping if a role salary band is missing
                pay = role_pay.get(role)
                if pay is None and role == "head_barista":
                    pay = role_pay.get("barista")
                if pay is None and role == "cashier":
                    pay = role_pay.get("barista")
                if pay is None:
                    continue
                r_low, r_base, r_high = pay
                if wage_floor:
                    r_low = max(r_low, wage_floor)
                    r_base = max(r_base, wage_floor)
                    r_high = max(r_high, wage_floor)
                low += count * r_low
                base += count * r_base
                high += count * r_high
                parts.append(f"{role}×{count:g}@{r_base:g}")
            if base > 0 and parts:
                band = derive_estimate_band(
                    key="labor_monthly",
                    values=[low, base, high],
                    observations=used_obs,
                    geography=geography,
                    unit="SAR/month",
                    derivation_prefix=(
                        "Role-based café payroll from sourced role salaries × staffing-calculator "
                        f"ratios (FOH guests/staff={foh_g:g}, BOH share={boh_s:g}, mgr/shift={mgr_s:g}); "
                        f"headcount from seats_base={seats_band_vals[1]:g} and hours/day="
                        f"{hours_day if hours_day is not None else 'default-12'}. "
                        f"Composition: {', '.join(parts)}. "
                        + (
                            f"Statutory wage floor {wage_floor:g} SAR/mo applied per role where below floor. "
                            if wage_floor
                            else ""
                        )
                    ),
                    min_observations=1,
                )
                if band:
                    band.metadata = {
                        **(band.metadata or {}),
                        "role_headcount": head,
                        "role_salary_bands": role_pay,
                        "seats_base_used": seats_band_vals[1],
                        "payroll_model": "role_based_staffing_ratios",
                    }
                    bands.append(band)
    elif sal:
        # Fallback: do not treat statutory-only as café payroll when no role model.
        role_only = [o for o in sal if _role_bucket(getattr(o, "role_or_item", None))]
        use = role_only or sal
        vals = [o.value for o in use]
        if staffing_roles and staffing_roles > 1 and role_only:
            med = float(median(vals))
            scaled = [med * staffing_roles * f for f in (0.85, 1.0, 1.2)]
            band = derive_estimate_band(
                key="labor_monthly",
                values=scaled,
                observations=use,
                geography=geography,
                unit="SAR/month",
                derivation_prefix=(
                    f"Role salary observations (n={len(use)}); staffing model uses "
                    f"{staffing_roles} roles × median role salary {med:g} with ± band. "
                ),
                min_observations=1,
            )
        else:
            # If only statutory min wage, keep band but mark as floor-only in derivation.
            only_floor = bool(use) and all(
                _role_bucket(getattr(o, "role_or_item", None)) is None for o in use
            )
            band = derive_estimate_band(
                key="labor_monthly",
                values=vals,
                observations=use,
                geography=geography,
                unit="SAR/month",
                derivation_prefix=(
                    "STATUTORY_MINIMUM_WAGE floor only — not a café staffing payroll model. "
                    if only_floor
                    else "Role salary observations aggregated as monthly labor evidence "
                    "(single-role / unscaled; staffing ratios or seats missing for role model). "
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

    seats = by_metric.get("seats_capacity") or by_metric.get("seats_capacity") or []
    if seats:
        band = derive_estimate_band(
            key="seats_capacity",
            values=[o.value for o in seats],
            observations=seats,
            geography=geography,
            unit="seats",
            derivation_prefix="OSM/local venue seat or capacity tags. ",
        )
        if band:
            bands.append(band)
    elif seats_band_vals and density_obs:
        # Derived seats from area × sourced dining density (not OSM tags).
        band = derive_estimate_band(
            key="seats_capacity",
            values=list(seats_band_vals),
            observations=density_obs,
            geography=geography,
            unit="seats",
            derivation_prefix=seats_derivation + " ",
            min_observations=1,
        )
        if band:
            band.metadata = {
                **(band.metadata or {}),
                "derivation_kind": "area_x_dining_density",
                "capacity_not_demand": True,
            }
            bands.append(band)

    hours = by_metric.get("operating_hours_day") or []
    if hours:
        band = derive_estimate_band(
            key="operating_hours_day",
            values=[o.value for o in hours],
            observations=hours,
            geography=geography,
            unit="hours",
            derivation_prefix="Parsed OSM opening_hours into average daily open hours. ",
        )
        if band:
            bands.append(band)

    return bands
