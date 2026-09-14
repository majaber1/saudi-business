"""Product Hardening Sprint — deterministic trust / decision-quality layer.

Does NOT replace Research → Evidence → Quality → Financial → Risk → Decision.
Adds intelligence BETWEEN layers. No migrations. No Phase 9A benchmarks.
"""

from .archetype_intelligence import (
    HARDENING_ARCHETYPES,
    assumption_requirement_explanations,
    classify_business_archetype,
    missing_required_assumptions,
    normalize_business_archetype,
    required_assumptions_for,
    schema_archetype_for,
)
from .assumption_semantics import (
    is_placeholder_sentinel,
    map_origin_to_provenance,
    semantic_type_for_key,
    validate_assumption_value,
)
from .evidence_gates import (
    apply_decision_safety,
    evaluate_evidence_verdict_gates,
    evaluate_numeric_evidence_assumption_consistency,
)
from .financial_gates import evaluate_financial_trust_gates
from .sector_packs import (
    SECTOR_PACK_IDS,
    get_sector_pack,
    list_sector_packs,
    sector_pack_for_archetype,
)

__all__ = [
    "HARDENING_ARCHETYPES",
    "SECTOR_PACK_IDS",
    "assumption_requirement_explanations",
    "classify_business_archetype",
    "missing_required_assumptions",
    "normalize_business_archetype",
    "required_assumptions_for",
    "schema_archetype_for",
    "evaluate_financial_trust_gates",
    "evaluate_evidence_verdict_gates",
    "evaluate_numeric_evidence_assumption_consistency",
    "apply_decision_safety",
    "get_sector_pack",
    "list_sector_packs",
    "sector_pack_for_archetype",
    "validate_assumption_value",
    "is_placeholder_sentinel",
    "map_origin_to_provenance",
    "semantic_type_for_key",
]
