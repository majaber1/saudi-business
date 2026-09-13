"""Phase 8C.2 deterministic research quality engine (single module)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Literal, Sequence
from urllib.parse import urlparse

RESEARCH_QUALITY_POLICY_VERSION = "8c2-v1"

ClaimType = Literal[
    "ECONOMIC_STATISTIC",
    "LABOR_STATISTIC",
    "INFLATION",
    "GDP",
    "INVESTMENT_FDI",
    "SECTOR_INVESTMENT",
    "SME_STATISTIC",
    "BANKING_MONETARY",
    "TAX_ZAKAT_CUSTOMS",
    "CYBER_REGULATION",
    "GENERAL_REGULATION",
    "MARKET_SIZE",
    "PRICING",
    "COMPETITOR",
    "SECTOR_SIGNAL",
    "OTHER",
    "UNKNOWN",
]
AuthorityFit = Literal[
    "PRIMARY", "SECONDARY", "RELATED", "UNRELATED", "INELIGIBLE", "UNKNOWN"
]
RelevanceState = Literal["EXACT", "HIGH", "PARTIAL", "LOW", "NONE", "UNKNOWN"]
FreshnessState = Literal[
    "CURRENT", "ACCEPTABLE", "STALE", "UNKNOWN", "NOT_APPLICABLE"
]
GeographyFit = Literal[
    "EXACT", "COUNTRY", "REGIONAL", "BROAD", "UNKNOWN", "MISMATCH"
]
ProvenanceState = Literal["COMPLETE", "PARTIAL", "MISSING", "INVALID"]
QualityState = Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
SelectionStatus = Literal[
    "PREFERRED",
    "ALTERNATE",
    "REJECTED_INELIGIBLE",
    "REJECTED_AI_ASSUMPTION",
    "UNRANKED",
]
ConflictStatus = Literal[
    "NOT_CONFLICT",
    "RESOLVED_PREFERRED_SOURCE",
    "UNRESOLVED",
    "TEMPORAL_CHANGE",
    "SCOPE_MISMATCH",
]

CLAIM_AUTHORITY_POLICY: dict[str, dict[str, tuple[str, ...]]] = {
    "INFLATION": {"primary": ("gastat",), "secondary": ()},
    "GDP": {"primary": ("gastat",), "secondary": ()},
    "LABOR_STATISTIC": {"primary": ("gastat",), "secondary": ()},
    "ECONOMIC_STATISTIC": {"primary": ("gastat",), "secondary": ("saudi_open_data",)},
    "INVESTMENT_FDI": {"primary": ("misa",), "secondary": ("gastat",)},
    "SECTOR_INVESTMENT": {"primary": ("misa",), "secondary": ()},
    "SME_STATISTIC": {"primary": ("monshaat",), "secondary": ("gastat",)},
    "BANKING_MONETARY": {"primary": ("sama",), "secondary": ()},
    "TAX_ZAKAT_CUSTOMS": {"primary": ("zatca",), "secondary": ()},
    "CYBER_REGULATION": {"primary": ("nca",), "secondary": ()},
    "GENERAL_REGULATION": {
        "primary": ("sama", "zatca", "nca"),
        "secondary": ("misa", "gastat"),
    },
    "MARKET_SIZE": {"primary": ("gastat", "misa"), "secondary": ()},
    "PRICING": {"primary": ("misa", "gastat"), "secondary": ()},
    "COMPETITOR": {"primary": ("misa",), "secondary": ()},
    "SECTOR_SIGNAL": {"primary": ("misa", "gastat"), "secondary": ()},
    "OTHER": {"primary": (), "secondary": ("gastat", "misa")},
    "UNKNOWN": {"primary": (), "secondary": ()},
}

_SAUDI_OFFICIAL = {
    "gastat",
    "misa",
    "monshaat",
    "sama",
    "zatca",
    "nca",
    "saudi_open_data",
}
_AUTHORITY_RANK = {
    "PRIMARY": 5,
    "SECONDARY": 4,
    "RELATED": 3,
    "UNKNOWN": 2,
    "UNRELATED": 1,
    "INELIGIBLE": 0,
}
_FRESHNESS_WINDOWS: dict[str, tuple[int, int]] = {
    "INFLATION": (90, 270),
    "GDP": (180, 540),
    "LABOR_STATISTIC": (180, 540),
    "ECONOMIC_STATISTIC": (180, 540),
    "INVESTMENT_FDI": (180, 540),
    "SECTOR_INVESTMENT": (180, 540),
    "SME_STATISTIC": (180, 540),
    "BANKING_MONETARY": (365, 1095),
    "TAX_ZAKAT_CUSTOMS": (365, 1825),
    "CYBER_REGULATION": (730, 3650),
    "GENERAL_REGULATION": (730, 3650),
    "MARKET_SIZE": (365, 1095),
    "PRICING": (60, 180),
    "COMPETITOR": (90, 270),
    "SECTOR_SIGNAL": (120, 365),
    "OTHER": (180, 540),
    "UNKNOWN": (180, 540),
}
_REGULATION = {
    "BANKING_MONETARY",
    "TAX_ZAKAT_CUSTOMS",
    "CYBER_REGULATION",
    "GENERAL_REGULATION",
}
_CLAIM_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("INFLATION", ("inflation", "cpi", "consumer price", "cost of living")),
    ("GDP", ("gdp", "gross domestic", "national accounts")),
    (
        "LABOR_STATISTIC",
        ("unemployment", "labor force", "labour force", "employment rate", "workforce"),
    ),
    (
        "INVESTMENT_FDI",
        (
            "fdi",
            "foreign direct",
            "inward investment",
            "investment inflow",
            "capital inflow",
            "foreign investment",
        ),
    ),
    (
        "SECTOR_INVESTMENT",
        ("sector attractiveness", "investment climate", "investor license"),
    ),
    (
        "SME_STATISTIC",
        ("sme", "msme", "monshaat", "monsha'at", "small business", "medium enterprise"),
    ),
    (
        "BANKING_MONETARY",
        ("sama", "central bank", "monetary", "interest rate", "banking regulation"),
    ),
    (
        "TAX_ZAKAT_CUSTOMS",
        ("zatca", "zakat", "vat", "customs", "tax authority", "e-invoicing"),
    ),
    (
        "CYBER_REGULATION",
        ("nca", "cybersecurity", "cyber security", "essential cybersecurity"),
    ),
    (
        "GENERAL_REGULATION",
        ("regulation", "regulatory", "compliance framework", "licensing rule"),
    ),
    ("PRICING", ("price", "pricing", "tariff", "fee schedule")),
    ("COMPETITOR", ("competitor", "competition", "rival firm", "market player")),
    ("MARKET_SIZE", ("market size", "tam", "sam", "som", "addressable market")),
    ("SECTOR_SIGNAL", ("sector signal", "industry outlook", "sector growth")),
    (
        "ECONOMIC_STATISTIC",
        ("economic indicator", "official statistic", "national statistic", "macro"),
    ),
]
_METRIC_MAP = {
    "cpi_inflation": "INFLATION",
    "inflation": "INFLATION",
    "cpi": "INFLATION",
    "gdp_growth": "GDP",
    "gdp": "GDP",
    "fdi_inflow": "INVESTMENT_FDI",
    "fdi": "INVESTMENT_FDI",
    "unemployment": "LABOR_STATISTIC",
    "labor": "LABOR_STATISTIC",
}
_AI_TYPES = {"ai_assumption", "ai_inference", "assumption", "unverified"}


@dataclass(frozen=True)
class QualityComponents:
    authority: int
    relevance: int
    freshness: int
    geography: int
    provenance: int

    def to_public_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass
class EvidenceQualityResult:
    evidence_id: str
    claim_type: ClaimType
    eligible: bool
    authority_fit: AuthorityFit
    relevance: RelevanceState
    freshness: FreshnessState
    geography_fit: GeographyFit
    provenance: ProvenanceState
    quality_score: int
    quality_state: QualityState
    quality_components: QualityComponents
    ranking_position: int | None = None
    selection_status: SelectionStatus = "UNRANKED"
    ranking_reason: list[str] = field(default_factory=list)
    selection_reason_codes: list[str] = field(default_factory=list)
    source_key: str | None = None
    published_at: str | None = None
    retrieved_at: str | None = None
    policy_version: str = RESEARCH_QUALITY_POLICY_VERSION

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim_type": self.claim_type,
            "eligible": self.eligible,
            "authority_fit": self.authority_fit,
            "relevance": self.relevance,
            "freshness": self.freshness,
            "geography_fit": self.geography_fit,
            "provenance": self.provenance,
            "quality_score": self.quality_score,
            "quality_state": self.quality_state,
            "quality_components": self.quality_components.to_public_dict(),
            "ranking_position": self.ranking_position,
            "selection_status": self.selection_status,
            "ranking_reason": list(self.ranking_reason),
            "selection_reason_codes": list(self.selection_reason_codes),
            "source_key": self.source_key,
            "published_at": self.published_at,
            "retrieved_at": self.retrieved_at,
            "policy_version": self.policy_version,
        }


@dataclass
class ConflictResult:
    conflict_group_id: str
    metric: str | None
    period: str | None
    geography: str | None
    unit: str | None
    status: ConflictStatus
    candidates: list[str]
    preferred_evidence_ref: str | None
    reason_codes: list[str] = field(default_factory=list)
    explanation: str = ""
    values: list[Any] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "conflict_group_id": self.conflict_group_id,
            "metric": self.metric,
            "period": self.period,
            "geography": self.geography,
            "unit": self.unit,
            "status": self.status,
            "candidates": list(self.candidates),
            "preferred_evidence_ref": self.preferred_evidence_ref,
            "reason_codes": list(self.reason_codes),
            "explanation": self.explanation,
            "values": list(self.values),
        }


@dataclass
class QualityEvaluationResult:
    policy_version: str
    claim_type: ClaimType
    evaluations: list[EvidenceQualityResult] = field(default_factory=list)
    preferred_evidence_ids: list[str] = field(default_factory=list)
    conflicts: list[ConflictResult] = field(default_factory=list)
    as_of: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "claim_type": self.claim_type,
            "as_of": self.as_of,
            "preferred_evidence_ids": list(self.preferred_evidence_ids),
            "evaluations": [e.to_public_dict() for e in self.evaluations],
            "conflicts": [c.to_public_dict() for c in self.conflicts],
        }


def classify_claim_type(
    *,
    text: str | None = None,
    metric_key: str | None = None,
    research_type: str | None = None,
) -> ClaimType:
    if metric_key:
        mk = str(metric_key).strip().lower()
        if mk in _METRIC_MAP:
            return _METRIC_MAP[mk]  # type: ignore[return-value]
    rt = (research_type or "").strip().upper()
    mapping = {
        "COMPETITOR": "COMPETITOR",
        "PRICING": "PRICING",
        "MARKET_SIZE": "MARKET_SIZE",
        "REGULATION": "GENERAL_REGULATION",
        "SECTOR_SIGNAL": "SECTOR_SIGNAL",
    }
    if rt in mapping:
        return mapping[rt]  # type: ignore[return-value]
    blob = (text or "").strip().lower()
    if not blob:
        return "UNKNOWN"
    for claim_type, keywords in _CLAIM_RULES:
        if any(k in blob for k in keywords):
            return claim_type  # type: ignore[return-value]
    if re.search(r"\b(saudi|ksa|kingdom)\b", blob) and re.search(
        r"\b(statistic|indicator|rate|index)\b", blob
    ):
        return "ECONOMIC_STATISTIC"
    return "OTHER"


def parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def evaluate_freshness(
    *,
    claim_type: ClaimType,
    published_at: Any = None,
    retrieved_at: Any = None,  # noqa: ARG001
    as_of: datetime | None = None,
) -> tuple[FreshnessState, str | None, list[str]]:
    reasons: list[str] = []
    now = as_of or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    pub = parse_dt(published_at)
    regulation = claim_type in _REGULATION
    if pub is None:
        reasons.append("published_at_missing")
        if regulation:
            reasons.append("regulation_age_not_decisive")
            return "NOT_APPLICABLE", None, reasons
        return "UNKNOWN", None, reasons
    pub_iso = pub.date().isoformat()
    if pub > now:
        reasons.append("published_at_in_future")
        return "UNKNOWN", pub_iso, reasons
    age_days = (now.date() - pub.date()).days
    current_max, acceptable_max = _FRESHNESS_WINDOWS.get(claim_type, _FRESHNESS_WINDOWS["OTHER"])
    if regulation and age_days > acceptable_max:
        reasons.append("regulation_age_not_decisive")
        reasons.append(f"age_days={age_days}")
        return "NOT_APPLICABLE", pub_iso, reasons
    if age_days <= current_max:
        reasons.extend([f"age_days={age_days}", "within_current_window"])
        return "CURRENT", pub_iso, reasons
    if age_days <= acceptable_max:
        reasons.extend([f"age_days={age_days}", "within_acceptable_window"])
        return "ACCEPTABLE", pub_iso, reasons
    reasons.extend([f"age_days={age_days}", "beyond_acceptable_window"])
    return "STALE", pub_iso, reasons


def candidate_evidence_id(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("evidence_id")
        or candidate.get("id")
        or candidate.get("idempotency_key")
        or candidate.get("official_url")
        or candidate.get("source_url")
        or candidate.get("document_id")
        or "unknown"
    )


def is_eligible_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    source_type = str(candidate.get("source_type") or candidate.get("evidence_type") or "").lower()
    if source_type in _AI_TYPES:
        return False, ["ai_assumption_ineligible"]
    official_url = candidate.get("official_url") or candidate.get("source_url") or candidate.get("url")
    document_id = candidate.get("document_id") or candidate.get("source_document_id")
    chunk_id = candidate.get("chunk_id")
    has_url = bool(str(official_url or "").strip())
    has_doc = bool(str(document_id or "").strip())
    has_chunk = bool(str(chunk_id or "").strip())
    if has_url:
        try:
            host = (urlparse(str(official_url)).hostname or "").lower()
        except Exception:
            host = ""
        if not host:
            has_url = False
            if not (has_doc or has_chunk):
                return False, ["invalid_url", "missing_provenance"]
    if not (has_url or has_doc or has_chunk):
        return False, ["missing_provenance"]
    for key, val in (("document_id", document_id), ("chunk_id", chunk_id), ("source_key", candidate.get("source_key"))):
        if val is None:
            continue
        s = str(val).strip().lower()
        if s.startswith(("fake_", "invented_")) or s == "null":
            return False, [f"fabricated_{key}"]
    return True, ["eligible"]


def authority_fit_for_source(*, claim_type: ClaimType, source_key: str | None, eligible: bool) -> AuthorityFit:
    if not eligible:
        return "INELIGIBLE"
    key = (source_key or "").strip().lower()
    if not key:
        return "UNKNOWN"
    policy = CLAIM_AUTHORITY_POLICY.get(claim_type) or CLAIM_AUTHORITY_POLICY["UNKNOWN"]
    if key in policy.get("primary", ()):
        return "PRIMARY"
    if key in policy.get("secondary", ()):
        return "SECONDARY"
    if key in _SAUDI_OFFICIAL:
        return "RELATED"
    return "UNRELATED"


def evaluate_relevance(*, claim_type: ClaimType, candidate: dict[str, Any], question: str | None = None) -> RelevanceState:
    text = " ".join([
        str(candidate.get("statement") or ""),
        str(candidate.get("metric_key") or candidate.get("metric") or ""),
        str(candidate.get("sector") or ""),
        str(question or ""),
    ]).lower()
    source_key = str(candidate.get("source_key") or "").lower()
    metric = str(candidate.get("metric_key") or candidate.get("metric") or "").lower()
    if claim_type == "INFLATION" and any(x in metric or x in text for x in ("cpi", "inflation")):
        return "EXACT" if source_key == "gastat" else "HIGH"
    if claim_type == "GDP" and "gdp" in (metric + " " + text):
        return "EXACT" if source_key == "gastat" else "HIGH"
    if claim_type == "INVESTMENT_FDI" and any(x in metric or x in text for x in ("fdi", "investment")):
        return "EXACT" if source_key == "misa" else "HIGH"
    if claim_type == "LABOR_STATISTIC" and any(x in metric or x in text for x in ("unemployment", "labor", "employment")):
        return "EXACT" if source_key == "gastat" else "HIGH"
    keywords = {
        "INFLATION": ("inflation", "cpi"),
        "GDP": ("gdp",),
        "INVESTMENT_FDI": ("fdi", "investment"),
        "LABOR_STATISTIC": ("unemployment", "labor", "employment"),
        "SME_STATISTIC": ("sme", "msme"),
        "PRICING": ("price", "pricing"),
        "COMPETITOR": ("competitor",),
    }
    keys = keywords.get(claim_type, ())
    if keys and any(k in text for k in keys):
        return "HIGH"
    if claim_type in {"OTHER", "UNKNOWN"}:
        return "PARTIAL" if text.strip() else "UNKNOWN"
    if source_key in {"gastat", "misa"} and keys and not any(k in text for k in keys):
        return "LOW"
    return "PARTIAL" if text.strip() else "UNKNOWN"


def evaluate_geography(*, candidate: dict[str, Any], expected_geography: str | None = "SA") -> GeographyFit:
    geo = candidate.get("geography") or candidate.get("country") or candidate.get("geo")
    source_key = str(candidate.get("source_key") or "").lower()
    if geo is None or str(geo).strip() == "":
        return "COUNTRY" if source_key in _SAUDI_OFFICIAL else "UNKNOWN"
    g = str(geo).strip().upper()
    expected = (expected_geography or "SA").strip().upper()
    saudi = {"SA", "SAU", "KSA", "SAUDI", "SAUDI ARABIA", "KINGDOM OF SAUDI ARABIA"}
    if expected in saudi:
        if g in {"SA", "SAU", "KSA"}:
            return "EXACT"
        if g in saudi:
            return "COUNTRY"
        if g in {"GCC", "MENA", "MIDDLE EAST"}:
            return "REGIONAL"
        if g in {"GLOBAL", "WORLD", "INTERNATIONAL"}:
            return "BROAD"
        return "MISMATCH"
    return "EXACT" if g == expected else "UNKNOWN"


def evaluate_provenance(candidate: dict[str, Any]) -> ProvenanceState:
    url = candidate.get("official_url") or candidate.get("source_url")
    doc = candidate.get("document_id") or candidate.get("source_document_id")
    chunk = candidate.get("chunk_id")
    source_key = candidate.get("source_key")
    published = candidate.get("published_at")
    score = sum(bool(x) for x in (url, doc, chunk, source_key, published))
    if score >= 4:
        return "COMPLETE"
    if score >= 1:
        return "PARTIAL"
    return "MISSING"


def _ranks(authority: AuthorityFit, relevance: RelevanceState, freshness: FreshnessState, geography: GeographyFit, provenance: ProvenanceState):
    auth = {"PRIMARY": 100, "SECONDARY": 80, "RELATED": 55, "UNKNOWN": 35, "UNRELATED": 15, "INELIGIBLE": 0}[authority]
    rel = {"EXACT": 100, "HIGH": 80, "PARTIAL": 50, "UNKNOWN": 30, "LOW": 15, "NONE": 0}[relevance]
    fr = {"CURRENT": 100, "ACCEPTABLE": 70, "NOT_APPLICABLE": 60, "UNKNOWN": 40, "STALE": 15}[freshness]
    geo = {"EXACT": 100, "COUNTRY": 85, "REGIONAL": 55, "BROAD": 35, "UNKNOWN": 40, "MISMATCH": 10}[geography]
    prov = {"COMPLETE": 100, "PARTIAL": 65, "MISSING": 20, "INVALID": 0}[provenance]
    return QualityComponents(authority=auth, relevance=rel, freshness=fr, geography=geo, provenance=prov)


def compose_quality_score(components: QualityComponents) -> tuple[int, QualityState]:
    score = int(round(0.30 * components.authority + 0.25 * components.relevance + 0.20 * components.freshness + 0.15 * components.geography + 0.10 * components.provenance))
    score = max(0, min(100, score))
    if score >= 80:
        return score, "HIGH"
    if score >= 55:
        return score, "MEDIUM"
    if score > 0:
        return score, "LOW"
    return score, "UNKNOWN"


def source_trust_bonus(candidate: dict[str, Any]) -> float:
    trust = candidate.get("trust_score")
    quality = candidate.get("source_quality_score", candidate.get("quality_score"))
    try:
        t = float(trust) if trust is not None else 0.0
    except (TypeError, ValueError):
        t = 0.0
    try:
        q = float(quality) if quality is not None else 0.0
    except (TypeError, ValueError):
        q = 0.0
    if t > 1.0:
        t /= 100.0
    if q > 1.0:
        q /= 100.0
    return max(0.0, min(1.0, 0.7 * t + 0.3 * q))


def evaluate_candidate(
    candidate: dict[str, Any],
    *,
    claim_type: ClaimType | None = None,
    question: str | None = None,
    expected_geography: str | None = "SA",
    as_of: datetime | None = None,
) -> EvidenceQualityResult:
    eid = candidate_evidence_id(candidate)
    ctype: ClaimType = claim_type or classify_claim_type(
        text=str(candidate.get("statement") or question or ""),
        metric_key=str(candidate["metric_key"]) if candidate.get("metric_key") is not None else None,
        research_type=str(candidate["research_type"]) if candidate.get("research_type") is not None else None,
    )
    eligible, elig_reasons = is_eligible_evidence(candidate)
    source_key = str(candidate["source_key"]).strip().lower() if candidate.get("source_key") else None
    authority = authority_fit_for_source(claim_type=ctype, source_key=source_key, eligible=eligible)
    relevance: RelevanceState = evaluate_relevance(claim_type=ctype, candidate=candidate, question=question) if eligible else "NONE"
    freshness, pub_iso, fresh_reasons = evaluate_freshness(
        claim_type=ctype,
        published_at=candidate.get("published_at"),
        retrieved_at=candidate.get("retrieved_at") or candidate.get("retrieved_date"),
        as_of=as_of,
    )
    geography = evaluate_geography(candidate=candidate, expected_geography=expected_geography)
    if not eligible:
        provenance: ProvenanceState = "INVALID" if "invalid_url" in elig_reasons else "MISSING"
        selection: SelectionStatus = "REJECTED_AI_ASSUMPTION" if "ai_assumption_ineligible" in elig_reasons else "REJECTED_INELIGIBLE"
        score, qstate = 0, "UNKNOWN"
    else:
        provenance = evaluate_provenance(candidate)
        selection = "UNRANKED"
        comps = _ranks(authority, relevance, freshness, geography, provenance)
        score, qstate = compose_quality_score(comps)
    comps = _ranks(authority, relevance, freshness, geography, provenance)
    reasons = list(elig_reasons) + list(fresh_reasons) + [f"authority_fit={authority}", f"relevance={relevance}", f"geography={geography}"]
    retrieved = candidate.get("retrieved_at") or candidate.get("retrieved_date")
    return EvidenceQualityResult(
        evidence_id=eid,
        claim_type=ctype,
        eligible=eligible,
        authority_fit=authority,
        relevance=relevance,
        freshness=freshness,
        geography_fit=geography,
        provenance=provenance,
        quality_score=score,
        quality_state=qstate,
        quality_components=comps,
        selection_status=selection,
        ranking_reason=reasons,
        selection_reason_codes=list(elig_reasons),
        source_key=source_key,
        published_at=pub_iso,
        retrieved_at=str(retrieved) if retrieved is not None else None,
    )


def ranking_tuple(result: EvidenceQualityResult, candidate: dict[str, Any]) -> tuple:
    return (
        1 if result.eligible else 0,
        _AUTHORITY_RANK.get(result.authority_fit, 0),
        {"EXACT": 5, "HIGH": 4, "PARTIAL": 3, "UNKNOWN": 2, "LOW": 1, "NONE": 0}.get(result.relevance, 2),
        {"CURRENT": 4, "ACCEPTABLE": 3, "NOT_APPLICABLE": 2, "UNKNOWN": 1, "STALE": 0}.get(result.freshness, 1),
        {"EXACT": 5, "COUNTRY": 4, "REGIONAL": 3, "BROAD": 2, "UNKNOWN": 1, "MISMATCH": 0}.get(result.geography_fit, 1),
        {"COMPLETE": 3, "PARTIAL": 2, "MISSING": 1, "INVALID": 0}.get(result.provenance, 1),
        int(round(source_trust_bonus(candidate) * 1000)),
        result.quality_score,
        result.evidence_id,
    )


def _norm(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _norm_unit(unit: Any) -> str | None:
    if unit is None:
        return None
    u = str(unit).strip().lower()
    return {"%": "percent", "pct": "percent", "percent": "percent", "percentage": "percent", "sar": "sar", "riyal": "sar"}.get(u, u)


def _norm_geo(geo: Any) -> str | None:
    if geo is None:
        return None
    g = str(geo).strip().upper()
    if g in {"SA", "SAU", "KSA", "SAUDI", "SAUDI ARABIA", "KINGDOM OF SAUDI ARABIA"}:
        return "SA"
    return g or None


def comparable_key(candidate: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    return (
        _norm(candidate.get("metric_key") or candidate.get("metric")),
        _norm(candidate.get("period")),
        _norm_geo(candidate.get("geography") or candidate.get("country") or candidate.get("geo")),
        _norm_unit(candidate.get("unit")),
    )


def values_differ(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) > 1e-9
    except (TypeError, ValueError):
        return str(a).strip() != str(b).strip()


def classify_non_conflict(a: dict[str, Any], b: dict[str, Any]) -> ConflictStatus | None:
    ma, pa, ga, ua = comparable_key(a)
    mb, pb, gb, ub = comparable_key(b)
    if not ma or not mb or ma != mb:
        return None
    if pa and pb and pa != pb:
        return "TEMPORAL_CHANGE"
    if ga and gb and ga != gb:
        return "SCOPE_MISMATCH"
    if ua and ub and ua != ub:
        return "SCOPE_MISMATCH"
    return None


def detect_and_resolve_conflicts(candidates: list[dict[str, Any]], evaluations: list[EvidenceQualityResult]) -> list[ConflictResult]:
    by_id = {e.evidence_id: e for e in evaluations}
    cand_by_id = {}
    for c in candidates:
        eid = candidate_evidence_id(c)
        cand_by_id[eid] = c
    groups: dict[tuple, list[str]] = {}
    for eid, c in cand_by_id.items():
        ev = by_id.get(eid)
        if ev is None or not ev.eligible:
            continue
        metric, period, geography, unit = comparable_key(c)
        if not metric or period is None or geography is None:
            continue
        groups.setdefault((metric, period, geography, unit or ""), []).append(eid)
    results: list[ConflictResult] = []
    for key, eids in groups.items():
        if len(eids) < 2:
            continue
        metric, period, geography, unit = key
        values = [cand_by_id[eid].get("value") for eid in eids]
        distinct: list[Any] = []
        for v in values:
            if not any(not values_differ(v, d) for d in distinct):
                distinct.append(v)
        if len(distinct) <= 1:
            continue
        group_id = hashlib.sha256(f"{metric}|{period}|{geography}|{unit}|{','.join(sorted(eids))}".encode()).hexdigest()[:16]
        ranked = sorted(eids, key=lambda i: ranking_tuple(by_id[i], cand_by_id[i]), reverse=True)
        top, second = by_id[ranked[0]], by_id[ranked[1]]
        top_key = ranking_tuple(top, cand_by_id[top.evidence_id])[:-1]
        second_key = ranking_tuple(second, cand_by_id[second.evidence_id])[:-1]
        clear = _AUTHORITY_RANK[top.authority_fit] > _AUTHORITY_RANK[second.authority_fit] and ranking_tuple(top, cand_by_id[top.evidence_id])[2] >= ranking_tuple(second, cand_by_id[second.evidence_id])[2]
        if top_key > second_key and (top.authority_fit == "PRIMARY" or clear):
            status: ConflictStatus = "RESOLVED_PREFERRED_SOURCE"
            preferred: str | None = top.evidence_id
            reasons = ["deterministic_preferred_source", f"preferred={top.source_key}", f"authority={top.authority_fit}"]
            explanation = f"Comparable conflict on {metric} for {period}/{geography}; preferred {top.source_key}."
        else:
            status = "UNRESOLVED"
            preferred = None
            reasons = ["equal_or_ambiguous_quality", "no_automatic_resolution"]
            explanation = f"Comparable conflict on {metric} for {period}/{geography}; left UNRESOLVED."
        results.append(ConflictResult(
            conflict_group_id=group_id,
            metric=metric,
            period=period,
            geography=geography,
            unit=unit or None,
            status=status,
            candidates=list(ranked),
            preferred_evidence_ref=preferred,
            reason_codes=reasons,
            explanation=explanation,
            values=list(distinct),
        ))
    return results


def _as_candidate(item: Any, *, question: str | None = None) -> dict[str, Any]:
    if isinstance(item, dict):
        out = dict(item)
    else:
        out = {
            "statement": getattr(item, "statement", None),
            "source_type": getattr(item, "source_type", None),
            "source_url": getattr(item, "source_url", None),
            "official_url": getattr(item, "source_url", None),
            "retrieved_date": getattr(item, "retrieved_date", None),
            "retrieved_at": getattr(item, "retrieved_at", None) or getattr(item, "retrieved_date", None),
            "published_at": getattr(item, "published_at", None),
            "confidence": getattr(item, "confidence", None),
            "metric_key": getattr(item, "metric_key", None),
            "value": getattr(item, "value", None),
            "unit": getattr(item, "unit", None),
            "period": getattr(item, "period", None),
            "source_key": getattr(item, "source_key", None),
            "document_id": getattr(item, "document_id", None),
            "chunk_id": getattr(item, "chunk_id", None),
            "origin": getattr(item, "origin", None),
            "geography": getattr(item, "geography", None),
            "trust_score": getattr(item, "trust_score", None),
            "authority_type": getattr(item, "authority_type", None),
            "evidence_id": getattr(item, "evidence_id", None),
        }
    if question and not out.get("question"):
        out["question"] = question
    if out.get("official_url") is None and out.get("source_url"):
        out["official_url"] = out.get("source_url")
    out["evidence_id"] = candidate_evidence_id(out)
    return out


def evaluate_research_quality(
    evidence_candidates: Sequence[Any],
    *,
    question: str | None = None,
    claim_type: ClaimType | None = None,
    expected_geography: str | None = "SA",
    as_of: datetime | None = None,
    metric_key: str | None = None,
) -> QualityEvaluationResult:
    as_of_dt = as_of or datetime.now(timezone.utc)
    if as_of_dt.tzinfo is None:
        as_of_dt = as_of_dt.replace(tzinfo=timezone.utc)
    candidates = [_as_candidate(c, question=question) for c in evidence_candidates]
    resolved: ClaimType = claim_type or classify_claim_type(text=question, metric_key=metric_key)
    if resolved in {"UNKNOWN", "OTHER"} and candidates:
        resolved = classify_claim_type(
            text=str(candidates[0].get("statement") or question or ""),
            metric_key=str(candidates[0]["metric_key"]) if candidates[0].get("metric_key") is not None else metric_key,
        )
    evaluations = [
        evaluate_candidate(c, claim_type=resolved, question=question, expected_geography=expected_geography, as_of=as_of_dt)
        for c in candidates
    ]
    indexed = list(zip(evaluations, candidates))
    indexed.sort(key=lambda pair: ranking_tuple(pair[0], pair[1]), reverse=True)
    ranked: list[EvidenceQualityResult] = []
    preferred_ids: list[str] = []
    position = 1
    for ev, _c in indexed:
        ev.ranking_position = position if ev.eligible else None
        if ev.eligible:
            if not preferred_ids:
                ev.selection_status = "PREFERRED"
                ev.selection_reason_codes = list(dict.fromkeys(ev.selection_reason_codes + ["top_ranked_eligible"]))
                preferred_ids.append(ev.evidence_id)
            elif ev.selection_status == "UNRANKED":
                ev.selection_status = "ALTERNATE"
                ev.selection_reason_codes = list(dict.fromkeys(ev.selection_reason_codes + ["ranked_alternate"]))
            position += 1
        ranked.append(ev)
    conflicts = detect_and_resolve_conflicts(candidates, ranked)
    for conflict in conflicts:
        if conflict.status == "RESOLVED_PREFERRED_SOURCE" and conflict.preferred_evidence_ref:
            preferred_ids = [conflict.preferred_evidence_ref]
            for ev in ranked:
                if ev.evidence_id == conflict.preferred_evidence_ref:
                    ev.selection_status = "PREFERRED"
                    if "conflict_preferred" not in ev.selection_reason_codes:
                        ev.selection_reason_codes.append("conflict_preferred")
                elif ev.eligible and ev.evidence_id in conflict.candidates:
                    if ev.selection_status == "PREFERRED":
                        ev.selection_status = "ALTERNATE"
                    if "conflict_non_preferred" not in ev.selection_reason_codes:
                        ev.selection_reason_codes.append("conflict_non_preferred")
    return QualityEvaluationResult(
        policy_version=RESEARCH_QUALITY_POLICY_VERSION,
        claim_type=resolved,
        evaluations=ranked,
        preferred_evidence_ids=preferred_ids,
        conflicts=conflicts,
        as_of=as_of_dt.isoformat(),
    )


def enrich_claims_with_quality(claims: Sequence[Any], quality: QualityEvaluationResult) -> list[dict[str, Any]]:
    by_id = {e.evidence_id: e for e in quality.evaluations}
    conflict_by_eid: dict[str, dict[str, Any]] = {}
    for c in quality.conflicts:
        payload = c.to_public_dict()
        for eid in c.candidates:
            conflict_by_eid[eid] = payload
    enriched: list[dict[str, Any]] = []
    for claim in claims:
        cand = _as_candidate(claim)
        eid = cand["evidence_id"]
        if hasattr(claim, "to_claim_dict"):
            base = dict(claim.to_claim_dict())
            base.update({
                "metric_key": getattr(claim, "metric_key", None),
                "value": getattr(claim, "value", None),
                "unit": getattr(claim, "unit", None),
                "period": getattr(claim, "period", None),
                "source_key": getattr(claim, "source_key", None),
                "from_knowledge": getattr(claim, "from_knowledge", False),
                "published_at": getattr(claim, "published_at", None),
            })
        elif isinstance(claim, dict):
            base = dict(claim)
        else:
            base = cand
        ev = by_id.get(eid)
        base["research_quality"] = {
            "policy_version": quality.policy_version,
            "claim_type": quality.claim_type,
            "evaluation": ev.to_public_dict() if ev else None,
            "conflict": conflict_by_eid.get(eid),
            "preferred_evidence_ids": list(quality.preferred_evidence_ids),
        }
        base["evidence_id"] = eid
        enriched.append(base)
    return enriched
