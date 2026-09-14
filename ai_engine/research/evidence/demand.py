"""CAPACITY vs DEMAND estimates — never treat physical max as expected demand."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ThroughputEstimate:
    kind: str  # CAPACITY_ESTIMATE | DEMAND_ESTIMATE
    daily_covers: float
    low: float
    base: float
    high: float
    derivation: str
    confidence: float
    inputs: dict[str, Any]
    provenance_class: str = "SYSTEM_ESTIMATE"

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_capacity_and_demand(
    *,
    seats: float | None,
    operating_hours: float | None,
    competitor_density_count: int | None = None,
    service_model: str | None = None,
    # Max realistic seat-turns per hour — methodology constant, not a market fact.
    # Labeled explicitly; only applied when seats+hours are known from evidence/user.
    max_turns_per_seat_hour: float = 1.0,
) -> dict[str, Any]:
    """
    Build CAPACITY_ESTIMATE and optional DEMAND_ESTIMATE.

    CAPACITY = seats × hours × max_turns_per_seat_hour (physical/service ceiling).
    DEMAND is NEVER set equal to capacity. Without demand proxies, demand stays None.
    """
    out: dict[str, Any] = {
        "capacity": None,
        "demand": None,
        "notes": [],
    }
    if seats is None or seats <= 0 or operating_hours is None or operating_hours <= 0:
        out["notes"].append(
            "CAPACITY_ESTIMATE blocked: seats_capacity and/or operating_hours_day missing."
        )
        return out

    cap_base = float(seats) * float(operating_hours) * float(max_turns_per_seat_hour)
    capacity = ThroughputEstimate(
        kind="CAPACITY_ESTIMATE",
        daily_covers=round(cap_base, 2),
        low=round(cap_base * 0.8, 2),
        base=round(cap_base, 2),
        high=round(cap_base * 1.2, 2),
        derivation=(
            f"CAPACITY_ESTIMATE = seats({seats:g}) × hours({operating_hours:g}) × "
            f"max_turns_per_seat_hour({max_turns_per_seat_hour:g}). "
            f"This is a physical/service ceiling, NOT expected demand. "
            f"Turn-rate is a methodology constraint, not a sourced market fact."
        ),
        confidence=0.55,
        inputs={
            "seats": seats,
            "operating_hours": operating_hours,
            "max_turns_per_seat_hour": max_turns_per_seat_hour,
            "service_model": service_model,
        },
    )
    out["capacity"] = capacity.to_public_dict()

    if competitor_density_count is None:
        out["notes"].append(
            "DEMAND_ESTIMATE withheld: no demand proxy (density/benchmark) available; "
            "do not copy CAPACITY into daily_covers."
        )
        return out

    dens = int(competitor_density_count)
    if dens >= 12:
        util_low, util_base, util_high = 0.25, 0.35, 0.45
        dens_note = f"high competition density ({dens})"
    elif dens >= 6:
        util_low, util_base, util_high = 0.35, 0.45, 0.55
        dens_note = f"moderate competition density ({dens})"
    else:
        util_low, util_base, util_high = 0.40, 0.55, 0.65
        dens_note = f"lower competition density ({dens})"

    demand = ThroughputEstimate(
        kind="DEMAND_ESTIMATE",
        daily_covers=round(cap_base * util_base, 2),
        low=round(cap_base * util_low, 2),
        base=round(cap_base * util_base, 2),
        high=round(cap_base * util_high, 2),
        derivation=(
            f"DEMAND_ESTIMATE = CAPACITY_ESTIMATE × utilization band "
            f"({util_low:.0%}–{util_high:.0%}, base {util_base:.0%}) informed by "
            f"{dens_note}. Distinct from capacity; not a footfall sensor reading. "
            f"SYSTEM_ESTIMATE only — not VERIFIED_FACT."
        ),
        confidence=0.4,
        inputs={
            "capacity_base": cap_base,
            "utilization_low": util_low,
            "utilization_base": util_base,
            "utilization_high": util_high,
            "competitor_density_count": dens,
            "service_model": service_model,
        },
    )
    out["demand"] = demand.to_public_dict()
    out["notes"].append(
        "DEMAND_ESTIMATE derived from capacity×density utilization; "
        "owner should validate with primary footfall / comps."
    )
    return out
