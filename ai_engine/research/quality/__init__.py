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

__all__ = [
    "RESEARCH_QUALITY_POLICY_VERSION",
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
    "classify_claim_type",
    "classify_non_conflict",
    "enrich_claims_with_quality",
    "evaluate_research_quality",
]
