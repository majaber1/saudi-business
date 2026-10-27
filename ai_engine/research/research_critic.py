"""Claim lineage review.

The critic records why a claim cannot be source-backed evidence. It does not
invent a replacement citation, date, or number.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

_OFFICIAL_HOSTS = (
    "stats.gov.sa",
    "www.stats.gov.sa",
    "gastat.gov.sa",
    "misa.gov.sa",
    "www.misa.gov.sa",
)

_FOREIGN_PLACE = (
    "dubai",
    "abu dhabi",
    "united arab emirates",
    "bahrain",
    "kuwait",
    "qatar",
    "egypt",
    "united states",
    "u.s.a",
)


def _field(claim: Any, key: str) -> Any:
    if isinstance(claim, dict):
        return claim.get(key)
    return getattr(claim, key, None)


def _http_url(url: Any) -> bool:
    return isinstance(url, str) and url.strip().lower().startswith(("https://", "http://"))


def _host(url: Any) -> str:
    if not _http_url(url):
        return ""
    return (urlparse(str(url).strip()).hostname or "").lower()


def _authority(source_type: str, url: Any) -> str:
    if source_type == "ai_assumption":
        return "ai_estimate"
    if source_type == "user_input":
        return "owner_assumption"
    host = _host(url)
    if host in _OFFICIAL_HOSTS or host.endswith(".stats.gov.sa") or host.endswith(".misa.gov.sa"):
        return "official"
    if source_type in {"official", "document"} and _http_url(url):
        return "third_party"
    return "unsourced"


def review_claim_lineage(
    claims: list[Any] | None,
    *,
    geography: str = "Saudi Arabia",
) -> dict[str, Any]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    estimates: list[dict[str, Any]] = []
    expects_saudi = "saudi" in geography.casefold() or "riyadh" in geography.casefold()

    for claim in claims or []:
        statement = str(_field(claim, "statement") or "")
        source_type = str(_field(claim, "source_type") or "unverified")
        url = _field(claim, "source_url")
        authority = _authority(source_type, url)
        reasons: list[str] = []
        if source_type == "ai_assumption" or authority == "ai_estimate":
            estimates.append(
                {
                    "statement": statement,
                    "authority": "ai_estimate",
                    "reason": "ai_estimate_is_not_source_evidence",
                }
            )
            continue
        if source_type in {"official", "document"} and not _http_url(url):
            reasons.append("missing_http_url")
        text = statement.casefold()
        names_foreign = any(token in text for token in _FOREIGN_PLACE)
        names_saudi = "saudi" in text or "riyadh" in text or "السعود" in text
        if expects_saudi and names_foreign and not names_saudi:
            reasons.append("geographic_mismatch")
        elif expects_saudi and names_foreign and names_saudi:
            reasons.append("conflicting_geography")
        if "usd" in text and ("sar" in text or "ريال" in text):
            reasons.append("conflicting_currency")
        row = {
            "statement": statement,
            "source_type": source_type,
            "authority": authority,
            "source_url": url if _http_url(url) else None,
        }
        if reasons:
            rejected.append({**row, "reasons": reasons})
        else:
            accepted.append(row)

    source_backed = [row for row in accepted if row["authority"] in {"official", "third_party"}]
    return {
        "accepted_count": len(accepted),
        "source_backed_count": len(source_backed),
        "rejected": rejected,
        "ai_estimates": estimates,
        "unresolved_gaps": [row["reasons"][0] for row in rejected],
        "blocks_investment": len(source_backed) == 0,
    }


def research_investment_ceiling(state: Any) -> str | None:
    """Incomplete or failed research cannot support GO or GO_WITH_CONDITIONS."""
    status = getattr(state, "research_status", None)
    context = getattr(state, "research_context", None) or {}
    if not isinstance(context, dict):
        context = {}
    critic = context.get("research_critic") or {}
    if status == "failed":
        return "INSUFFICIENT_EVIDENCE"
    if status in {"blocked", "partial", "complete"} and critic.get("blocks_investment") is True:
        return "INSUFFICIENT_EVIDENCE"
    return None
