"""Phase 8C.2 — Deterministic Research Quality package.

LLM must never choose which source is authoritative.
"""

from ai_engine.research.quality.engine import (
    RESEARCH_QUALITY_POLICY_VERSION,
    AuthorityFit,
    ClaimType,
    ConflictResult,
    ConflictStatus,
    EvidenceQualityResult,
    FreshnessState,
    GeographyFit,
    ProvenanceState,
    QualityComponents,
    QualityEvaluationResult,
    QualityState,
    RelevanceState,
    SelectionStatus,
    classify_claim_type,
    classify_non_conflict,
    enrich_claims_with_quality,
    evaluate_research_quality,
)
from ai_engine.research.quality.observability import (
    OBSERVABILITY_VERSION,
    attach_observability_to_research_context,
    project_research_quality_observability,
    source_display_name,
)

__all__ = [
    "RESEARCH_QUALITY_POLICY_VERSION",
    "OBSERVABILITY_VERSION",
    "AuthorityFit",
    "ClaimType",
    "ConflictResult",
    "ConflictStatus",
    "EvidenceQualityResult",
    "FreshnessState",
    "GeographyFit",
    "ProvenanceState",
    "QualityComponents",
    "QualityEvaluationResult",
    "QualityState",
    "RelevanceState",
    "SelectionStatus",
    "attach_observability_to_research_context",
    "classify_claim_type",
    "classify_non_conflict",
    "enrich_claims_with_quality",
    "evaluate_research_quality",
    "project_research_quality_observability",
    "source_display_name",
]
