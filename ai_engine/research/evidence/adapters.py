"""Source-specific numeric evidence adapters (generic, not coffee-hardcoded)."""
from __future__ import annotations

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
    r"([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(?:SAR|SR|ر\.?\s*س\.?|ريال)",
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
    return False


def extract_sar_amounts(text: str) -> list[float]:
    out: list[float] = []
    for m in _SAR_NUM.finditer(text or ""):
        raw = m.group(1) or m.group(2)
        val = _f(raw or "")
        if val is not None:
            out.append(val)
    return out


def adapt_rent_listing(
    *,
    text: str,
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
) -> list[NumericObservation]:
    """listing price + area + period → SAR/m²/year when possible."""
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
    url: str | None = None,
    title: str | None = None,
    geography: str = "Saudi Arabia",
    district: str | None = None,
) -> list[NumericObservation]:
    blob = f"{title or ''}\n{text or ''}"
    low = blob.lower()
    if not any(
        k in low
        for k in (
            "menu",
            "latte",
            "cappuccino",
            "espresso drink",
            "meal",
            "وجبة",
            "قائمة",
            "price list",
            "delivery",
            "hungerstation",
            "jahez",
        )
    ):
        return []
    amounts = extract_sar_amounts(blob)
    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    for amt in amounts:
        if 5 <= amt <= 120:
            obs.append(
                NumericObservation(
                    evidence_class="menu_pricing",
                    metric="menu_item_sar",
                    value=float(amt),
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
                    confidence=0.5,
                )
            )
    return obs[:40]


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
    period = "month"
    if any(k in low for k in ("per year", "annual", "/year", "سنوي")):
        period = "year"
    obs: list[NumericObservation] = []
    now = datetime.now(timezone.utc).isoformat()
    for amt in amounts:
        monthly = amt / 12.0 if period == "year" else amt
        if not (2_500 <= monthly <= 40_000):
            continue
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
                confidence=0.55 if role else 0.45,
            )
        )
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
