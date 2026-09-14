"""Source-specific numeric evidence adapters (generic, not coffee-hardcoded)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from ai_engine.research.evidence.domain_classes import DOMAIN_CLASSES
from ai_engine.research.evidence.evidence_classes import EVIDENCE_CLASSES
from ai_engine.research.evidence.observations import NumericObservation

_SAR_NUM = re.compile(
    r"(?:SAR|SR|ر\.?\s*س\.?|ريال)\s*([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
    r"|"
    # Suffix form: do not steal a calendar year from patterns like "2024 SAR4,000.00".
    r"([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(?:SAR|SR|ر\.?\s*س\.?|ريال)(?!\s*[0-9])",
    re.I,
)
_AREA_M2 = re.compile(
    r"([0-9]{2,4}(?:\.[0-9]+)?)\s*(?:m(?:2|²)|sqm|sq\.?\s*m|متر|م(?:2|٢))",
    re.I,
)
_AMAZON_WHOLE = re.compile(r'a-price-whole[^>]*>([0-9,]+)', re.I)
_IKEA_PRICE = re.compile(r'data-price="([0-9]+(?:\.[0-9]+)?)"', re.I)
_PCT = re.compile(
    r"(?:food\s*cost|cogs|cost of goods)[^\n%]{0,40}?([0-9]{1,2}(?:\.[0-9]+)?)\s*%|"
    r"([0-9]{1,2}(?:\.[0-9]+)?)\s*%[^\n]{0,30}?(?:food\s*cost|cogs)",
    re.I,
)
_SALARY_ROLE = re.compile(
    r"(barista|waiter|chef|manager|cashier|server|cook|موظف|باريستا|مدير|نادل)",
    re.I,
)
_MIN_WAGE_HINT = re.compile(
    r"minimum\s+wage|حد\s*أدنى|الحد\s*الأدنى\s*للأجور|private\s+sector\s*\(saudi",
    re.I,
)
_JSON_PRICE = re.compile(r'"price"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?', re.I)
_BDI_PRICE = re.compile(
    r"(?:currencySymbol[^<]*</[^>]+>|ر\.?\s*س\.?)\s*([0-9]+(?:\.[0-9]+)?)\s*</bdi>",
    re.I,
)
_BDI_PRICE_ALT = re.compile(r"</span>([0-9]+(?:\.[0-9]+)?)</bdi>", re.I)
_SAR_CURRENCY_HINT = re.compile(
    r'(?:["\']currency["\']\s*:\s*["\']SAR["\']|\bSAR\b|ر(?:\.\s*)?س|ريال)',
    re.I,
)


def _f(raw: str) -> Optional[float]:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _host(url: str | None) -> str:
    try:
        return (urlparse(url or "").hostname or "").lower()
    except Exception:
        return ""


def _host_matches_domain_class(host: str, domain_class_id: str) -> bool:
    dc = DOMAIN_CLASSES.get(domain_class_id)
    if not dc or not host:
        return False
    return any(host == d or host.endswith("." + d) for d in dc.domains)


def host_allowed_for_evidence_class(url: str | None, evidence_class_id: str) -> bool:
    """Gate adapters so equipment catalogs cannot emit salary/menu false positives."""
    spec = EVIDENCE_CLASSES.get(evidence_class_id)
    if not spec:
        return False
    host = _host(url)
    if not host:
        return evidence_class_id in {
            "cogs_inputs",
            "fitout_capex",
            "commercial_rent",
            "salary_labor",
        }
    if _host_matches_domain_class(host, "search_index") or _host_matches_domain_class(
        host, "open_geo_encyclopedia"
    ):
        return evidence_class_id in {
            "commercial_rent",
            "menu_pricing",
            "salary_labor",
            "fitout_capex",
            "cogs_inputs",
        }
    for dc_id in spec.domain_classes:
        if dc_id in {"search_index", "market_report", "official_saudi"}:
            continue
        if _host_matches_domain_class(host, dc_id):
            return True
    if evidence_class_id in {"cogs_inputs", "salary_labor", "commercial_rent", "fitout_capex"}:
        if _host_matches_domain_class(host, "official_saudi") or _host_matches_domain_class(
            host, "market_report"
        ):
            return True
    # Discovered brand/venue hosts (OSM website tags, search follow): allow when the
    # evidence class opts into local_brand_website, but never cross-fire vendor catalogs.
    if "local_brand_website" in spec.domain_classes:
        blocked = (
            "equipment_vendor",
            "fitout_vendor",
            "job_salary",
            "real_estate_listing",
        )
        if not any(_host_matches_domain_class(host, b) for b in blocked):
            return True
    return False


def extract_sar_amounts(text: str) -> list[float]:
    out: list[float] = []
    for m in _SAR_NUM.finditer(text or ""):
        raw = m.group(1) or m.group(2)
        val = _f(raw or "")
        if val is not None:
            out.append(val)
    return out


_WASALT_RETAIL_SUBTYPES = {
    "معرض",
    "محل",
    "showroom",
    "shop",
    "retail",
    "store",
}
_WASALT_EXCLUDE_SUBTYPES = {
    "مستودع",
    "warehouse",
    "أرض",
    "land",
    "شقة",
    "apartment",
    "فيلا",
    "villa",
}


def _parse_opening_hours_daily(value: str) -> float | None:
    """Best-effort OSM opening_hours → average open hours/day (methodology parse, not invention)."""
    raw = (value or "").strip()
    if not raw or raw.lower() in {"24/7", "open"}:
        return 24.0 if raw.lower() in {"24/7"} else None
    # Match HH:MM-HH:MM ranges (take first range as representative day length).
    ranges = re.findall(
        r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})",
        raw,
    )
    if not ranges:
        return None
    hours: list[float] = []
    for h1, m1, h2, m2 in ranges:
        start = int(h1) + int(m1) / 60.0
        end = int(h2) + int(m2) / 60.0
        if end <= start:
            end += 24.0
        dur = end - start
        if 1.0 <= dur <= 24.0:
            hours.append(dur)
    if not hours:
        return None
    return round(sum(hours) / len(hours), 2)


def adapt_osm_capacity_signals(
    *,
    seat_tags: list[dict[str, Any]] | None = None,
    opening_hours_tags: list[dict[str, Any]] | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
    source_url: str | None = "https://overpass-api.de/api/interpreter",
) -> list[NumericObservation]:
    """Promote OSM seat/capacity + opening_hours tags into numeric observations."""
    now = datetime.now(timezone.utc).isoformat()
    obs: list[NumericObservation] = []
    for row in seat_tags or []:
        try:
            val = float(row.get("value"))
        except (TypeError, ValueError):
            continue
        if not (4 <= val <= 400):
            continue
        obs.append(
            NumericObservation(
                evidence_class="capacity_signals",
                metric="seats_capacity",
                value=val,
                unit="seats",
                geography=geography,
                district=district,
                role_or_item=str(row.get("name") or "osm_amenity"),
                source_url=source_url,
                source_title=f"OSM {row.get('metric') or 'seats'} tag",
                retrieved_at=now,
                adapter_id="osm_capacity",
                raw_excerpt=str(row)[:200],
                confidence=0.55,
                metadata={"osm_metric": row.get("metric"), "source": "overpass"},
            )
        )
    for row in opening_hours_tags or []:
        daily = _parse_opening_hours_daily(str(row.get("value") or ""))
        if daily is None or not (4 <= daily <= 24):
            continue
        obs.append(
            NumericObservation(
                evidence_class="capacity_signals",
                metric="operating_hours_day",
                value=float(daily),
                unit="hours",
                geography=geography,
                district=district,
                role_or_item=str(row.get("name") or "osm_amenity"),
                source_url=source_url,
                source_title="OSM opening_hours tag",
                retrieved_at=now,
                adapter_id="osm_opening_hours",
                raw_excerpt=str(row.get("value") or "")[:200],
                confidence=0.6,
                metadata={"source": "overpass", "raw_opening_hours": row.get("value")},
            )
        )
    return obs


def _adapt_wasalt_next_data(
    *,
    html: str,
    url: str | None,
    title: str | None,
    geography: str,
    district: str | None,
) -> list[NumericObservation]:
    """Parse Wasalt category SSR __NEXT_DATA__ commercial rent listings."""
    host = _host(url)
    if host and "wasalt.sa" not in host and "wasalt.com" not in host:
        # Still allow when html clearly contains Wasalt searchResult payload.
        if '"searchResult"' not in (html or "") or "wasalt" not in (html or "").lower():
            return []
    m = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html or "",
        re.I | re.S,
    )
    if not m:
        return []
    try:
        payload = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    props = (
        ((payload.get("props") or {}).get("pageProps") or {}).get("searchResult") or {}
    )
    listings = props.get("properties") or []
    if not isinstance(listings, list) or not listings:
        return []

    now = datetime.now(timezone.utc).isoformat()
    obs: list[NumericObservation] = []
    for listing in listings[:40]:
        if not isinstance(listing, dict):
            continue
        info = listing.get("propertyInfo") or {}
        if not isinstance(info, dict):
            continue
        main_type = str(info.get("propertyMainType") or "")
        sub_type = str(info.get("propertySubType") or "")
        prop_for = str(info.get("propertyFor") or info.get("transactionType") or "rent")
        if prop_for and prop_for.lower() not in {"rent", "إيجار", "lease", ""}:
            # sale listings on mixed pages
            if "sale" in prop_for.lower() or prop_for in {"بيع"}:
                continue
        if any(x in sub_type for x in _WASALT_EXCLUDE_SUBTYPES):
            continue
        # Prefer retail/showroom; allow office only with café-plausible size + rent.
        is_retail = any(x in sub_type for x in _WASALT_RETAIL_SUBTYPES) or sub_type.lower() in {
            "showroom",
            "shop",
        }
        is_office = "مكتب" in sub_type or "office" in sub_type.lower()
        if not (is_retail or is_office or "تجاري" in main_type or "commercial" in main_type.lower()):
            continue

        rent_raw = info.get("expectedRent")
        try:
            rent_amt = float(rent_raw)
        except (TypeError, ValueError):
            continue
        freq = str(
            info.get("expectedRentType")
            or ((info.get("rentFreq") or {}).get("yearly") or {}).get("freq")
            or ""
        )
        period = "year"
        if any(k in freq for k in ("شهر", "month", "/الشهر", "/mo")):
            period = "month"
        elif any(k in freq for k in ("سنة", "year", "/سنة", "yearly")):
            period = "year"
        elif rent_amt >= 50_000:
            period = "year"
        else:
            period = "month"

        monthly = rent_amt if period == "month" else rent_amt / 12.0
        area_raw = listing.get("floorSize")
        if area_raw in (None, ""):
            for attr in listing.get("attributes") or []:
                if isinstance(attr, dict) and attr.get("key") in {
                    "builtUpArea",
                    "area",
                    "landArea",
                }:
                    area_raw = attr.get("value")
                    break
        try:
            area = float(str(area_raw).replace(",", "")) if area_raw not in (None, "") else None
        except (TypeError, ValueError):
            area = None

        # Filter coworking-desk noise (tiny monthly on huge advertised floors).
        if is_office and not is_retail:
            if monthly < 8_000:
                continue
            if area is not None and not (40 <= area <= 400):
                continue
        if is_retail:
            if monthly < 3_000:
                continue
            # Saudi portals list huge auto/furniture showrooms alongside shop units.
            # Keep only F&B-plausible retail footprints so rent/area bands are not
            # dominated by 500–2,000 m² معرض listings.
            if area is not None and not (20 <= area <= 250):
                continue
        if not (3_000 <= monthly <= 400_000):
            continue

        listing_district = district or str(info.get("district") or "") or None
        listing_title = str(info.get("title") or title or sub_type or "Wasalt listing")
        slug = str(info.get("slug") or listing.get("slug") or "")
        listing_url = url
        if slug and url and "wasalt.sa" in (url or ""):
            listing_url = f"https://wasalt.sa/property/rent/{slug}" if not slug.startswith("http") else slug

        if area and 15 <= area <= 250:
            annual = monthly * 12.0
            per_m2_year = annual / area
            if 50 <= per_m2_year <= 15_000:
                obs.append(
                    NumericObservation(
                        evidence_class="commercial_rent",
                        metric="rent_sar_per_m2_year",
                        value=round(per_m2_year, 2),
                        unit="SAR/m2/year",
                        geography=geography,
                        district=listing_district,
                        period="year",
                        source_url=listing_url,
                        source_title=listing_title,
                        retrieved_at=now,
                        adapter_id="wasalt_next_data",
                        raw_excerpt=f"{listing_title}; {sub_type}; {rent_amt:g}{freq}; {area:g} m2",
                        confidence=0.72,
                        metadata={
                            "listing_amount": rent_amt,
                            "area_m2": area,
                            "period": period,
                            "subtype": sub_type,
                            "source": "wasalt_next_data",
                        },
                    )
                )
            obs.append(
                NumericObservation(
                    evidence_class="commercial_rent",
                    metric="store_area_m2",
                    value=float(area),
                    unit="m2",
                    geography=geography,
                    district=listing_district,
                    source_url=listing_url,
                    source_title=listing_title,
                    retrieved_at=now,
                    adapter_id="wasalt_next_data",
                    raw_excerpt=f"{listing_title}; area {area:g} m2",
                    confidence=0.7,
                    metadata={"subtype": sub_type, "source": "wasalt_next_data"},
                )
            )

        obs.append(
            NumericObservation(
                evidence_class="commercial_rent",
                metric="rent_monthly_sar",
                value=round(monthly, 2),
                unit="SAR/month",
                geography=geography,
                district=listing_district,
                period="month",
                source_url=listing_url,
                source_title=listing_title,
                retrieved_at=now,
                adapter_id="wasalt_next_data",
                raw_excerpt=f"{listing_title}; {sub_type}; monthly≈{monthly:g} from {rent_amt:g}{freq}",
                confidence=0.7,
                metadata={
                    "area_m2": area,
                    "period": period,
                    "subtype": sub_type,
                    "source": "wasalt_next_data",
                },
            )
        )
    return obs


def adapt_rent_listing(
    *,
    text: str,
    html: str = "",
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
) -> list[NumericObservation]:
    """listing price + area + period → SAR/m²/year when possible."""
    if html:
        structured = _adapt_wasalt_next_data(
            html=html, url=url, title=title, geography=geography, district=district
        )
        if structured:
            return structured
    blob = f"{title or ''}\n{text or ''}"
    amounts = extract_sar_amounts(blob)
    areas = [float(m.group(1)) for m in _AREA_M2.finditer(blob)]
    low = blob.lower()
    if not any(
        k in low
        for k in ("rent", "lease", "إيجار", "commercial", "shop for rent", "per sqm", "sqm")
    ):
        return []
    period = "month"
    if any(k in low for k in ("per year", "/year", "annual", "سنوي")):
        period = "year"
    elif any(k in low for k in ("per month", "/month", "/mo", "شهري", "monthly")):
        period = "month"

    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    for amt in amounts:
        if amt < 50 or amt > 5_000_000:
            continue
        area = areas[0] if areas else None
        if area and 15 <= area <= 2000:
            annual = amt * 12 if period == "month" else amt
            per_m2_year = annual / area
            if 50 <= per_m2_year <= 10_000:
                obs.append(
                    NumericObservation(
                        evidence_class="commercial_rent",
                        metric="rent_sar_per_m2_year",
                        value=round(per_m2_year, 2),
                        unit="SAR/m2/year",
                        geography=geography,
                        district=district,
                        period="year",
                        source_url=url,
                        source_title=title,
                        retrieved_at=now,
                        adapter_id="rent_listing",
                        raw_excerpt=blob[:280],
                        confidence=0.62,
                        metadata={"listing_amount": amt, "area_m2": area, "period": period},
                    )
                )
            monthly = amt if period == "month" else amt / 12.0
            if 2_000 <= monthly <= 500_000:
                obs.append(
                    NumericObservation(
                        evidence_class="commercial_rent",
                        metric="rent_monthly_sar",
                        value=round(monthly, 2),
                        unit="SAR/month",
                        geography=geography,
                        district=district,
                        period="month",
                        source_url=url,
                        source_title=title,
                        retrieved_at=now,
                        adapter_id="rent_listing",
                        raw_excerpt=blob[:280],
                        confidence=0.58,
                        metadata={"area_m2": area, "period": period},
                    )
                )
        else:
            monthly = amt if period == "month" else (amt / 12.0 if amt > 50_000 else amt)
            if 3_000 <= monthly <= 400_000:
                obs.append(
                    NumericObservation(
                        evidence_class="commercial_rent",
                        metric="rent_monthly_sar",
                        value=round(monthly, 2),
                        unit="SAR/month",
                        geography=geography,
                        district=district,
                        period="month",
                        source_url=url,
                        source_title=title,
                        retrieved_at=now,
                        adapter_id="rent_listing",
                        raw_excerpt=blob[:280],
                        confidence=0.45,
                        metadata={"period": period, "area_known": False},
                    )
                )
        if areas:
            for a in areas[:2]:
                if 20 <= a <= 800:
                    obs.append(
                        NumericObservation(
                            evidence_class="commercial_rent",
                            metric="store_area_m2",
                            value=float(a),
                            unit="m2",
                            geography=geography,
                            district=district,
                            source_url=url,
                            source_title=title,
                            retrieved_at=now,
                            adapter_id="rent_listing",
                            raw_excerpt=blob[:200],
                            confidence=0.55,
                        )
                    )
        break
    return obs


def adapt_menu_pricing(
    *,
    text: str,
    html: str = "",
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
) -> list[NumericObservation]:
    blob = f"{title or ''}\n{text or ''}"
    html_blob = html or ""
    combined = f"{blob}\n{html_blob[:200000]}"
    low = combined.lower()
    has_menu_kw = any(
        k in low
        for k in (
            "menu",
            "latte",
            "cappuccino",
            "espresso drink",
            "espresso",
            "meal",
            "وجبة",
            "قائمة",
            "price list",
            "delivery",
            "hungerstation",
            "jahez",
            "product",
            "woocommerce",
            "add-to-cart",
            "add to cart",
        )
    )
    has_sar_currency = bool(_SAR_CURRENCY_HINT.search(combined))
    json_prices = [float(x) for x in _JSON_PRICE.findall(html_blob or blob) if _f(x) is not None]
    bdi_prices: list[float] = []
    for rx in (_BDI_PRICE, _BDI_PRICE_ALT):
        for raw in rx.findall(html_blob or ""):
            val = _f(raw)
            if val is not None:
                bdi_prices.append(val)
    # Require menu context OR (SAR currency + structured product prices).
    if not has_menu_kw and not (has_sar_currency and (json_prices or bdi_prices)):
        return []
    amounts = extract_sar_amounts(blob)
    amounts.extend(json_prices)
    amounts.extend(bdi_prices)
    # Prefer drink/menu-like band; drop tip-jar / fee micro-prices and banquet outliers.
    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    seen: set[float] = set()
    for amt in amounts:
        if not (5 <= amt <= 120):
            continue
        key = round(float(amt), 2)
        if key in seen:
            continue
        seen.add(key)
        conf = 0.55 if (json_prices or bdi_prices) and has_sar_currency else 0.5
        obs.append(
            NumericObservation(
                evidence_class="menu_pricing",
                metric="menu_item_sar",
                value=float(key),
                unit="SAR",
                geography=geography,
                district=district,
                role_or_item="menu_item",
                period="one_time",
                source_url=url,
                source_title=title,
                retrieved_at=now,
                adapter_id="menu_pricing",
                raw_excerpt=blob[:240],
                confidence=conf,
                metadata={
                    "structured_price": bool(json_prices or bdi_prices),
                    "sar_currency_hint": has_sar_currency,
                },
            )
        )
        if len(obs) >= 40:
            break
    return obs


def adapt_salary(
    *,
    text: str,
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
) -> list[NumericObservation]:
    blob = f"{title or ''}\n{text or ''}"
    low = blob.lower()
    if not any(
        k in low
        for k in ("salary", "wage", "راتب", "أجور", "compensation", "job vacancy", "hiring", "وظائف")
    ):
        return []
    amounts = extract_sar_amounts(blob)
    role_m = _SALARY_ROLE.search(blob)
    role = role_m.group(1) if role_m else None
    is_min_wage = bool(_MIN_WAGE_HINT.search(blob))
    if is_min_wage and not role:
        role = "statutory_minimum_wage"
    # Prefer explicit monthly framing. Long statutory pages often also mention
    # "annual" elsewhere — that must not convert a "per month" SAR figure.
    has_month = any(
        k in low for k in ("per month", "/month", "monthly", "شهري", "per month")
    )
    has_year = any(k in low for k in ("per year", "/year", "annual salary", "سنوي"))
    if is_min_wage or has_month or not has_year:
        period = "month"
    else:
        period = "year"
    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    # Prefer café-/wage-plausible amounts; skip calendar years (e.g. 2024) first.
    ranked = sorted(
        amounts,
        key=lambda a: (
            0 if 3_000 <= (a / 12.0 if period == "year" else a) <= 25_000 else 1,
            a,
        ),
    )
    for amt in ranked:
        monthly = amt / 12.0 if period == "year" else amt
        if not (2_500 <= monthly <= 40_000):
            continue
        # Statutory minimum pages often list a single national figure — keep one high-signal obs.
        conf = 0.55 if role else 0.45
        if is_min_wage:
            conf = 0.65
            # Prefer the statutory figure itself over incidental role matches in chrome.
            role = "statutory_minimum_wage"
        obs.append(
            NumericObservation(
                evidence_class="salary_labor",
                metric="salary_monthly_sar",
                value=round(monthly, 2),
                unit="SAR/month",
                geography=geography,
                district=district,
                role_or_item=role,
                period="month",
                source_url=url,
                source_title=title,
                retrieved_at=now,
                adapter_id="salary",
                raw_excerpt=blob[:240],
                confidence=conf,
                metadata={
                    "statutory_minimum_wage": is_min_wage,
                    "source_host": _host(url),
                    "period_detected": period,
                },
            )
        )
        if is_min_wage:
            break
    return obs[:20]


def adapt_equipment_catalog(
    *,
    text: str,
    html: str = "",
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    evidence_class: str = "equipment_capex",
    item_hint: str | None = None,
) -> list[NumericObservation]:
    """Vendor catalog prices → SAR CAPEX observations."""
    host = _host(url)
    prices: list[float] = []
    if "amazon." in host:
        for m in _AMAZON_WHOLE.finditer(html or text or ""):
            val = _f(m.group(1))
            if val is not None:
                prices.append(val)
    if "ikea." in host:
        for m in _IKEA_PRICE.finditer(html or text or ""):
            val = _f(m.group(1))
            if val is not None:
                prices.append(val)
    if not prices:
        if host and any(v in host for v in ("amazon.", "ikea.", "jarir.", "extra.", "noon.")):
            prices = extract_sar_amounts(f"{title or ''}\n{text or ''}")
        else:
            return []

    lo, hi = 30.0, 80_000.0
    if evidence_class == "furniture_pos_opening":
        lo, hi = 30.0, 15_000.0
    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    seen: set[float] = set()
    for p in prices:
        if p < lo or p > hi:
            continue
        key = round(p, 2)
        if key in seen:
            continue
        seen.add(key)
        metric = (
            "opening_item_sar"
            if evidence_class == "furniture_pos_opening"
            else "equipment_item_sar"
        )
        obs.append(
            NumericObservation(
                evidence_class=evidence_class,
                metric=metric,
                value=float(key),
                unit="SAR",
                geography=geography,
                role_or_item=item_hint or title,
                period="one_time",
                source_url=url,
                source_title=title,
                retrieved_at=now,
                adapter_id="equipment",
                raw_excerpt=(title or "")[:120],
                confidence=0.6,
                metadata={"vendor_host": host},
            )
        )
        if len(obs) >= 30:
            break
    return obs


def adapt_fitout(
    *,
    text: str,
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
) -> list[NumericObservation]:
    blob = f"{title or ''}\n{text or ''}"
    amounts = extract_sar_amounts(blob)
    areas = [float(m.group(1)) for m in _AREA_M2.finditer(blob)]
    low = blob.lower()
    if not any(k in low for k in ("fit-out", "fit out", "fitout", "renovation", "تشطيب", "تجهيز")):
        return []
    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    for amt in amounts:
        if areas and 15 <= areas[0] <= 2000 and 100 <= amt <= 20_000:
            obs.append(
                NumericObservation(
                    evidence_class="fitout_capex",
                    metric="fitout_sar_per_m2",
                    value=float(amt),
                    unit="SAR/m2",
                    geography=geography,
                    period="one_time",
                    source_url=url,
                    source_title=title,
                    retrieved_at=now,
                    adapter_id="fitout",
                    raw_excerpt=blob[:240],
                    confidence=0.5,
                    metadata={"area_m2": areas[0]},
                )
            )
        elif 20_000 <= amt <= 5_000_000:
            obs.append(
                NumericObservation(
                    evidence_class="fitout_capex",
                    metric="fitout_total_sar",
                    value=float(amt),
                    unit="SAR",
                    geography=geography,
                    period="one_time",
                    source_url=url,
                    source_title=title,
                    retrieved_at=now,
                    adapter_id="fitout",
                    raw_excerpt=blob[:240],
                    confidence=0.45,
                )
            )
    return obs


def adapt_cogs(
    *,
    text: str,
    html: str = "",
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
) -> list[NumericObservation]:
    blob = f"{title or ''}\n{text or ''}"
    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    for m in _PCT.finditer(blob):
        raw = m.group(1) or m.group(2)
        val = _f(raw or "")
        if val is None or not (8 <= val <= 55):
            continue
        obs.append(
            NumericObservation(
                evidence_class="cogs_inputs",
                metric="food_cost_pct",
                value=float(val),
                unit="percent",
                geography=geography,
                period="ongoing",
                source_url=url,
                source_title=title,
                retrieved_at=now,
                adapter_id="cogs",
                raw_excerpt=blob[max(0, m.start() - 40) : m.end() + 40],
                confidence=0.5,
            )
        )
    # Ingredient catalog prices (Amazon etc.) — labeled input_cost_sar only.
    # Never promote these to food_cost_pct (would invent a margin).
    host = _host(url)
    if host and any(v in host for v in ("amazon.", "noon.", "extra.", "jarir.")):
        prices: list[float] = []
        for m in _AMAZON_WHOLE.finditer(html or text or ""):
            val = _f(m.group(1))
            if val is not None:
                prices.append(val)
        if not prices:
            prices = extract_sar_amounts(blob)
        low = blob.lower()
        ingredientish = any(
            k in low
            for k in (
                "milk",
                "bean",
                "beans",
                "flour",
                "sugar",
                "ingredient",
                "حليب",
                "بن",
                "قهوة",
            )
        )
        if ingredientish:
            seen: set[float] = set()
            for pval in prices:
                if not (5 <= pval <= 500):
                    continue
                key = round(float(pval), 2)
                if key in seen:
                    continue
                seen.add(key)
                obs.append(
                    NumericObservation(
                        evidence_class="cogs_inputs",
                        metric="input_cost_sar",
                        value=float(key),
                        unit="SAR",
                        geography=geography,
                        role_or_item=title or "ingredient",
                        period="one_time",
                        source_url=url,
                        source_title=title,
                        retrieved_at=now,
                        adapter_id="cogs",
                        raw_excerpt=(title or "")[:120],
                        confidence=0.45,
                        metadata={
                            "note": "Ingredient catalog price — not a food-cost percent",
                            "vendor_host": host,
                        },
                    )
                )
                if len(seen) >= 20:
                    break
    return obs


ADAPTERS = {
    "rent_listing": adapt_rent_listing,
    "menu_pricing": adapt_menu_pricing,
    "salary": adapt_salary,
    "equipment": adapt_equipment_catalog,
    "fitout": adapt_fitout,
    "cogs": adapt_cogs,
}


def run_adapter(
    adapter_id: str,
    *,
    text: str,
    html: str = "",
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
    evidence_class: str | None = None,
    item_hint: str | None = None,
) -> list[NumericObservation]:
    if adapter_id == "equipment":
        return adapt_equipment_catalog(
            text=text,
            html=html,
            url=url,
            title=title,
            geography=geography,
            evidence_class=evidence_class or "equipment_capex",
            item_hint=item_hint,
        )
    if adapter_id == "menu_pricing":
        return adapt_menu_pricing(
            text=text,
            html=html,
            url=url,
            title=title,
            geography=geography,
            district=district,
        )
    if adapter_id == "cogs":
        return adapt_cogs(
            text=text,
            html=html,
            url=url,
            title=title,
            geography=geography,
        )
    if adapter_id == "rent_listing":
        return adapt_rent_listing(
            text=text,
            html=html,
            url=url,
            title=title,
            geography=geography,
            district=district,
        )
    fn = ADAPTERS.get(adapter_id)
    if not fn:
        return []
    kwargs: dict[str, Any] = {
        "text": text,
        "url": url,
        "title": title,
        "geography": geography,
    }
    if adapter_id in {"rent_listing", "menu_pricing", "salary"}:
        kwargs["district"] = district
    return fn(**kwargs)


def adapt_page_for_classes(
    *,
    evidence_class_ids: list[str],
    adapters_by_class: dict[str, str],
    text: str,
    html: str = "",
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
) -> list[NumericObservation]:
    out: list[NumericObservation] = []
    for eid in evidence_class_ids:
        if not host_allowed_for_evidence_class(url, eid):
            continue
        adapter_id = adapters_by_class.get(eid)
        if not adapter_id:
            continue
        out.extend(
            run_adapter(
                adapter_id,
                text=text,
                html=html,
                url=url,
                title=title,
                geography=geography,
                district=district,
                evidence_class=eid,
            )
        )
    return out
