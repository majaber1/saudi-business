"""Commercial discovery SourceConnector — multi-source competitors / location / pricing.

Governed live retrieval for local-business research depth. Reuses SafePageReader
allowlists and the SourceConnector contract. Never invents competitors, rents,
or prices. Documents multi-source search exhaustion when nothing is found.

Sources attempted (in order, all recorded):
1. OpenStreetMap Nominatim — named POIs + geocoding
2. DuckDuckGo HTML — multi-query discovery + follow allowlisted result pages
3. Wikipedia REST — district/city operating-context summaries
4. Overpass API (best-effort) — amenity density near geocoded point

Generic across business types: amenity/query terms are inferred from the
free-text research query (sector / idea / city), not hardcoded to coffee.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote_plus, urlparse

import httpx

from app.integrations.research.page_reader import PageFetchError, SafePageReader
from app.integrations.research.security import UrlSecurityError, canonicalize_url

from .base import ConnectorHealth, ConnectorStatus, SourceConnector, utcnow
from .schemas import (
    AuthorityType,
    Provenance,
    SourceDocument,
    SourceType,
    VerificationEligibility,
)
from .validation import compute_content_hash

CONNECTOR_ID = "live.commercial_discovery"
REGISTRY_KEY = "commercial_discovery"
SEARCH_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
USER_AGENT = (
    "SaudiBusinessBot/parity (+https://saudi-business.local; governed commercial research; "
    "contact=ops@saudi-business.local)"
)

# Minimal bootstrap allowlist (geo + search + official). Full commercial follow
# allowlist is resolved per-request from evidence-class source strategy so new
# sectors reuse domain/evidence classes instead of coffee-only domain patches.
COMMERCIAL_ALLOWED_DOMAINS: tuple[str, ...] = (
    "nominatim.openstreetmap.org",
    "openstreetmap.org",
    "www.openstreetmap.org",
    "overpass-api.de",
    "html.duckduckgo.com",
    "duckduckgo.com",
    "www.bing.com",
    "bing.com",
    "en.wikipedia.org",
    "ar.wikipedia.org",
    "wikipedia.org",
    "stats.gov.sa",
    "www.stats.gov.sa",
    "misa.gov.sa",
    "www.misa.gov.sa",
)

# Generic query-term → OSM amenity tag. Not coffee-specific product logic.
_AMENITY_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("coffee", "café", "cafe", "specialty coffee", "مقهى", "قهوة"), "cafe"),
    (("restaurant", "dining", "fnb", "f&b", "مطعم", "food service"), "restaurant"),
    (("bakery", "مخبز"), "bakery"),
    (("gym", "fitness", "نادي"), "fitness_centre"),
    (("hotel", "فندق"), "hotel"),
    (("clinic", "healthcare", "عيادة", "مستشفى", "hospital"), "clinic"),
    (("pharmacy", "صيدلية"), "pharmacy"),
    (("school", "education", "مدرسة", "تعليم"), "school"),
    (("retail", "shop", "store", "متجر", "retail store"), "shop"),
    (("salon", "barber", "صالة"), "hairdresser"),
)

_RENT_RE = re.compile(
    r"(?:SAR|SR|ر\.?\s*س|ريال)\s*([0-9][0-9,]{2,6})|"
    r"([0-9][0-9,]{2,6})\s*(?:SAR|SR|ر\.?\s*س|ريال)"
    r"(?:\s*(?:/?\s*m(?:2|²)|per\s*m(?:2|²)|/mo(?:nth)?|/month|شهري))?",
    re.I,
)
_PRICE_RE = re.compile(
    r"(?:SAR|SR|ر\.?\s*س|ريال)\s*([0-9]{1,4}(?:\.\d+)?)|"
    r"([0-9]{1,4}(?:\.\d+)?)\s*(?:SAR|SR|ر\.?\s*س|ريال)",
    re.I,
)
_DDG_RESULT_RE = re.compile(
    r'class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>'
    r'.*?class="result__snippet"[^>]*>(?P<snippet>.*?)</(?:a|td)>',
    re.I | re.S,
)
_TAG_RE = re.compile(r"<[^>]+>")


def infer_amenity_tag(query: str) -> str:
    blob = (query or "").lower()
    for markers, tag in _AMENITY_RULES:
        if any(m in blob for m in markers):
            return tag
    return "commercial"


def infer_city_district(query: str) -> tuple[str, str]:
    """Best-effort geography tokens from free text. Empty when unknown."""
    text = query or ""
    city = ""
    district = ""
    city_markers = (
        ("riyadh", "Riyadh"),
        ("jeddah", "Jeddah"),
        ("dammam", "Dammam"),
        ("khobar", "Khobar"),
        ("makkah", "Makkah"),
        ("madinah", "Madinah"),
        ("الرياض", "الرياض"),
        ("جدة", "جدة"),
        ("الدمام", "الدمام"),
    )
    lower = text.lower()
    for marker, label in city_markers:
        if marker in lower:
            city = label
            break

    known_districts = (
        ("olaya", "Olaya"),
        ("ulaya", "Olaya"),
        ("العليا", "العليا"),
        ("malaz", "Malaz"),
        ("sulaimaniyah", "Sulaimaniyah"),
        ("rawdah", "Rawdah"),
        ("nuzha", "Nuzha"),
        ("yasmin", "Yasmin"),
        ("hamra", "Hamra"),
    )
    for marker, label in known_districts:
        if marker in lower:
            district = label
            break

    if not district:
        m = re.search(
            r"(?:in|near|at|بحي|في)\s+([A-Za-z\u0600-\u06FF][A-Za-z0-9\u0600-\u06FF\-]{1,30})",
            text,
            re.I,
        )
        if m:
            token = m.group(1).strip(" ,.")
            # Stop-words that mean the capture overran into the business idea
            if token.lower() not in {
                "saudi",
                "arabia",
                "specialty",
                "coffee",
                "cafe",
                "café",
                "shop",
                "restaurant",
                "local",
                "business",
                "for",
                "the",
            }:
                district = token
    return city, district


def _strip_html(raw: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", raw or "")).strip()



def _unwrap_bing_url(url: str) -> str:
    """Decode Bing /ck/a redirect wrappers to the destination URL when present."""
    if not url:
        return url
    try:
        from html import unescape
        from urllib.parse import parse_qs, unquote, urlparse
        import base64
        import re as _re

        cleaned = unescape(url).replace("&amp;", "&")
        host = (urlparse(cleaned).hostname or "").lower()
        if "bing.com" not in host:
            return cleaned
        qs = parse_qs(urlparse(cleaned).query)
        for key in ("u", "r", "url"):
            vals = qs.get(key) or []
            if not vals:
                continue
            cand = unquote(vals[0])
            if cand.startswith("a1"):
                raw = cand[2:]
                raw += "=" * ((4 - len(raw) % 4) % 4)
                try:
                    decoded = base64.urlsafe_b64decode(raw.encode()).decode("utf-8", "ignore")
                    m = _re.search(r"https?://\S+", decoded)
                    if m:
                        return m.group(0).rstrip("'\"<>")
                except Exception:
                    pass
            if cand.startswith("http"):
                return cand
        return cleaned
    except Exception:
        return url



def _osm_url(osm_type: str, osm_id: Any) -> Optional[str]:
    t = (osm_type or "").lower()
    if t not in {"node", "way", "relation"} or osm_id is None:
        return None
    return f"https://www.openstreetmap.org/{t}/{osm_id}"


class CommercialDiscoveryConnector(SourceConnector):
    """Multi-source commercial discovery (competitors, location, pricing signals)."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        timeout_seconds: float = 25.0,
        max_queries: int = 8,
        max_pois: int = 12,
        max_ddg_follow: int = 4,
    ) -> None:
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.max_queries = max_queries
        self.max_pois = max_pois
        self.max_ddg_follow = max_ddg_follow
        self._allowlist: List[str] = list(COMMERCIAL_ALLOWED_DOMAINS)
        self._reader = SafePageReader(
            allowed_domains=self._allowlist,
            timeout_seconds=timeout_seconds,
            user_agent=USER_AGENT,
        )
        self._last_exhaustion: Dict[str, Any] = {}
        self._strategy_meta: Dict[str, Any] = {}
        self._observations: List[Dict[str, Any]] = []

    @property
    def connector_id(self) -> str:
        return CONNECTOR_ID

    @property
    def source_metadata(self) -> Dict[str, Any]:
        return {
            "name": "Commercial Discovery (OSM + web + encyclopedia)",
            "source_type": SourceType.OPEN_DATA.value,
            "authority_type": AuthorityType.COMMERCIAL_SOURCE.value,
            "registry_key": REGISTRY_KEY,
            "allowed_domains": list(self._allowlist or COMMERCIAL_ALLOWED_DOMAINS),
            "retrieval": "multi_source_governed",
            "source_strategy": "evidence_class",
            "strategy_meta": dict(self._strategy_meta or {}),
        }

    def health(self) -> ConnectorHealth:
        if not self.enabled:
            return ConnectorHealth(
                status=ConnectorStatus.DISABLED,
                checked_at=utcnow(),
                detail="commercial_discovery disabled",
            )
        try:
            with httpx.Client(timeout=8.0, headers={"User-Agent": USER_AGENT}) as client:
                r = client.get(
                    "https://nominatim.openstreetmap.org/status",
                )
                ok = r.status_code < 500
            return ConnectorHealth(
                status=ConnectorStatus.HEALTHY if ok else ConnectorStatus.DEGRADED,
                checked_at=utcnow(),
                detail="nominatim reachable" if ok else f"nominatim status={r.status_code}",
            )
        except Exception as exc:  # noqa: BLE001
            return ConnectorHealth(
                status=ConnectorStatus.DEGRADED,
                checked_at=utcnow(),
                detail=f"health check error: {exc}",
            )

    def fetch(self, *, query: Optional[str] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        q = (query or kwargs.get("q") or "").strip()
        if not q:
            q = "local business competitors Saudi Arabia"

        amenity = infer_amenity_tag(q)
        city, district = infer_city_district(q)
        # Prefer explicit geography kwargs when callers provide them
        city = str(kwargs.get("city") or city or "").strip() or city
        district = str(kwargs.get("district") or district or "").strip() or district
        sector = str(kwargs.get("sector") or amenity or "").strip()
        missing_keys = kwargs.get("missing_keys") or kwargs.get("coverage_gaps")
        if isinstance(missing_keys, str):
            missing_keys = [missing_keys]

        geography = ", ".join(p for p in (district, city, "Saudi Arabia") if p)

        # --- Evidence-class source strategy (scalable allowlist + seeds) ---
        strategy = None
        try:
            from ai_engine.research.evidence.strategy import resolve_strategy

            strategy = resolve_strategy(
                sector=sector or amenity,
                archetype=str(kwargs.get("archetype") or ""),
                city=city,
                district=district,
                query=q,
                amenity=amenity,
                missing_keys=list(missing_keys) if missing_keys else None,
                evidence_class_ids=kwargs.get("evidence_class_ids"),
            )
            self._apply_strategy_allowlist(strategy.allowlist_domains)
            self._strategy_meta = dict(strategy.meta)
            self._strategy_meta["evidence_class_ids"] = list(strategy.evidence_class_ids)
            self._strategy_meta["adapters"] = dict(strategy.adapters)
        except Exception as exc:  # noqa: BLE001
            self._strategy_meta = {"error": str(exc), "fallback": "bootstrap_allowlist"}
            strategy = None

        attempts: List[Dict[str, Any]] = []
        raw_docs: List[Dict[str, Any]] = []
        self._observations = []

        if strategy is not None:
            attempts.append(
                {
                    "source": "evidence_class_strategy",
                    "ok": True,
                    "evidence_classes": list(strategy.evidence_class_ids),
                    "allowlist_count": len(strategy.allowlist_domains),
                    "seed_count": len(strategy.seed_urls),
                    "query_count": len(strategy.queries),
                }
            )

        # --- 1) Geocode + Nominatim POI discovery ---
        geo = self._geocode(city or "Riyadh", district)
        attempts.append({"source": "nominatim_geocode", **geo.get("meta", {})})
        pois, poi_meta = self._nominatim_pois(
            amenity=amenity, city=city, district=district, query=q, geo=geo
        )
        attempts.append({"source": "nominatim_pois", **poi_meta})
        for poi in pois:
            raw_docs.append(poi)

        # Competition density (best-effort Overpass)
        dens_lat = geo.get("lat")
        dens_lon = geo.get("lon")
        if dens_lat is not None and amenity != "commercial":
            density, dens_meta = self._overpass_density(
                lat=float(dens_lat), lon=float(dens_lon), amenity=amenity
            )
            attempts.append({"source": "overpass_density", **dens_meta})
            if density:
                raw_docs.append(density)
            # Follow OSM-tagged brand websites for menu/ticket evidence (session-merged).
            brand_urls = list(dens_meta.get("websites") or [])
            if brand_urls and strategy is not None:
                brand_docs, brand_meta = self._fetch_brand_websites(
                    urls=brand_urls,
                    strategy=strategy,
                    geography=geography,
                    district=district or None,
                )
                attempts.append({"source": "osm_brand_websites", **brand_meta})
                raw_docs.extend(brand_docs)
        if pois:
            names = [p.get("competitor_name") for p in pois if p.get("competitor_name")]
            raw_docs.append(
                {
                    "evidence_kind": "competition_density",
                    "title": f"Competition density proxy: {len(pois)} named {amenity} POIs from Nominatim",
                    "content": (
                        f"Location economics — competition density: approximately {len(pois)} "
                        f"named OpenStreetMap-sourced '{amenity}' venues found via Nominatim near {geography}. "
                        f"Named sample: {', '.join(str(n) for n in names[:8])}. "
                        f"This is a competition-density / local rivalry proxy for district operating context, "
                        f"not a rent quote or footfall sensor reading."
                    ),
                    "url": "https://nominatim.openstreetmap.org/",
                    "geography": geography,
                    "sector_hint": amenity,
                    "confidence": 0.68,
                    "retrieval_method": "nominatim_count_proxy",
                    "retrieved_at": utcnow().isoformat(),
                    "density_count": len(pois),
                }
            )

        # --- 2) Wikipedia district/city context ---
        wiki_docs, wiki_meta = self._wikipedia_location(city=city, district=district)
        attempts.append({"source": "wikipedia", **wiki_meta})
        raw_docs.extend(wiki_docs)

        # --- 3) Evidence-class seed catalog fetches (works when search is blocked) ---
        if strategy is not None and strategy.seed_urls:
            seed_docs, seed_meta = self._fetch_seed_catalogs(
                strategy=strategy, geography=geography, district=district or None
            )
            attempts.append({"source": "evidence_seed_catalogs", **seed_meta})
            raw_docs.extend(seed_docs)

        # --- 4) Multi-query web discovery (DDG; Bing fallback when DDG challenged) ---
        ddg_queries = (
            list(strategy.queries)
            if strategy and strategy.queries
            else self._build_ddg_queries(
                amenity=amenity, city=city, district=district, query=q
            )
        )
        # Keep legacy competitor query at front
        legacy = self._build_ddg_queries(
            amenity=amenity, city=city, district=district, query=q
        )
        for lq in legacy[:2]:
            if lq not in ddg_queries:
                ddg_queries.insert(0, lq)
        ddg_queries = ddg_queries[: self.max_queries]

        ddg_docs, ddg_meta = self._duckduckgo_multi(
            ddg_queries,
            strategy=strategy,
            geography=geography,
            district=district or None,
        )
        attempts.append({"source": "duckduckgo", **ddg_meta})
        raw_docs.extend(ddg_docs)

        if not ddg_meta.get("ok") or int(ddg_meta.get("results") or 0) == 0:
            # Prefer economics queries (menu/rent/salary) when DDG is challenged —
            # otherwise Bing's first-N cut was competitor-only and never followed menus.
            def _econ_rank(query: str) -> int:
                low = (query or "").lower()
                if any(k in low for k in ("menu", "price", "أسعار", "قائمة", "ticket")):
                    return 0
                if any(k in low for k in ("rent", "إيجار", "sqm", "lease")):
                    return 1
                if any(k in low for k in ("salary", "راتب", "wage", "staff")):
                    return 2
                return 3

            bing_queries = sorted(list(ddg_queries), key=_econ_rank)[:8]
            bing_docs, bing_meta = self._bing_multi(
                bing_queries,
                strategy=strategy,
                geography=geography,
                district=district or None,
            )
            attempts.append({"source": "bing_fallback", **bing_meta})
            raw_docs.extend(bing_docs)

        # Attach normalized observation docs for downstream band derivation
        for obs in self._observations:
            raw_docs.append(obs)

        # Exhaustion document — always emitted for audit / NOT_FOUND justification
        found_competitors = sum(
            1 for d in raw_docs if d.get("evidence_kind") == "competitor_poi"
        )
        found_location = sum(
            1
            for d in raw_docs
            if d.get("evidence_kind") in {"location_context", "competition_density"}
        )
        found_pricing = sum(
            1
            for d in raw_docs
            if d.get("evidence_kind")
            in {
                "pricing_signal",
                "rent_signal",
                "numeric_observation",
                "commercial_rent",
                "menu_pricing",
                "equipment_capex",
                "furniture_pos_opening",
                "salary_labor",
                "fitout_capex",
                "cogs_inputs",
            }
        )
        exhaustion = {
            "evidence_kind": "search_exhaustion",
            "title": "Commercial discovery multi-source search log",
            "content": self._exhaustion_text(
                queries=ddg_queries,
                attempts=attempts,
                found_competitors=found_competitors,
                found_location=found_location,
                found_pricing=found_pricing,
                geography=geography,
                amenity=amenity,
            ),
            "url": None,
            "geography": geography,
            "sector_hint": amenity,
            "attempts": attempts,
            "query": q,
            "strategy_meta": dict(self._strategy_meta or {}),
            "observation_count": len(self._observations),
            "retrieved_at": utcnow().isoformat(),
        }
        raw_docs.append(exhaustion)
        self._last_exhaustion = exhaustion
        return raw_docs

    def _apply_strategy_allowlist(self, domains: List[str]) -> None:
        merged = list(COMMERCIAL_ALLOWED_DOMAINS)
        seen = {d.lower() for d in merged}
        for d in domains or []:
            key = str(d).lower()
            if key and key not in seen:
                seen.add(key)
                merged.append(str(d))
        self._allowlist = merged
        self._reader = SafePageReader(
            allowed_domains=self._allowlist,
            timeout_seconds=self.timeout_seconds,
            user_agent=USER_AGENT,
        )

    def _record_observations(
        self,
        observations: List[Any],
        *,
        geography: str,
    ) -> List[Dict[str, Any]]:
        docs: List[Dict[str, Any]] = []
        for o in observations or []:
            if hasattr(o, "to_evidence_item"):
                item = o.to_evidence_item()
            elif isinstance(o, dict):
                item = dict(o)
            else:
                continue
            item.setdefault("evidence_kind", item.get("evidence_class") or "numeric_observation")
            item.setdefault("title", f"Numeric observation: {item.get('metric')}")
            item.setdefault("geography", geography)
            item.setdefault("retrieval_method", "evidence_adapter")
            item.setdefault("retrieved_at", utcnow().isoformat())
            item.setdefault("confidence", float(item.get("confidence") or 0.55))
            # Ensure content field for SourceDocument normalize
            if not item.get("content"):
                item["content"] = item.get("statement") or item.get("title")
            docs.append(item)
            self._observations.append(item)
        return docs

    def _fetch_brand_websites(
        self,
        *,
        urls: List[str],
        strategy: Any,
        geography: str,
        district: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Fetch OSM-discovered brand/venue websites for menu adapters."""
        from ai_engine.research.evidence.adapters import adapt_page_for_classes
        from ai_engine.research.evidence.strategy import merge_session_hosts

        out: List[Dict[str, Any]] = []
        errors: List[str] = []
        fetched = 0
        # Session-merge discovered brand hosts into follow allowlist.
        try:
            merged = merge_session_hosts(
                self._allowlist,
                list(urls or []),
                evidence_class_ids=list(getattr(strategy, "evidence_class_ids", []) or []),
            )
            if len(merged) > len(self._allowlist):
                self._apply_strategy_allowlist(merged)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"allowlist_merge:{exc}")

        adapters_by_class = dict(getattr(strategy, "adapters", {}) or {})
        evidence_ids = list(getattr(strategy, "evidence_class_ids", []) or [])
        # Prefer menu-oriented classes when present.
        preferred = [e for e in evidence_ids if e in {"menu_pricing", "cogs_inputs", "commercial_rent"}]
        class_ids = preferred or evidence_ids

        for url in list(urls or [])[:6]:
            try:
                if not self._url_allowlisted(url):
                    errors.append(f"not_allowlisted:{url[:80]}")
                    continue
                page = self._reader.read(url)
                fetched += 1
                page_text = (page.text or "")[:6000]
                page_html = (page.html or "")[:200000]
                observations = adapt_page_for_classes(
                    evidence_class_ids=class_ids,
                    adapters_by_class=adapters_by_class,
                    text=page_text,
                    html=page_html,
                    url=page.final_url or url,
                    title=(page.title if hasattr(page, "title") else None) or url,
                    geography=geography,
                    district=district,
                )
                out.extend(
                    self._record_observations(observations, geography=geography)
                )
                out.append(
                    {
                        "evidence_kind": "brand_website_page",
                        "title": f"OSM brand website: {url}",
                        "content": (
                            f"Fetched OSM-tagged brand/venue website for commercial evidence. "
                            f"Excerpt: {page_text[:1200]}"
                        ),
                        "url": page.final_url or url,
                        "geography": geography,
                        "confidence": 0.55,
                        "retrieval_method": "osm_brand_website",
                        "retrieved_at": utcnow().isoformat(),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{url[:60]}:{exc}")
        return out, {
            "ok": fetched > 0,
            "urls_attempted": len(list(urls or [])[:6]),
            "fetched": fetched,
            "observation_docs": len(out),
            "errors": errors[:8],
        }

    def _fetch_seed_catalogs(
        self,
        *,
        strategy: Any,
        geography: str,
        district: Optional[str],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        from ai_engine.research.evidence.adapters import adapt_page_for_classes

        seed_to_classes: Dict[str, List[str]] = dict(
            (strategy.meta or {}).get("seed_owners") or {}
        )

        out: List[Dict[str, Any]] = []
        errors: List[str] = []
        fetched = 0
        obs_count = 0
        for url in list(strategy.seed_urls or [])[:12]:
            try:
                if not self._url_allowlisted(url):
                    errors.append(f"not_allowlisted:{url[:80]}")
                    continue
                page = self._reader.read(url)
                fetched += 1
                text = (page.text or "")[:8000]
                html = (page.html or "")[:200000]
                class_ids = list(seed_to_classes.get(url) or strategy.evidence_class_ids)
                adapters = {
                    eid: strategy.adapters[eid]
                    for eid in class_ids
                    if eid in (strategy.adapters or {})
                }
                observations = adapt_page_for_classes(
                    evidence_class_ids=class_ids,
                    adapters_by_class=adapters,
                    text=text,
                    html=html,
                    url=page.final_url or url,
                    title=page.title or url,
                    geography=geography,
                    district=district,
                )
                obs_docs = self._record_observations(observations, geography=geography)
                obs_count += len(obs_docs)
                out.append(
                    {
                        "evidence_kind": "seed_catalog_page",
                        "title": f"Seed catalog: {page.title or url}",
                        "content": (
                            f"Evidence-class seed catalog fetch for {url}. "
                            f"Classes={class_ids}. "
                            f"Extracted {len(observations)} numeric observation(s). "
                            f"Excerpt: {text[:1200]}"
                        ),
                        "url": page.final_url or url,
                        "geography": geography,
                        "confidence": 0.55,
                        "retrieval_method": "evidence_seed_catalog",
                        "retrieved_at": utcnow().isoformat(),
                        "observation_count": len(observations),
                    }
                )
                out.extend(obs_docs)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{url[:80]}: {exc}")
        return out, {
            "ok": fetched > 0,
            "pages_fetched": fetched,
            "observations": obs_count,
            "errors": errors[:8],
            "seeds_attempted": len(list(strategy.seed_urls or [])[:12]),
        }

    def normalize(self, raw: Dict[str, Any]) -> SourceDocument:
        retrieved = utcnow()
        kind = str(raw.get("evidence_kind") or "commercial_web")
        title = str(raw.get("title") or kind)
        content = str(raw.get("content") or "").strip()
        if not content:
            content = title
        url = raw.get("url")
        canonical = None
        if url:
            try:
                canonical = canonicalize_url(str(url))
            except UrlSecurityError:
                canonical = str(url)

        source_id = (
            f"commercial:{kind}:"
            + hashlib.sha256((canonical or title or content)[:400].encode()).hexdigest()[:16]
        )
        authority = AuthorityType.COMMERCIAL_SOURCE
        source_type = SourceType.OPEN_DATA
        eligibility = VerificationEligibility.NOT_ELIGIBLE
        if kind in {"competitor_poi", "competition_density"}:
            authority = AuthorityType.REPUTABLE_INSTITUTION
            source_type = SourceType.OPEN_DATA
            eligibility = VerificationEligibility.ELIGIBLE
        elif kind == "location_context":
            authority = AuthorityType.REPUTABLE_INSTITUTION
            source_type = SourceType.MARKET_REPORT
            eligibility = VerificationEligibility.ELIGIBLE
        elif kind == "search_exhaustion":
            authority = AuthorityType.UNVERIFIED
            source_type = SourceType.OTHER
            eligibility = VerificationEligibility.NOT_ELIGIBLE

        return SourceDocument(
            source_id=source_id,
            source_name="Commercial Discovery",
            source_type=source_type,
            authority_type=authority,
            url=str(url) if url else None,
            canonical_url=canonical,
            title=title[:240],
            content=content[:12000],
            published_at=None,
            retrieved_at=retrieved,
            country="SA",
            geography=str(raw.get("geography") or "") or None,
            sector=str(raw.get("sector_hint") or "") or None,
            language="en",
            document_type=kind,
            content_type="text/plain",
            confidence=float(raw.get("confidence") or 0.55),
            content_hash=compute_content_hash(content[:12000]),
            provenance=Provenance(
                connector_id=CONNECTOR_ID,
                original_url=str(url) if url else None,
                retrieval_method=str(raw.get("retrieval_method") or "multi_source_http"),
                retrieved_at=retrieved,
                registry_key=REGISTRY_KEY,
            ),
            metadata={
                "evidence_kind": kind,
                "competitor_name": raw.get("competitor_name"),
                "relevance": raw.get("relevance"),
                "attempts": raw.get("attempts"),
                "query": raw.get("query"),
                "metric": raw.get("metric"),
                "value": raw.get("value"),
                "unit": raw.get("unit"),
                "adapter_id": raw.get("adapter_id"),
                "observation_count": raw.get("observation_count"),
                "strategy_meta": raw.get("strategy_meta"),
            },
            verification_eligibility=eligibility,
        )

    # --- internals ---------------------------------------------------------

    def _http_get_json(self, url: str, *, params: Optional[dict] = None) -> Any:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": USER_AGENT}) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    def _geocode(self, city: str, district: str) -> Dict[str, Any]:
        q = " ".join(p for p in (district, city, "Saudi Arabia") if p)
        try:
            data = self._http_get_json(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": q,
                    "format": "json",
                    "limit": 3,
                    "countrycodes": "sa",
                },
            )
            if not data:
                data = self._http_get_json(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "city": city or "Riyadh",
                        "country": "Saudi Arabia",
                        "format": "json",
                        "limit": 1,
                    },
                )
            # Prefer hits whose display_name includes the city (avoid wrong-province matches)
            city_l = (city or "riyadh").lower()
            chosen = None
            for hit in data or []:
                display = str(hit.get("display_name") or "").lower()
                if city_l in display or "الرياض" in display:
                    chosen = hit
                    break
            if chosen is None and data:
                # Fallback: city-only geocode
                data2 = self._http_get_json(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "city": city or "Riyadh",
                        "country": "Saudi Arabia",
                        "format": "json",
                        "limit": 1,
                    },
                )
                chosen = (data2 or [None])[0] or data[0]
            if chosen:
                return {
                    "lat": float(chosen["lat"]),
                    "lon": float(chosen["lon"]),
                    "display_name": chosen.get("display_name"),
                    "meta": {"ok": True, "query": q, "hits": len(data or [])},
                }
            return {"meta": {"ok": False, "query": q, "hits": 0, "reason": "no_geocode_hit"}}
        except Exception as exc:  # noqa: BLE001
            return {"meta": {"ok": False, "query": q, "error": str(exc)}}

    def _nominatim_pois(
        self,
        *,
        amenity: str,
        city: str,
        district: str,
        query: str,
        geo: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        searches: List[str] = []
        place = " ".join(p for p in (district, city, "Saudi Arabia") if p) or "Saudi Arabia"
        if amenity and amenity != "commercial":
            searches.append(f"{amenity} near {place}")
            searches.append(f"{amenity} {place}")
        # Also use sector keywords from original query (first meaningful tokens)
        tokens = re.findall(r"[A-Za-z\u0600-\u06FF]{3,}", query or "")
        sector_bits = " ".join(tokens[:4])
        if sector_bits:
            searches.append(f"{sector_bits} {place}")
        searches = searches[:4]

        out: List[Dict[str, Any]] = []
        seen: set[str] = set()
        errors: List[str] = []
        for sq in searches:
            try:
                data = self._http_get_json(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": sq,
                        "format": "json",
                        "limit": self.max_pois,
                        "countrycodes": "sa",
                        "addressdetails": 1,
                    },
                )
                time.sleep(0.35)  # Nominatim usage policy courtesy
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{sq}: {exc}")
                continue
            for hit in data or []:
                name = str(hit.get("name") or "").strip()
                display = str(hit.get("display_name") or "").strip()
                if not name and display:
                    name = display.split(",")[0].strip()
                if not name or name.lower() in seen:
                    continue
                # Skip pure street/admin hits without amenity class when looking for venues
                cls = str(hit.get("class") or "")
                typ = str(hit.get("type") or "")
                if cls in {"highway", "place", "boundary"} and amenity != "commercial":
                    continue
                # Skip street-like names (Arabic/English thoroughfares)
                streetish = (
                    name.startswith("طريق")
                    or name.startswith("شارع")
                    or name.lower().startswith("street")
                    or name.lower().startswith("road")
                    or "highway" in typ
                )
                if streetish:
                    continue
                if re.fullmatch(r"(رقم|no\.?|#)\s*\d+", name, re.I):
                    continue
                # Prefer POIs in the requested city when city is known
                if city:
                    city_l = city.lower()
                    display_l = display.lower()
                    city_ar = {"riyadh": "الرياض", "jeddah": "جدة", "dammam": "الدمام"}.get(city_l)
                    if city_l not in display_l and not (city_ar and city_ar in display):
                        # Soft filter: skip clearly other-city hits
                        other_cities = ("الدمام", "dammam", "جدة", "jeddah", "الخبر", "khobar", "الظهران")
                        if any(o in display_l for o in other_cities) and city_l == "riyadh":
                            continue
                        if any(o in display_l for o in ("الرياض", "riyadh")) and city_l != "riyadh":
                            continue
                seen.add(name.lower())
                osm_url = _osm_url(str(hit.get("osm_type") or ""), hit.get("osm_id"))
                relevance = (
                    f"Named {cls}/{typ or 'venue'} listed in OpenStreetMap near {place}; "
                    f"relevant as a local competitor / operating peer for '{amenity}' discovery query."
                )
                content = (
                    f"Competitor / local venue evidence: {name}. "
                    f"Location: {display}. "
                    f"OSM class={cls} type={typ}. "
                    f"Relevance: {relevance} "
                    f"Geography: {place}. Retrieved via Nominatim search '{sq}'."
                )
                out.append(
                    {
                        "evidence_kind": "competitor_poi",
                        "title": f"Competitor POI: {name}",
                        "content": content,
                        "url": osm_url,
                        "competitor_name": name,
                        "relevance": relevance,
                        "geography": place,
                        "sector_hint": amenity,
                        "confidence": 0.72,
                        "retrieval_method": "nominatim_search",
                        "query": sq,
                        "retrieved_at": utcnow().isoformat(),
                    }
                )
                if len(out) >= self.max_pois:
                    break
            if len(out) >= self.max_pois:
                break

        return out, {
            "ok": bool(out),
            "queries": searches,
            "hits": len(out),
            "errors": errors,
            "geocode_ok": bool(geo.get("lat") is not None),
        }

    def _overpass_density(
        self, *, lat: float, lon: float, amenity: str, radius_m: int = 1500
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        # Use out body + count client-side; Overpass `out count` is flaky under load.
        ql = (
            f'[out:json][timeout:20];'
            f'(node["amenity"="{amenity}"](around:{radius_m},{lat},{lon});'
            f'way["amenity"="{amenity}"](around:{radius_m},{lat},{lon}););'
            f"out tags center {self.max_pois};"
        )
        try:
            with httpx.Client(timeout=22.0, headers={"User-Agent": USER_AGENT}) as client:
                r = client.post(
                    "https://overpass-api.de/api/interpreter",
                    data={"data": ql},
                )
                if r.status_code >= 400:
                    return None, {"ok": False, "status": r.status_code, "reason": "http_error"}
                payload = r.json()
            elements = payload.get("elements") or []
            names: list[str] = []
            websites: list[str] = []
            seats_obs: list[dict[str, Any]] = []
            for el in elements:
                tags = el.get("tags") or {}
                n = tags.get("name") or tags.get("name:en")
                if n:
                    names.append(str(n))
                web = tags.get("website") or tags.get("contact:website") or tags.get("url")
                if web:
                    w = str(web).strip()
                    if w and not w.startswith("http"):
                        w = "https://" + w
                    if w.startswith("http") and w not in websites:
                        websites.append(w)
                for seat_key in ("seats", "capacity"):
                    if seat_key in tags:
                        try:
                            seats_obs.append(
                                {
                                    "name": n,
                                    "metric": seat_key,
                                    "value": float(str(tags[seat_key]).split()[0]),
                                }
                            )
                        except (TypeError, ValueError):
                            pass
            count = len(elements)
            content = (
                f"Location economics — competition density: approximately {count} "
                f"OpenStreetMap '{amenity}' amenities within {radius_m}m of "
                f"lat={lat:.4f}, lon={lon:.4f}. "
                f"Named sample: {', '.join(names[:8]) or 'unnamed'}. "
                f"Brand websites tagged: {', '.join(websites[:6]) or 'none'}. "
                f"This is a footfall/competition-density proxy for district operating context, "
                f"not a rent quote."
            )
            return (
                {
                    "evidence_kind": "competition_density",
                    "title": f"Competition density ({amenity}) ~{count} within {radius_m}m",
                    "content": content,
                    "url": "https://overpass-api.de/api/interpreter",
                    "geography": f"{lat:.4f},{lon:.4f}",
                    "sector_hint": amenity,
                    "confidence": 0.65,
                    "retrieval_method": "overpass_around",
                    "retrieved_at": utcnow().isoformat(),
                    "density_count": count,
                    "brand_websites": websites[:12],
                    "seat_tags": seats_obs[:12],
                },
                {
                    "ok": True,
                    "count": count,
                    "named": len(names),
                    "websites": websites[:12],
                    "seat_tags": seats_obs[:12],
                },
            )
        except Exception as exc:  # noqa: BLE001
            return None, {"ok": False, "error": str(exc)}

    def _wikipedia_location(
        self, *, city: str, district: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        titles: List[str] = []
        if district:
            d = district.replace("_", " ").strip()
            if city:
                titles.append(f"{d} ({city})")
                titles.append(f"Al {d} ({city})" if not d.lower().startswith("al") else f"{d} ({city})")
            titles.append(d)
        if city:
            titles.append(city)
            titles.append(f"{city}, Saudi Arabia")
        # Deduplicate preserving order
        seen: set[str] = set()
        uniq = []
        for t in titles:
            k = t.lower()
            if k not in seen:
                seen.add(k)
                uniq.append(t)

        out: List[Dict[str, Any]] = []
        tried: List[str] = []
        for title in uniq[:5]:
            tried.append(title)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}"
            try:
                data = self._http_get_json(url)
            except Exception:
                continue
            if not isinstance(data, dict) or data.get("type") == "https://mediawiki.org/api/rest_v1/errors/not_found":
                continue
            extract = str(data.get("extract") or "").strip()
            page_url = (data.get("content_urls") or {}).get("desktop", {}).get("page") or data.get(
                "content_urls", {}
            ).get("desktop", {}).get("page")
            if not page_url:
                page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
            if not extract:
                continue
            content = (
                f"Location economics / district operating context for {title}: {extract} "
                f"Use as qualitative customer-profile and district character evidence; "
                f"not a verified rent or footfall statistic."
            )
            out.append(
                {
                    "evidence_kind": "location_context",
                    "title": f"Location context: {data.get('title') or title}",
                    "content": content,
                    "url": page_url,
                    "geography": title,
                    "confidence": 0.6,
                    "retrieval_method": "wikipedia_rest_summary",
                    "retrieved_at": utcnow().isoformat(),
                }
            )
            if len(out) >= 2:
                break
        return out, {"ok": bool(out), "tried_titles": tried, "hits": len(out)}

    def _build_ddg_queries(
        self, *, amenity: str, city: str, district: str, query: str
    ) -> List[str]:
        place = " ".join(p for p in (district, city) if p) or "Saudi Arabia"
        label = amenity if amenity != "commercial" else "local business"
        qs = [
            f"{label} competitors {place} Saudi Arabia",
            f"best {label} {place} Riyadh" if "riyadh" not in place.lower() else f"best {label} {place}",
            f"commercial rent SAR {place} retail shop",
            f"{place} commercial rent per sqm Saudi Arabia",
            f"{label} average price SAR {place}",
            f"{label} menu prices {place} SAR",
            f"F&B barista salary SAR Saudi Arabia" if amenity in {"cafe", "restaurant"} else f"{label} staff salary SAR Saudi Arabia",
            f"{label} fit out cost SAR Saudi Arabia small shop",
        ]
        # Include original research query fragment
        if query and query not in qs:
            qs.insert(0, f"{query} competitors pricing rent")
        # Unique, capped
        out: List[str] = []
        for q in qs:
            if q not in out:
                out.append(q)
        return out[: self.max_queries]

    def _duckduckgo_multi(
        self,
        queries: Sequence[str],
        *,
        strategy: Any = None,
        geography: str = "Saudi Arabia",
        district: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        per_query: List[Dict[str, Any]] = []
        follow_budget = self.max_ddg_follow
        adapters_by_class = dict(getattr(strategy, "adapters", {}) or {})
        evidence_ids = list(getattr(strategy, "evidence_class_ids", []) or [])
        for q in queries:
            results, meta = self._ddg_search(q)
            per_query.append({"query": q, **meta})
            # Session-merge discovered hosts when strategy allows
            if strategy is not None and getattr(strategy, "allow_discovered_hosts", False):
                try:
                    from ai_engine.research.evidence.strategy import merge_session_hosts

                    urls = [r["url"] for r in results if r.get("url")]
                    merged = merge_session_hosts(
                        self._allowlist,
                        urls,
                        evidence_class_ids=evidence_ids,
                    )
                    if len(merged) > len(self._allowlist):
                        self._apply_strategy_allowlist(merged)
                except Exception:  # noqa: BLE001
                    pass
            for res in results:
                title = res["title"]
                snippet = res["snippet"]
                href = res["url"]
                kind = "commercial_web"
                low = f"{title} {snippet}".lower()
                if any(k in low for k in ("rent", "إيجار", "lease", "sqm", "m²", "per month")):
                    kind = "rent_signal"
                elif any(k in low for k in ("price", "sar", "menu", "ticket", "cost")):
                    kind = "pricing_signal"
                elif any(k in low for k in ("competitor", "cafe", "restaurant", "coffee", "shop")):
                    kind = "competitor_web_mention"

                rent_hits = [m.group(0) for m in _RENT_RE.finditer(snippet)]
                price_hits = [m.group(0) for m in _PRICE_RE.finditer(snippet)]
                content = (
                    f"Web discovery result for query '{q}'. Title: {title}. "
                    f"Snippet: {snippet}. "
                )
                if rent_hits:
                    content += f"Rent-related figures mentioned in snippet: {', '.join(rent_hits[:3])}. "
                if price_hits:
                    content += f"Price figures mentioned in snippet: {', '.join(price_hits[:3])}. "
                content += (
                    "Treat as unverified commercial web signal pending primary confirmation. "
                    "Includes competitor / location / pricing keywords for evidence theme coverage."
                )
                doc = {
                    "evidence_kind": kind,
                    "title": title[:200],
                    "content": content,
                    "url": href if self._url_allowlisted(href) else None,
                    "geography": geography,
                    "confidence": 0.4,
                    "retrieval_method": "duckduckgo_html",
                    "query": q,
                    "retrieved_at": utcnow().isoformat(),
                    "snippet_rent_mentions": rent_hits[:3],
                    "snippet_price_mentions": price_hits[:3],
                }
                if follow_budget > 0 and href and self._url_allowlisted(href):
                    try:
                        page = self._reader.read(href)
                        follow_budget -= 1
                        page_text = (page.text or "")[:4000]
                        page_html = (page.html or "")[:120000]
                        doc["content"] = (
                            doc["content"]
                            + f" Page excerpt ({page.final_url}): {page_text[:1500]}"
                        )
                        doc["url"] = page.final_url
                        doc["confidence"] = 0.5
                        doc["snippet_rent_mentions"] = [
                            m.group(0) for m in _RENT_RE.finditer(page_text)
                        ][:5]
                        doc["snippet_price_mentions"] = [
                            m.group(0) for m in _PRICE_RE.finditer(page_text)
                        ][:5]
                        if evidence_ids and adapters_by_class:
                            from ai_engine.research.evidence.adapters import (
                                adapt_page_for_classes,
                            )

                            observations = adapt_page_for_classes(
                                evidence_class_ids=evidence_ids,
                                adapters_by_class=adapters_by_class,
                                text=page_text,
                                html=page_html,
                                url=page.final_url or href,
                                title=title,
                                geography=geography,
                                district=district,
                            )
                            out.extend(
                                self._record_observations(
                                    observations, geography=geography
                                )
                            )
                    except (PageFetchError, UrlSecurityError, Exception):  # noqa: BLE001
                        pass
                elif snippet and evidence_ids and adapters_by_class:
                    # Snippet-only adaptation (weaker confidence)
                    try:
                        from ai_engine.research.evidence.adapters import (
                            adapt_page_for_classes,
                        )

                        observations = adapt_page_for_classes(
                            evidence_class_ids=evidence_ids,
                            adapters_by_class=adapters_by_class,
                            text=f"{title}\n{snippet}",
                            url=href if self._url_allowlisted(href) else None,
                            title=title,
                            geography=geography,
                            district=district,
                        )
                        for o in observations:
                            if hasattr(o, "confidence"):
                                o.confidence = min(float(o.confidence), 0.42)
                        out.extend(
                            self._record_observations(observations, geography=geography)
                        )
                    except Exception:  # noqa: BLE001
                        pass
                out.append(doc)
        return out, {
            "ok": bool(out),
            "queries_run": len(queries),
            "results": len(out),
            "per_query": per_query,
            "pages_followed": self.max_ddg_follow - follow_budget,
        }

    def _bing_multi(
        self,
        queries: Sequence[str],
        *,
        strategy: Any = None,
        geography: str = "Saudi Arabia",
        district: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Bing HTML fallback when DuckDuckGo is challenged — same connector, not a new subsystem."""
        out: List[Dict[str, Any]] = []
        per_query: List[Dict[str, Any]] = []
        follow_budget = max(4, min(6, self.max_ddg_follow + 2))
        adapters_by_class = dict(getattr(strategy, "adapters", {}) or {})
        evidence_ids = list(getattr(strategy, "evidence_class_ids", []) or [])
        pages_followed = 0
        for q in queries:
            results, meta = self._bing_search(q)
            per_query.append({"query": q, **meta})
            # Session-merge discovered hosts before follow (enables brand menus).
            if strategy is not None and getattr(strategy, "allow_discovered_hosts", False):
                try:
                    from ai_engine.research.evidence.strategy import merge_session_hosts

                    urls = [r["url"] for r in results if r.get("url")]
                    merged = merge_session_hosts(
                        self._allowlist,
                        urls,
                        evidence_class_ids=evidence_ids,
                    )
                    if len(merged) > len(self._allowlist):
                        self._apply_strategy_allowlist(merged)
                except Exception:  # noqa: BLE001
                    pass

            # Prefer following menu/pricing URLs within the budget.
            def _follow_rank(res: Dict[str, str]) -> int:
                low = f"{res.get('title','')} {res.get('snippet','')} {res.get('url','')}".lower()
                if any(k in low for k in ("menu", "price", "قائمة", "أسعار", "/menu")):
                    return 0
                if any(k in low for k in ("rent", "إيجار", "lease")):
                    return 1
                if any(k in low for k in ("salary", "راتب", "job")):
                    return 2
                return 3

            ordered = sorted(list(results), key=_follow_rank)
            for res in ordered:
                title = res["title"]
                snippet = res["snippet"]
                href = res["url"]
                content = (
                    f"Bing discovery result for query '{q}'. Title: {title}. "
                    f"Snippet: {snippet}. Unverified commercial web signal."
                )
                doc = {
                    "evidence_kind": "commercial_web",
                    "title": title[:200],
                    "content": content,
                    "url": href if self._url_allowlisted(href) else None,
                    "geography": geography,
                    "confidence": 0.38,
                    "retrieval_method": "bing_html",
                    "query": q,
                    "retrieved_at": utcnow().isoformat(),
                }
                if follow_budget > 0 and href and self._url_allowlisted(href):
                    try:
                        page = self._reader.read(href)
                        follow_budget -= 1
                        pages_followed += 1
                        page_text = (page.text or "")[:6000]
                        page_html = (page.html or "")[:200000]
                        doc["content"] += f" Page excerpt: {page_text[:1200]}"
                        doc["url"] = page.final_url
                        doc["confidence"] = 0.5
                        if evidence_ids and adapters_by_class:
                            from ai_engine.research.evidence.adapters import (
                                adapt_page_for_classes,
                            )

                            observations = adapt_page_for_classes(
                                evidence_class_ids=evidence_ids,
                                adapters_by_class=adapters_by_class,
                                text=page_text,
                                html=page_html,
                                url=page.final_url or href,
                                title=title,
                                geography=geography,
                                district=district,
                            )
                            out.extend(
                                self._record_observations(
                                    observations, geography=geography
                                )
                            )
                    except Exception:  # noqa: BLE001
                        pass
                out.append(doc)
        return out, {
            "ok": bool(out),
            "queries_run": len(queries),
            "results": len(out),
            "per_query": per_query,
            "pages_followed": pages_followed,
        }

    def _bing_search(self, query: str) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                headers={"User-Agent": SEARCH_USER_AGENT, "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"},
                follow_redirects=True,
            ) as client:
                r = client.get(url)
                r.raise_for_status()
                html = r.text
        except Exception as exc:  # noqa: BLE001
            return [], {"ok": False, "error": str(exc), "hits": 0}

        results: List[Dict[str, str]] = []
        for m in re.finditer(
            r'class="b_algo".*?<h2[^>]*>\s*<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>'
            r'.*?(?:<p[^>]*>(?P<snippet>.*?)</p>)?',
            html,
            re.I | re.S,
        ):
            href = _strip_html(m.group("href"))
            title = _strip_html(m.group("title"))
            snippet = _strip_html(m.group("snippet") or "")
            if not title or "bing.com/ck" in href and "http" not in href:
                # Keep bing redirect URLs — reader may not follow off-allowlist
                pass
            if not title:
                continue
            results.append({"title": title, "url": _unwrap_bing_url(href), "snippet": snippet})
            if len(results) >= 5:
                break
        return results, {"ok": True, "hits": len(results)}

    def _ddg_search(self, query: str) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                headers={"User-Agent": SEARCH_USER_AGENT, "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"},
                follow_redirects=True,
            ) as client:
                r = client.get(url)
                if r.status_code == 202 or "challenge" in (r.text or "")[:800].lower():
                    return [], {
                        "ok": False,
                        "error": "ddg_bot_challenge",
                        "status": r.status_code,
                        "hits": 0,
                    }
                r.raise_for_status()
                html = r.text
        except Exception as exc:  # noqa: BLE001
            return [], {"ok": False, "error": str(exc), "hits": 0}

        results: List[Dict[str, str]] = []
        for m in _DDG_RESULT_RE.finditer(html):
            href = _strip_html(m.group("href"))
            if "uddg=" in href:
                from urllib.parse import parse_qs, unquote, urlparse as _up

                qs = parse_qs(_up(href).query)
                if qs.get("uddg"):
                    href = unquote(qs["uddg"][0])
            title = _strip_html(m.group("title"))
            snippet = _strip_html(m.group("snippet"))
            if not title:
                continue
            results.append({"title": title, "url": href, "snippet": snippet})
            if len(results) >= 5:
                break
        if not results:
            for m in re.finditer(
                r'result__a[^>]*href="([^"]+)"[^>]*>([^<]+)', html, re.I
            ):
                results.append(
                    {
                        "title": _strip_html(m.group(2)),
                        "url": m.group(1),
                        "snippet": "",
                    }
                )
                if len(results) >= 5:
                    break
        return results, {"ok": True, "hits": len(results)}

    def _url_allowlisted(self, url: str) -> bool:
        try:
            host = (urlparse(url).hostname or "").lower()
        except Exception:
            return False
        domains = self._allowlist or list(COMMERCIAL_ALLOWED_DOMAINS)
        return any(host == d or host.endswith("." + d) for d in domains)

    def _exhaustion_text(
        self,
        *,
        queries: Sequence[str],
        attempts: Sequence[Dict[str, Any]],
        found_competitors: int,
        found_location: int,
        found_pricing: int,
        geography: str,
        amenity: str,
    ) -> str:
        lines = [
            "Commercial discovery search exhaustion record.",
            f"Geography: {geography}. Amenity/sector tag: {amenity}.",
            f"Competitor POIs found: {found_competitors}.",
            f"Location economics docs found: {found_location}.",
            f"Pricing/rent web signals found: {found_pricing}.",
            "Queries executed:",
        ]
        for q in queries:
            lines.append(f"- {q}")
        lines.append("Source attempt outcomes:")
        for a in attempts:
            lines.append(f"- {json.dumps(a, ensure_ascii=False)[:500]}")
        if found_competitors == 0 and found_location == 0 and found_pricing == 0:
            lines.append(
                "NOT_FOUND justification: all attempted sources returned no usable "
                "commercial evidence after multi-source search."
            )
        else:
            lines.append(
                "Partial/complete: at least one source class returned evidence; "
                "remaining UNKNOWN assumptions must stay unresolved rather than fabricated."
            )
        return "\n".join(lines)
