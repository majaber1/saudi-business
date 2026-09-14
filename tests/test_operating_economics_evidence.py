"""Operating economics — evidence-class strategy, adapters, bands, demand."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

if not os.environ.get("DATABASE_URL"):
    _tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _tmp.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "backend"))

from ai_engine.research.evidence.adapters import (  # noqa: E402
    adapt_equipment_catalog,
    adapt_menu_pricing,
    adapt_page_for_classes,
    adapt_rent_listing,
    adapt_salary,
    host_allowed_for_evidence_class,
)
from ai_engine.research.evidence.bands import bands_from_observations  # noqa: E402
from ai_engine.research.evidence.coverage import (  # noqa: E402
    coverage_gaps,
    validate_numeric_coverage,
)
from ai_engine.research.evidence.demand import derive_capacity_and_demand  # noqa: E402
from ai_engine.research.evidence.observations import NumericObservation  # noqa: E402
from ai_engine.research.evidence.strategy import (  # noqa: E402
    allowlist_for_classes,
    evidence_classes_for_sector,
    resolve_strategy,
)
from ai_engine.research.market.operating_estimates import (  # noqa: E402
    synthesize_operating_estimates,
)


def test_evidence_classes_not_coffee_hardcoded_allowlist():
    fnb = evidence_classes_for_sector("F&B cafe")
    mfg = evidence_classes_for_sector("manufacturing factory")
    assert "commercial_rent" in fnb
    assert "menu_pricing" in fnb
    assert "equipment_capex" in mfg
    assert "menu_pricing" not in mfg  # manufacturing does not need café menus
    allow = allowlist_for_classes(fnb)
    assert "amazon.sa" in allow or "www.amazon.sa" in allow
    assert "bayut.sa" in allow or "www.bayut.sa" in allow
    # Strategy expands beyond bootstrap OSM/DDG domains
    assert len(allow) > 15


def test_resolve_strategy_seed_owners_scoped():
    s = resolve_strategy(
        sector="fnb",
        city="Riyadh",
        district="Olaya",
        amenity="cafe",
        query="specialty coffee",
    )
    assert s.seed_urls
    owners = s.meta.get("seed_owners") or {}
    assert owners
    # espresso seed belongs to equipment, not salary
    espresso = [u for u in s.seed_urls if "espresso" in u or "amazon.sa/s" in u]
    assert espresso
    for u in espresso:
        classes = owners.get(u) or []
        assert "salary_labor" not in classes


def test_host_gate_blocks_salary_on_amazon():
    assert host_allowed_for_evidence_class(
        "https://www.amazon.sa/s?k=espresso", "equipment_capex"
    )
    assert not host_allowed_for_evidence_class(
        "https://www.amazon.sa/s?k=espresso", "salary_labor"
    )
    assert not host_allowed_for_evidence_class(
        "https://www.amazon.sa/s?k=espresso", "menu_pricing"
    )


def test_rent_adapter_normalizes_to_sar_m2_year():
    text = "Commercial shop for rent in Olaya: SAR 15,000 per month, 80 sqm retail unit."
    obs = adapt_rent_listing(
        text=text,
        url="https://www.bayut.sa/en/listing/1",
        title="Shop rent Olaya",
        geography="Olaya, Riyadh",
        district="Olaya",
    )
    metrics = {o.metric for o in obs}
    assert "rent_monthly_sar" in metrics or "rent_sar_per_m2_year" in metrics
    m2 = [o for o in obs if o.metric == "rent_sar_per_m2_year"]
    if m2:
        # 15000*12/80 = 2250
        assert abs(m2[0].value - 2250) < 1


def test_salary_adapter_requires_salary_keywords():
    assert adapt_salary(text="Espresso machine SAR 4500", url="https://example.com") == []
    obs = adapt_salary(
        text="Barista salary in Riyadh SAR 4500 per month hiring now",
        url="https://www.bayt.com/job/1",
        title="Barista job",
    )
    assert obs and obs[0].metric == "salary_monthly_sar"
    assert obs[0].value == 4500


def test_menu_adapter_keyword_gate():
    assert adapt_menu_pricing(text="Widget SAR 25 only", url="https://hungerstation.com/x") == []
    obs = adapt_menu_pricing(
        text="Café menu: Latte SAR 18, Cappuccino SAR 20, Meal SAR 32",
        url="https://hungerstation.com/sa-en/r/1",
    )
    assert len(obs) >= 2
    assert all(o.metric == "menu_item_sar" for o in obs)


def test_equipment_amazon_prices_and_bands():
    html = '<span class="a-price-whole">3,299</span><span class="a-price-whole">4,499</span><span class="a-price-whole">5,199</span>'
    obs = adapt_equipment_catalog(
        text="",
        html=html,
        url="https://www.amazon.sa/s?k=commercial+espresso+machine",
        title="Espresso machines",
    )
    assert len(obs) == 3
    bands = bands_from_observations(obs, geography="Riyadh, Saudi Arabia")
    by = {b.key: b for b in bands}
    assert "equipment_capex" in by
    assert by["equipment_capex"].low <= by["equipment_capex"].base <= by["equipment_capex"].high
    assert by["equipment_capex"].observation_count == 3


def test_adapt_page_for_classes_no_cross_fire():
    html = '<span class="a-price-whole">3,299</span>'
    obs = adapt_page_for_classes(
        evidence_class_ids=["equipment_capex", "salary_labor", "menu_pricing"],
        adapters_by_class={
            "equipment_capex": "equipment",
            "salary_labor": "salary",
            "menu_pricing": "menu_pricing",
        },
        text="Espresso machine SAR 3299",
        html=html,
        url="https://www.amazon.sa/s?k=espresso",
        title="Amazon",
    )
    assert obs
    assert all(o.evidence_class == "equipment_capex" for o in obs)


def test_capacity_vs_demand_never_equal_by_default():
    out = derive_capacity_and_demand(seats=40, operating_hours=12, competitor_density_count=10)
    assert out["capacity"]["kind"] == "CAPACITY_ESTIMATE"
    assert out["demand"]["kind"] == "DEMAND_ESTIMATE"
    assert out["demand"]["base"] < out["capacity"]["base"]
    blocked = derive_capacity_and_demand(seats=40, operating_hours=12, competitor_density_count=None)
    assert blocked["demand"] is None


def test_coverage_gaps_and_no_estimate_without_evidence():
    gaps = coverage_gaps(assumptions=[{"key": "equipment_capex", "value": "UNKNOWN"}])
    assert "avg_ticket" in gaps
    assert "equipment_capex" in gaps
    est = synthesize_operating_estimates(evidence_items=[], geography="Riyadh")
    assert est == []
    # Structured observations produce SYSTEM_ESTIMATE
    items = [
        {
            "metric": "equipment_item_sar",
            "value": 4000,
            "unit": "SAR",
            "source_url": "https://www.amazon.sa/x",
            "evidence_class": "equipment_capex",
            "statement": "equipment_capex observation: equipment_item_sar = 4000 SAR",
        },
        {
            "metric": "equipment_item_sar",
            "value": 5500,
            "unit": "SAR",
            "source_url": "https://www.amazon.sa/y",
            "evidence_class": "equipment_capex",
            "statement": "equipment_capex observation: equipment_item_sar = 5500 SAR",
        },
        {
            "metric": "equipment_item_sar",
            "value": 7000,
            "unit": "SAR",
            "source_url": "https://www.extra.com/z",
            "evidence_class": "equipment_capex",
            "statement": "equipment_capex observation: equipment_item_sar = 7000 SAR",
        },
    ]
    est2 = synthesize_operating_estimates(evidence_items=items, geography="Riyadh")
    assert any(e.key == "equipment_capex" for e in est2)
    assert all(e.provenance_class == "SYSTEM_ESTIMATE" for e in est2)


def test_validate_numeric_coverage_partial():
    cov = validate_numeric_coverage(estimate_keys=["equipment_capex", "other_capex"])
    assert cov["status"] == "PARTIAL"
    assert cov["commercially_useful"] is False


def test_local_brand_host_gate_allows_discovered_menu_sites():
    assert host_allowed_for_evidence_class("https://barista.sa/en/menu/", "menu_pricing")
    assert host_allowed_for_evidence_class("https://noircafe.sa/pages/menu", "menu_pricing")
    # Equipment catalogs must remain blocked for menu
    assert not host_allowed_for_evidence_class(
        "https://www.amazon.sa/s?k=espresso", "menu_pricing"
    )


def test_menu_adapter_parses_json_and_bdi_sar_prices():
    html = """
    <script>Object.assign(window.x,{"currency":"SAR","products":{"1":{"price":15},"2":{"price":18},"3":{"price":22}}});</script>
    <span class="woocommerce-Price-currencySymbol">&#x631;.&#x633;</span>17.00</bdi>
    """
    obs = adapt_menu_pricing(
        text="Cafe menu specialty drinks",
        html=html,
        url="https://barista.sa/en/menu/",
        title="Menu",
    )
    vals = sorted({o.value for o in obs})
    assert 15 in vals and 18 in vals and 22 in vals
    assert all(o.metric == "menu_item_sar" for o in obs)
    bands = bands_from_observations(obs, geography="Riyadh")
    by = {b.key: b for b in bands}
    assert "avg_ticket" in by
    assert by["avg_ticket"].low <= by["avg_ticket"].base <= by["avg_ticket"].high


def test_cogs_input_cost_not_promoted_to_food_cost_pct():
    from ai_engine.research.evidence.adapters import adapt_cogs

    html = '<span class="a-price-whole">24</span><span class="a-price-whole">32</span>'
    obs = adapt_cogs(
        text="fresh milk 1L grocery ingredient",
        html=html,
        url="https://www.amazon.sa/s?k=fresh+milk+1L",
        title="Fresh milk 1L",
    )
    assert obs
    assert all(o.metric == "input_cost_sar" for o in obs)
    bands = bands_from_observations(obs, geography="Riyadh")
    assert not any(b.key == "food_cost_pct" for b in bands)


def test_sector_blurb_uses_amenity_search_token():
    from ai_engine.research.evidence.strategy import resolve_strategy

    long = (
        "Premium specialty coffee shop (third-wave) targeting young professionals "
        "and office workers in Olaya, Riyadh"
    )
    s = resolve_strategy(sector=long, city="Riyadh", district="Olaya", amenity="cafe")
    joined = " | ".join(s.queries)
    assert "cafe menu" in joined.lower()
    assert "third-wave" not in joined.lower()


def test_wasalt_seeds_in_commercial_rent_strategy():
    s = resolve_strategy(sector="fnb", city="Riyadh", district="Olaya", amenity="cafe")
    seeds = " ".join(s.seed_urls)
    assert "wasalt.sa" in seeds
    assert "عقارات-تجارية-للايجار-في-الرياض" in seeds
    assert "صالات-عرض-للايجار-في-الرياض" in seeds
    assert any(d.endswith("wasalt.sa") or d == "wasalt.sa" for d in s.allowlist_domains)


def test_wasalt_next_data_rent_adapter_fixture():
    html = """
    <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"searchResult":{"properties":[
      {"floorSize":"80","propertyInfo":{
        "propertyMainType":"تجاري","propertySubType":"معرض","propertyFor":"rent",
        "expectedRent":120000,"expectedRentType":"/سنة","title":"معرض للإيجار",
        "district":"العليا","slug":"showroom-olaya-1"
      }},
      {"floorSize":"60","propertyInfo":{
        "propertyMainType":"تجاري","propertySubType":"معرض","propertyFor":"rent",
        "expectedRent":96000,"expectedRentType":"/سنة","title":"معرض 2",
        "district":"العليا","slug":"showroom-olaya-2"
      }},
      {"floorSize":"980","propertyInfo":{
        "propertyMainType":"تجاري","propertySubType":"معرض","propertyFor":"rent",
        "expectedRent":320000,"expectedRentType":"/سنة","title":"huge showroom",
        "district":"العليا","slug":"showroom-huge"
      }},
      {"floorSize":"9000","propertyInfo":{
        "propertyMainType":"تجاري","propertySubType":"مكتب","propertyFor":"rent",
        "expectedRent":1000,"expectedRentType":"/سنة","title":"cowork desk",
        "district":"السويدي","slug":"desk-1"
      }}
    ]}}}}
    </script>
    """
    obs = adapt_rent_listing(
        text="commercial rent Riyadh",
        html=html,
        url="https://wasalt.sa/عقارات-تجارية-للايجار-في-الرياض",
        title="Wasalt commercial",
        geography="Riyadh",
        district="Olaya",
    )
    assert obs
    monthly = [o.value for o in obs if o.metric == "rent_monthly_sar"]
    assert 10000.0 in monthly and 8000.0 in monthly
    # Coworking desk noise + oversized showrooms excluded
    assert all(v >= 3000 for v in monthly)
    areas = [o.value for o in obs if o.metric == "store_area_m2"]
    assert 80.0 in areas and 60.0 in areas
    assert 980.0 not in areas
    bands = bands_from_observations(obs, geography="Riyadh")
    assert any(b.key == "rent_monthly" for b in bands)


def test_osm_capacity_signals_to_bands():
    from ai_engine.research.evidence.adapters import adapt_osm_capacity_signals

    obs = adapt_osm_capacity_signals(
        seat_tags=[
            {"name": "Cafe A", "metric": "seats", "value": 28},
            {"name": "Cafe B", "metric": "capacity", "value": 36},
        ],
        opening_hours_tags=[
            {"name": "Cafe A", "value": "Mo-Su 08:00-22:00"},
            {"name": "Cafe B", "value": "Mo-Fr 09:00-23:00"},
        ],
        geography="Riyadh",
        district="Olaya",
    )
    assert {o.metric for o in obs} >= {"seats_capacity", "operating_hours_day"}
    bands = bands_from_observations(obs, geography="Riyadh")
    keys = {b.key for b in bands}
    assert "seats_capacity" in keys
    assert "operating_hours_day" in keys


def test_adapter_html_slice_preserves_next_data_beyond_200k():
    """Regression: Wasalt SSR JSON often sits past a naive 200KB HTML cut."""
    sys.path.insert(0, str(_ROOT / "backend"))
    from app.integrations.sources.commercial_discovery import _adapter_html_slice

    payload = (
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"searchResult":{"properties":[{"id":1}]}}}}'
        "</script>"
    )
    html = ("<!--pad-->" * 30000) + payload  # >200KB prefix
    assert len(html) > 200_000
    sliced = _adapter_html_slice(html, limit=200_000)
    assert "__NEXT_DATA__" in sliced
    assert "searchResult" in sliced
    assert len(sliced) <= 200_000 + 200
