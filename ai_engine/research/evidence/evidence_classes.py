"""Evidence classes — what numeric evidence we seek and how to acquire it.

Each class binds: domain classes + query templates + seed URL templates + adapter.
Sector packs declare which evidence classes they need; the commercial connector
resolves allowlists and seeds from this registry (not coffee-hardcoded domains).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus


@dataclass(frozen=True)
class EvidenceClassSpec:
    id: str
    label: str
    assumption_keys: tuple[str, ...]
    domain_classes: tuple[str, ...]
    adapter_id: str
    query_templates: tuple[str, ...] = ()
    # Seed catalog URL templates. Placeholders: {city}, {city_slug}, {district},
    # {sector}, {query}, {query_enc}. Never coffee-only product numbers.
    seed_url_templates: tuple[str, ...] = ()
    notes: str = ""


EVIDENCE_CLASSES: dict[str, EvidenceClassSpec] = {
    "commercial_rent": EvidenceClassSpec(
        id="commercial_rent",
        label="Commercial rent",
        assumption_keys=("rent_monthly", "store_area_m2"),
        domain_classes=("real_estate_listing", "market_report", "search_index"),
        adapter_id="rent_listing",
        query_templates=(
            "commercial rent SAR {city} {district} retail shop",
            "{city} commercial rent per sqm Saudi Arabia",
            "إيجار محل تجاري {city} {district}",
        ),
        seed_url_templates=(
            "https://www.bayut.sa/en/for-rent/commercial/{city_slug}/",
            "https://haraj.com.sa/",
            "https://haraj.com.sa/tags/{city_ar}_إيجار%20محل",
        ),
        notes="Normalize to SAR/m²/year when area+period present; else SAR/month.",
    ),
    "menu_pricing": EvidenceClassSpec(
        id="menu_pricing",
        label="Menu / ticket pricing",
        assumption_keys=("avg_ticket",),
        domain_classes=(
            "delivery_marketplace",
            "local_brand_website",
            "market_report",
            "search_index",
        ),
        adapter_id="menu_pricing",
        query_templates=(
            "{sector} menu prices {city} SAR",
            "{sector} specialty coffee menu price SAR {city}",
            "{sector} average drink price SAR {city} {district}",
            "أسعار قائمة {sector} {city}",
            "{city} {sector} menu SAR site:.sa",
        ),
        seed_url_templates=("https://hungerstation.com/sa-en",),
        notes="Product observations → comparable basket → low/base/high ticket.",
    ),
    "salary_labor": EvidenceClassSpec(
        id="salary_labor",
        label="Salaries / staffing labor cost",
        assumption_keys=("labor_monthly",),
        domain_classes=("job_salary", "official_saudi", "search_index"),
        adapter_id="salary",
        query_templates=(
            "{sector} staff salary SAR Saudi Arabia {city}",
            "{sector} worker monthly salary SAR {city}",
            "راتب موظف {sector} {city}",
        ),
        seed_url_templates=(),
        notes="Role + geography + period → monthly SAR.",
    ),
    "equipment_capex": EvidenceClassSpec(
        id="equipment_capex",
        label="Equipment CAPEX",
        assumption_keys=("equipment_capex",),
        domain_classes=("equipment_vendor", "search_index"),
        adapter_id="equipment",
        query_templates=(
            "commercial {sector} equipment price SAR Saudi Arabia",
            "{sector} machine cost SAR",
        ),
        seed_url_templates=(
            "https://www.amazon.sa/s?k={query_enc}",
            "https://www.extra.com/en-sa/search/?q={query_enc}",
            "https://www.ikea.com/sa/en/search/products/?q={query_enc}",
        ),
        notes="Item + vendor → SAR CAPEX observations. Seed queries use sector tokens.",
    ),
    "fitout_capex": EvidenceClassSpec(
        id="fitout_capex",
        label="Fit-out / renovation CAPEX",
        assumption_keys=("fitout_capex",),
        domain_classes=("fitout_vendor", "market_report", "search_index"),
        adapter_id="fitout",
        query_templates=(
            "{sector} fit out cost SAR Saudi Arabia small shop",
            "commercial fit-out cost per sqm SAR {city}",
        ),
        seed_url_templates=(),
        notes="Prefer SAR/m² with scope; do not confuse unit rates with total CAPEX.",
    ),
    "furniture_pos_opening": EvidenceClassSpec(
        id="furniture_pos_opening",
        label="Furniture / POS / opening costs",
        assumption_keys=("other_capex", "furniture_capex", "pos_capex"),
        domain_classes=("fitout_vendor", "equipment_vendor", "search_index"),
        adapter_id="equipment",
        query_templates=(
            "POS system price SAR Saudi Arabia",
            "cafe furniture SAR {city}",
        ),
        seed_url_templates=(
            "https://www.amazon.sa/s?k={pos_query_enc}",
            "https://www.amazon.sa/s?k={furniture_query_enc}",
            "https://www.ikea.com/sa/en/cat/dining-furniture-46080/",
            "https://www.jarir.com/sa-en/catalogsearch/result/?q=pos",
        ),
        notes="Opening package components with vendor provenance.",
    ),
    "cogs_inputs": EvidenceClassSpec(
        id="cogs_inputs",
        label="COGS / input cost signals",
        assumption_keys=("food_cost_pct",),
        domain_classes=("market_report", "official_saudi", "search_index", "equipment_vendor"),
        adapter_id="cogs",
        query_templates=(
            "F&B food cost percentage Saudi Arabia",
            "{sector} COGS percent restaurant Saudi",
            "تكلفة البضاعة المباعة مطاعم السعودية",
        ),
        seed_url_templates=(
            "https://www.amazon.sa/s?k={cogs_milk_query_enc}",
            "https://www.amazon.sa/s?k={cogs_beans_query_enc}",
        ),
        notes=(
            "Percent COGS only when sourced. Amazon ingredient catalog prices are "
            "input_cost_sar observations only — never promoted to food_cost_pct."
        ),
    ),
}

# Sector → evidence classes (generic; manufacturing/saas can extend).
SECTOR_EVIDENCE_CLASSES: dict[str, tuple[str, ...]] = {
    "fnb": (
        "commercial_rent",
        "menu_pricing",
        "salary_labor",
        "equipment_capex",
        "fitout_capex",
        "furniture_pos_opening",
        "cogs_inputs",
    ),
    "manufacturing": (
        "commercial_rent",
        "salary_labor",
        "equipment_capex",
        "fitout_capex",
        "cogs_inputs",
    ),
    "saas": (
        "salary_labor",
        "cogs_inputs",
    ),
    "default": (
        "commercial_rent",
        "salary_labor",
        "equipment_capex",
        "fitout_capex",
        "furniture_pos_opening",
    ),
}


def _city_slug(city: str) -> str:
    c = (city or "riyadh").strip().lower()
    mapping = {
        "riyadh": "riyadh",
        "الرياض": "riyadh",
        "jeddah": "jeddah",
        "جدة": "jeddah",
        "dammam": "dammam",
        "الدمام": "dammam",
    }
    return mapping.get(c, quote_plus(c.replace(" ", "-")))


def render_template(template: str, *, ctx: dict[str, str]) -> str:
    out = template
    for k, v in ctx.items():
        out = out.replace("{" + k + "}", v)
    return out


def build_render_context(
    *,
    city: str = "",
    district: str = "",
    sector: str = "",
    query: str = "",
    amenity: str = "",
) -> dict[str, str]:
    raw_sector = (sector or "").strip()
    amenity_token = (amenity or "").strip()
    # Opaque sector codes (fnb/saas) are bad web-search tokens (Bing → First National Bank).
    opaque = {"fnb", "f&b", "saas", "qsr"}
    # Long free-text sector blurbs (owner concept sentences) also poison search queries.
    looks_like_blurb = (
        len(raw_sector) > 40
        or raw_sector.count(" ") >= 5
        or any(x in raw_sector.lower() for x in ("targeting", "positioning", "professionals", "workers"))
    )
    if (raw_sector.lower() in opaque or looks_like_blurb) and amenity_token:
        sector_token = amenity_token
    elif raw_sector.lower() in opaque:
        sector_token = "cafe" if raw_sector.lower() in {"fnb", "f&b", "qsr"} else "local business"
    elif looks_like_blurb:
        # Infer a short search token from the blurb when amenity is missing.
        low = raw_sector.lower()
        if any(k in low for k in ("cafe", "coffee", "مقهى", "قهوة")):
            sector_token = "cafe"
        elif any(k in low for k in ("restaurant", "dining", "مطعم")):
            sector_token = "restaurant"
        else:
            sector_token = "local business"
    else:
        sector_token = (raw_sector or amenity_token or "local business").strip() or "local business"
    # Equipment seed keywords stay generic to sector/amenity — not coffee hardcodes.
    equip_q = f"commercial {sector_token} equipment"
    if amenity_token in {"cafe", "restaurant", "bakery"} or "coffee" in sector_token.lower():
        equip_q = "commercial espresso machine"
    pos_q = "POS system cash register"
    furniture_q = f"{sector_token} furniture table"
    city_ar_map = {
        "riyadh": "الرياض",
        "الرياض": "الرياض",
        "jeddah": "جدة",
        "جدة": "جدة",
        "dammam": "الدمام",
        "الدمام": "الدمام",
    }
    city_key = (city or "Riyadh").strip().lower()
    city_ar = city_ar_map.get(city_key, city or "الرياض")
    # Generic F&B input seeds (sector-tokenized) — not hard-coded product economics.
    milk_q = "fresh milk 1L"
    beans_q = f"{sector_token} beans wholesale" if sector_token else "food ingredients"
    if amenity in {"cafe", "restaurant", "bakery"} or "coffee" in sector_token.lower():
        beans_q = "green coffee beans 1kg"
    return {
        "city": city or "Riyadh",
        "city_slug": _city_slug(city or "Riyadh"),
        "city_ar": city_ar,
        "district": district or "",
        "sector": sector_token,
        "query": query or sector_token,
        "query_enc": quote_plus(equip_q),
        "pos_query_enc": quote_plus(pos_q),
        "furniture_query_enc": quote_plus(furniture_q),
        "cogs_milk_query_enc": quote_plus(milk_q),
        "cogs_beans_query_enc": quote_plus(beans_q),
        "amenity": amenity or "",
    }


def evidence_class_public_meta() -> list[dict[str, Any]]:
    return [
        {
            "id": e.id,
            "label": e.label,
            "assumption_keys": list(e.assumption_keys),
            "domain_classes": list(e.domain_classes),
            "adapter_id": e.adapter_id,
            "seed_url_count": len(e.seed_url_templates),
            "notes": e.notes,
        }
        for e in EVIDENCE_CLASSES.values()
    ]
