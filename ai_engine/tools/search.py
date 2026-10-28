"""Allowlisted Saudi search adapter.

No credential is treated as a result. This module does not fabricate hits,
URLs, or retrieval timestamps. When no allowlisted provider is configured,
search stays BLOCKED. A configured key calls that provider and keeps only
hits that already contain an http(s) URL. The retrieval time is the time
the response was received.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import httpx

ALLOWLISTED_SEARCH_PROVIDERS: tuple[dict[str, str], ...] = (
    {"id": "tavily", "env": "TAVILY_API_KEY"},
    {"id": "brave", "env": "BRAVE_SEARCH_API_KEY"},
)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
_TIMEOUT = httpx.Timeout(12.0, connect=5.0)
_MAX_ATTEMPTS = 2

_ACCEPTED_SOURCE_LABELS = frozenset({"general", "official", "gastat", "misa"})


def configured_search_providers(environ: Mapping[str, str] | None = None) -> list[str]:
    env = environ if environ is not None else os.environ
    found: list[str] = []
    for provider in ALLOWLISTED_SEARCH_PROVIDERS:
        if str(env.get(provider["env"]) or "").strip():
            found.append(provider["id"])
    return found


def _provider_env(provider_id: str) -> str:
    for provider in ALLOWLISTED_SEARCH_PROVIDERS:
        if provider["id"] == provider_id:
            return provider["env"]
    raise KeyError(provider_id)


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
        "status": "READY",
        "reason": None,
        "configured_providers": configured,
        "results": [],
        "implemented": True,
        "message": (
            "An allowlisted provider is configured. "
            "Results are returned only from that provider response."
        ),
    }


def _http_url(url: Any) -> str | None:
    if not isinstance(url, str):
        return None
    value = url.strip()
    lower = value.lower()
    if not (lower.startswith("https://") or lower.startswith("http://")):
        return None
    if "@" in value.split("/", 3)[2]:
        return None
    return value


def _valid_timestamp(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if len(text) < 10 or text[4] != "-" or text[7] != "-":
        return None
    return text


def _dedupe_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    for item in results:
        url = str(item.get("url") or "")
        if url in seen:
            continue
        seen.add(url)
        kept.append(item)
    return kept


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
                "provider": str(data.get("provider") or ""),
            }
        )
    kept = _dedupe_results(kept)
    status = "partial" if dropped and kept else ("complete" if kept else "failed")
    reason = None if kept and not dropped else ("PARTIAL_INVALID_HITS" if kept else "NO_VALID_HITS")
    return {
        "status": status,
        "reason": reason,
        "results": kept,
        "retrieved_at": retrieved_at,
        "partial": bool(dropped and kept),
    }


def map_provider_body(provider_id: str, body: Mapping[str, Any] | None, *, retrieved_at: str) -> dict[str, Any]:
    """Map a provider JSON body into the shared result shape. Unknown fields are dropped."""
    data = dict(body or {})
    raw: list[Any]
    if provider_id == "tavily":
        raw = data.get("results") if isinstance(data.get("results"), list) else []
    elif provider_id == "brave":
        web = data.get("web") if isinstance(data.get("web"), dict) else {}
        raw = web.get("results") if isinstance(web.get("results"), list) else []
    else:
        raw = []
    results: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": item.get("title") or "",
                "url": item.get("url") or "",
                "snippet": item.get("content") or item.get("description") or "",
            }
        )
    return {"provider": provider_id, "retrieved_at": retrieved_at, "results": results}


def provider_request(provider_id: str, query: str, api_key: str) -> dict[str, Any]:
    """Build one provider call. The key stays in the request headers, not in logs."""
    if provider_id == "tavily":
        return {
            "method": "POST",
            "url": TAVILY_SEARCH_URL,
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "json": {"query": query, "max_results": 5, "search_depth": "basic", "include_answer": False},
        }
    if provider_id == "brave":
        return {
            "method": "GET",
            "url": BRAVE_SEARCH_URL,
            "headers": {
                "Accept": "application/json",
                "X-Subscription-Token": api_key,
            },
            "params": {"q": query, "count": 5},
        }
    raise ValueError(f"unsupported search provider: {provider_id}")


def _public_provider_error(status_code: int) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "provider_error": True,
        "results": [],
    }


def fetch_provider_payload(
    provider_id: str,
    api_key: str,
    query: str,
    client: Any,
) -> dict[str, Any]:
    """Call the provider. Retry once on timeout or a 5xx response. Do not retry a rate limit."""
    request = provider_request(provider_id, query, api_key)
    last_timeout: BaseException | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.request(
                request["method"],
                request["url"],
                headers=request.get("headers"),
                json=request.get("json"),
                params=request.get("params"),
            )
        except (httpx.TimeoutException, TimeoutError) as exc:
            last_timeout = exc
            if attempt + 1 < _MAX_ATTEMPTS:
                continue
            raise TimeoutError("search provider timed out") from last_timeout
        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code == 429:
            return _public_provider_error(429)
        if status_code >= 500 and attempt + 1 < _MAX_ATTEMPTS:
            continue
        if status_code >= 400:
            return _public_provider_error(status_code)
        body = response.json() if hasattr(response, "json") else {}
        if not isinstance(body, dict):
            body = {}
        retrieved_at = datetime.now(timezone.utc).isoformat()
        payload = map_provider_body(provider_id, body, retrieved_at=retrieved_at)
        payload["status_code"] = status_code
        return payload
    return _public_provider_error(500)


def execute_allowlisted_search(
    query: str,
    *,
    source: str = "general",
    transport: Callable[[str], Mapping[str, Any]] | None = None,
    environ: Mapping[str, str] | None = None,
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
            "implemented": True,
            "message": "The requested source is not on the search allowlist.",
        }
    if not str(query or "").strip():
        return {
            "query": query,
            "source": source,
            "status": "BLOCKED",
            "reason": "EMPTY_QUERY",
            "results": [],
            "implemented": True,
            "message": "An empty query was not sent to a provider.",
        }
    if transport is None:
        blocked = search_availability(environ)
        if blocked["status"] != "READY":
            return {"query": query, "source": source, **blocked}
        return {
            "query": query,
            "source": source,
            "status": "BLOCKED",
            "reason": "TRANSPORT_NOT_PROVIDED",
            "configured_providers": blocked["configured_providers"],
            "results": [],
            "implemented": True,
            "message": "No provider transport was supplied. No results were fabricated.",
        }
    try:
        payload = transport(query)
    except TimeoutError:
        return {
            "query": query,
            "source": source,
            "status": "failed",
            "reason": "TIMEOUT",
            "results": [],
            "implemented": True,
            "message": "The search provider timed out. No fallback results were created.",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "query": query,
            "source": source,
            "status": "failed",
            "reason": "PROVIDER_ERROR",
            "results": [],
            "implemented": True,
            "message": "Search provider failed.",
            "error_type": type(exc).__name__,
        }
    status_code = int(payload.get("status_code") or 0)
    if status_code == 429:
        return {
            "query": query,
            "source": source,
            "status": "failed",
            "reason": "RATE_LIMIT",
            "results": [],
            "implemented": True,
            "message": "The search provider rate-limited the request. No fallback results were created.",
        }
    if status_code >= 400 or payload.get("provider_error"):
        return {
            "query": query,
            "source": source,
            "status": "failed",
            "reason": "PROVIDER_ERROR",
            "results": [],
            "implemented": True,
            "status_code": status_code,
            "message": "The search provider returned an error. No fallback results were created.",
        }
    normalized = normalize_provider_payload(payload)
    return {
        "query": query,
        "source": source,
        "implemented": True,
        "provider": payload.get("provider"),
        "message": "Provider payload normalized. Invalid hits were dropped, not repaired.",
        **normalized,
    }


def run_configured_search(
    query: str,
    *,
    source: str = "general",
    environ: Mapping[str, str] | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Call the first configured allowlisted provider. Without a key, stay BLOCKED."""
    env = environ if environ is not None else os.environ
    configured = configured_search_providers(env)
    if not configured:
        return execute_allowlisted_search(query, source=source, transport=None, environ=env)
    provider_id = configured[0]
    api_key = str(env.get(_provider_env(provider_id)) or "").strip()
    owns_client = client is None
    http = client if client is not None else httpx.Client(timeout=_TIMEOUT, verify=True, follow_redirects=False)

    def transport(text: str) -> dict[str, Any]:
        return fetch_provider_payload(provider_id, api_key, text, http)

    try:
        result = execute_allowlisted_search(query, source=source, transport=transport, environ=env)
    finally:
        if owns_client:
            http.close()
    result["configured_providers"] = configured
    result["provider"] = provider_id
    return result


async def search_saudi_data(
    query: str,
    source: str = "general",
    *,
    environ: Mapping[str, str] | None = None,
    client: Any | None = None,
) -> dict:
    """Public search entry. Stays BLOCKED until an allowlisted credential is configured."""
    if source not in _ACCEPTED_SOURCE_LABELS and source not in {
        item["id"] for item in ALLOWLISTED_SEARCH_PROVIDERS
    }:
        return execute_allowlisted_search(query, source=source, transport=None, environ=environ)
    return run_configured_search(query, source=source, environ=environ, client=client)
