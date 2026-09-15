"""Evidence-class commercial acquisition — reusable across Saudi business types.

Scalable source strategy keyed by *evidence class* (rent, menu, salary, …),
not by one-off domain allowlist patches per sector.
"""
from __future__ import annotations

from ai_engine.research.evidence.bands import derive_estimate_band
from ai_engine.research.evidence.coverage import (
    MATERIAL_NUMERIC_KEYS,
    coverage_gaps,
    validate_numeric_coverage,
)
from ai_engine.research.evidence.demand import derive_capacity_and_demand
from ai_engine.research.evidence.observations import NumericObservation
from ai_engine.research.evidence.strategy import (
    EvidenceClassSpec,
    allowlist_for_classes,
    evidence_classes_for_sector,
    query_templates_for_classes,
    resolve_strategy,
    seed_urls_for_classes,
)

__all__ = [
    "MATERIAL_NUMERIC_KEYS",
    "EvidenceClassSpec",
    "NumericObservation",
    "allowlist_for_classes",
    "coverage_gaps",
    "derive_capacity_and_demand",
    "derive_estimate_band",
    "evidence_classes_for_sector",
    "query_templates_for_classes",
    "resolve_strategy",
    "seed_urls_for_classes",
    "validate_numeric_coverage",
]
