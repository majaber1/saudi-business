"""Reject official evidence that has no real citation.

The critic does not invent a URL or a retrieval date. A claim that fails
stays out of the official evidence list.
"""
from __future__ import annotations

from ai_engine.research.schemas import ResearchClaim


def _http_url(url: str | None) -> bool:
    if not isinstance(url, str):
        return False
    value = url.strip().lower()
    return value.startswith("https://") or value.startswith("http://")


def screen_research_citations(
    claims: list[ResearchClaim] | None,
) -> tuple[list[ResearchClaim], list[str]]:
    """Keep sourced official and document claims. Drop the rest of those types.

    Other source types are returned unchanged. This function does not write
    a source_url or retrieved_date onto any claim.
    """
    accepted: list[ResearchClaim] = []
    rejected: list[str] = []
    for claim in claims or []:
        if claim.source_type in {"official", "document"} and not _http_url(claim.source_url):
            rejected.append(f"rejected_unsourced:{claim.source_type}")
            continue
        accepted.append(claim)
    return accepted, rejected
