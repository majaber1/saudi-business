"""Explicit discount-rate contract.

PERCENT and RATIO are the only accepted representations. A bare number is
never divided by 100. Historical API callers that omit a representation keep
the old ratio contract only when the value is already inside 0..1.
"""
from __future__ import annotations

from typing import Optional


class AmbiguousRateError(ValueError):
    """Raised when a rate cannot be interpreted without guessing."""


def normalize_explicit_rate(value, representation: str) -> float:
    """Convert an explicitly labeled rate to a ratio in [0, 1]."""
    label = (representation or "").strip().upper()
    if isinstance(value, str):
        text = value.strip().replace("%", "").replace("٪", "").replace(",", "").strip()
        if not text:
            raise AmbiguousRateError("Rate value is empty")
        number = float(text)
    else:
        number = float(value)
    if label == "PERCENT":
        if number < 0 or number > 100:
            raise AmbiguousRateError("PERCENT rate must be between 0 and 100")
        return number / 100.0
    if label == "RATIO":
        if number < 0 or number > 1:
            raise AmbiguousRateError("RATIO rate must be between 0 and 1 and was not rescaled")
        return number
    raise AmbiguousRateError("rate_representation must be PERCENT or RATIO")


def resolve_api_discount_rate(value: float, representation: Optional[str]) -> tuple[float, str]:
    """Resolve a discount rate at an API boundary.

    Missing representation preserves the historical ratio contract for values
    already in [0, 1]. Values outside that range are rejected and are not
    divided by 100. Stored results are not rewritten by this function.
    """
    if representation is None:
        number = float(value)
        if number < 0 or number > 1:
            raise AmbiguousRateError(
                "discount_rate without discount_rate_representation must already be a ratio "
                "between 0 and 1. Pass PERCENT or RATIO. The value was not divided by 100."
            )
        return number, "RATIO"
    ratio = normalize_explicit_rate(value, representation)
    return ratio, representation.strip().upper()
