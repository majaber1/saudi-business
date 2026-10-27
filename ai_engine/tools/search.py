"""Allowlisted Saudi search adapter.

No credential is treated as a result. This module does not fabricate hits,
URLs, or retrieval timestamps. When no allowlisted provider is configured,
search stays BLOCKED.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Mapping

ALLOWLISTED_SEARCH_PROVIDERS: tuple[dict[str, str], ...] = (
    {"id": "tavily", "env": "TAVILY_API_KEY"},
    {"id": "brave", "env": "BRAVE_SEARCH_API_KEY"},
)

_ACCEPTED_SOURCE_LABELS = frozenset({"general", "official", "gastat", "misa"})


def configured_search_providers(environ: Mapping[str, str] | None = None) -> list[str]:
    env = environ if environ is not None else os.environ
    found: list[str] = []
    for provider in ALLOWLISTED_SEARCH_PROVIDERS:
        if str(env.get(provider["env"]) or "").strip():
            found.append(provider["id"])
    return found


def search_availability(environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    configured = configured_search_providers(environ)
    if not configured:
        return {
            "status": "BLOCKED",
            "reason": "NO_ALLOWLISTED_PROVIDER_CONFIGURED",
            "configured_providers": [],
            "results": [],
            "implemented": False,
            "message": (
                "No allowlisted search credential is configured. "
                "Search was not executed and no results were fabricated."
            ),
        }
    return {
        "status": "BLOCKED",
        "reason": "PROVIDER_CREDENTIAL_PRESENT_BUT_CLIENT_NOT_ENABLED",
        "configured_providers": configured,
        "results": [],
        "implemented": False,
        "message": (
            "An allowlisted credential is present, but this build does not call the provider. "
            "No results were fabricated."
        ),
    }


def _http_url(url: Any) -> str | None:
    if not isinstance(url, str):
        return None
    value = url.strip()
    lower = value.lower()
    if lower.startswith("https://") or lower.startswith("http://"):
        return value
    return None


def _valid_timestamp(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if len(text) < 10 or text[4] != "-" or text[7] != "-":
        return None
    return text


def normalize_provider_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Keep only hits that already carry an http(s) URL and a retrieval timestamp."""
    data = dict(payload or {})
    retrieved_at = _valid_timestamp(data.get("retrieved_at"))
    raw_results = data.get("results") or []
    if not isinstance(raw_results, list):
        raw_results = []
    if retrieved_at is None:
        return {
            "status": "failed",
            "reason": "MISSING_RETRIEVAL_TIMESTAMP",
            "results": [],
            "retrieved_at": None,
            "partial": False,
        }
    kept: list[dict[str, Any]] = []
    dropped = 0
    for item in raw_results:
        if not isinstance(item, dict):
            dropped += 1
            continue
        url = _http_url(item.get("url") or item.get("source_url"))
        if url is None:
            dropped += 1
            continue
        kept.append(
            {
                "title": str(item.get("title") or ""),
                "url": url,
                "snippet": str(item.get("snippet") or item.get("content") or ""),
                "retrieved_at": retrieved_at,
            }
        )
    status = "partial" if dropped and kept else ("complete" if kept else "failed")
    reason = None if kept and not dropped else ("PARTIAL_INVALID_HITS" if kept else "NO_VALID_HITS")
    return {
        "status": status,
        "reason": reason,
        "results": kept,
        "retrieved_at": retrieved_at,
        "partial": bool(dropped and kept),
    }


def execute_allowlisted_search(
    query: str,
    *,
    source: str = "general",
    transport: Callable[[str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run an injected provider transport. A missing transport does not invent hits."""
    if source not in _ACCEPTED_SOURCE_LABELS and source not in {
        item["id"] for item in ALLOWLISTED_SEARCH_PROVIDERS
    }:
        return {
            "query": query,
            "source": source,
            "status": "BLOCKED",
            "reason": "INVALID_SOURCE",
            "results": [],
            "implemented": False,
            "message": "The requested source is not on the search allowlist.",
        }
    if transport is None:
        blocked = search_availability()
        return {"query": query, "source": source, **blocked}
    try:
        payload = transport(query)
    except TimeoutError:
        return {
            "query": query,
            "source": source,
            "status": "failed",
            "reason": "TIMEOUT",
            "results": [],
            "implemented": False,
            "message": "The search provider timed out. No fallback results were created.",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "query": query,
            "source": source,
            "status": "failed",
            "reason": "PROVIDER_ERROR",
            "results": [],
            "implemented": False,
            "message": f"Search provider failed: {exc}",
        }
    if int(payload.get("status_code") or 0) == 429:
        return {
            "query": query,
            "source": source,
            "status": "failed",
            "reason": "RATE_LIMIT",
            "results": [],
            "implemented": False,
            "message": "The search provider rate-limited the request. No fallback results were created.",
        }
    normalized = normalize_provider_payload(payload)
    return {
        "query": query,
        "source": source,
        "implemented": True,
        "message": "Provider payload normalized. Invalid hits were dropped, not repaired.",
        **normalized,
    }


async def search_saudi_data(query: str, source: str = "general") -> dict:
    """Public search entry. Stays BLOCKED until an allowlisted provider is configured and enabled."""
    if source not in _ACCEPTED_SOURCE_LABELS:
        return execute_allowlisted_search(query, source=source, transport=None)
    availability = search_availability()
    return {"query": query, "source": source, **availability}
