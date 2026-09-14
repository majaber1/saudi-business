"""Normalized numeric observations with full provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class NumericObservation:
    evidence_class: str
    metric: str  # e.g. rent_sar_per_m2_year, menu_item_sar, salary_monthly_sar
    value: float
    unit: str
    currency: str = "SAR"
    geography: str = "Saudi Arabia"
    district: Optional[str] = None
    role_or_item: Optional[str] = None
    period: Optional[str] = None  # month|year|one_time
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    adapter_id: str = ""
    raw_excerpt: str = ""
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_evidence_item(self) -> dict[str, Any]:
        """Shape compatible with operating_estimates / claims pipelines."""
        label = self.role_or_item or self.metric
        statement = (
            f"{self.evidence_class} observation: {label} = {self.value:g} {self.unit} "
            f"({self.currency}). Geography: {self.geography}"
            + (f" / {self.district}" if self.district else "")
            + (f". Period: {self.period}" if self.period else "")
            + f". Adapter: {self.adapter_id}."
        )
        if self.raw_excerpt:
            statement += f" Excerpt: {self.raw_excerpt[:240]}"
        return {
            "statement": statement,
            "content": statement,
            "source_url": self.source_url,
            "url": self.source_url,
            "geography": self.geography,
            "source_key": "commercial_discovery",
            "document_id": f"obs:{self.evidence_class}:{self.metric}:{self.value:g}",
            "evidence_kind": self.evidence_class,
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "adapter_id": self.adapter_id,
            "confidence": self.confidence,
            "retrieved_at": self.retrieved_at,
        }
