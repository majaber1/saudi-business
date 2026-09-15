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


def test_wageindicator_minimum_wage_salary_adapter():
    """Statutory Saudi private-sector minimum wage is a labor floor observation."""
    html = """
    Private Sector (Saudi nationals)
    Minimum wage with effect from November 19, 2024 SAR4,000.00
    Annual reports and living wage methodology are described elsewhere.
    """
    obs = adapt_salary(
        text=html,
        url="https://wageindicator.org/salary/minimum-wage/saudi-arabia",
        title="Minimum wage - Saudi Arabia",
        geography="Saudi Arabia",
    )
    assert obs
    assert any(abs(o.value - 4000.0) < 0.01 for o in obs)
    assert all(o.metric == "salary_monthly_sar" for o in obs)
    bands = bands_from_observations(obs, geography="Saudi Arabia")
    assert any(b.key == "labor_monthly" for b in bands)


def test_salary_labor_strategy_includes_wageindicator_seed():
    s = resolve_strategy(sector="fnb", city="Riyadh", district="Olaya", amenity="cafe")
    assert any("wageindicator.org" in u for u in s.seed_urls)
    assert any(d.endswith("wageindicator.org") or d == "wageindicator.org" for d in s.allowlist_domains)


def test_salary_observation_not_remapped_to_rent():
    """SAR/month salary statements must not be classified as rent_monthly."""
    from ai_engine.research.schemas import ResearchClaim
    from ai_engine.research.market.service import evidence_items_from_research_claims
    from ai_engine.research.market.operating_estimates import synthesize_operating_estimates

    claims = [
        ResearchClaim(
            statement=(
                "salary_labor observation: statutory_minimum_wage = 4000 SAR/month (SAR). "
                "Adapter: salary."
            ),
            source_url="https://wageindicator.org/salary/minimum-wage/saudi-arabia",
            confidence=0.65,
            source_type="document",
        )
    ]
    items = evidence_items_from_research_claims(claims)
    assert items and items[0].get("metric") == "salary_monthly_sar"
    estimates = synthesize_operating_estimates(evidence_items=items, geography="Riyadh")
    assert any(e.key == "labor_monthly" for e in estimates)
    assert all(e.key != "rent_monthly" or float(e.base) != 4000 for e in estimates)


def test_gap_recovery_prioritizes_labor_and_cogs_seeds():
    """Missing labor/COGS must not be starved by rent/equipment seed budget."""
    from ai_engine.research.evidence.strategy import resolve_strategy

    s = resolve_strategy(
        sector="fnb",
        city="Riyadh",
        district="Olaya",
        amenity="cafe",
        missing_keys=["labor_monthly", "food_cost_pct", "fitout_capex"],
    )
    joined = " ".join(s.seed_urls)
    assert "wageindicator.org" in joined
    # COGS ingredient seeds should survive the budget when prioritized
    assert "amazon.sa" in joined
    assert any("milk" in u or "bean" in u or "coffee" in u for u in s.seed_urls)


def test_capacity_demand_uses_operating_hours_estimate():
    """Hours band must be read alongside seats for capacity derivation."""
    from ai_engine.research.evidence.demand import derive_capacity_and_demand

    blocked = derive_capacity_and_demand(seats=20.0, operating_hours=None)
    assert blocked.get("capacity") is None
    ok = derive_capacity_and_demand(seats=20.0, operating_hours=13.5)
    assert ok.get("capacity") is not None


def test_normalize_role_underscores_and_assistant_manager():
    from ai_engine.research.evidence.adapters import _normalize_role

    assert _normalize_role("Assistant_Manager") == "senior_barista"
    assert _normalize_role("Head_Barista") == "head_barista"
    assert _normalize_role("Restaurant_Manager") == "store_manager"


def test_cogs_fitout_density_html_fallback_when_text_truncated():
    """Connector may pass thin text; adapters must still read HTML body numbers."""
    from ai_engine.research.evidence.adapters import (
        adapt_cogs,
        adapt_fitout,
        adapt_space_density,
        adapt_salary,
        adapt_staffing_ratios,
    )

    cogs_html = "<html><body>" + ("pad " * 5000) + " Food cost percentage is typically 32 percent of sales.</body></html>"
    cogs = adapt_cogs(text=cogs_html[:200], html=cogs_html, url="https://squareup.com/x", title="Food cost")
    assert any(o.metric == "food_cost_pct" and abs(o.value - 32) < 0.1 for o in cogs)

    fit_html = "<html><body>" + ("x" * 5000) + " Fit-out ranges from SAR 480 – 1,960/m² for retail interiors.</body></html>"
    fit = adapt_fitout(text=fit_html[:200], html=fit_html, url="https://archskills.com/x", title="Fit-out")
    assert {round(o.value) for o in fit if o.metric == "fitout_sar_per_m2"} >= {480, 1960}

    dens_html = "<html><body>" + ("y" * 5000) + " Allow 12–15 square feet per seat for coffee shops.</body></html>"
    dens = adapt_space_density(text=dens_html[:200], html=dens_html, url="https://bravecalculator.com/x")
    assert dens and all(o.metric == "dining_m2_per_seat" for o in dens)

    wage_html = "<html><body>" + ("z" * 9000) + " Minimum wage SAR4,000.00 private sector Saudi nationals.</body></html>"
    wage = adapt_salary(
        text=wage_html[:800],
        html=wage_html,
        url="https://wageindicator.org/salary/minimum-wage/saudi-arabia",
        title="Minimum wage - Saudi Arabia",
    )
    assert any(abs(o.value - 4000) < 0.1 for o in wage)

    staff_html = "const RATIOS = { 'cafe': { fohRatio: 30, bohPct: 0.35, mgrPerShift: 1 } };"
    staff = adapt_staffing_ratios(text="", html=staff_html, url="https://shifty-app.com/staffing-calculator/")
    assert {o.metric for o in staff} >= {"staff_foh_guests_per", "staff_boh_share_of_foh", "staff_mgr_per_shift"}


def test_role_payroll_and_seats_from_density():
    from datetime import datetime, timezone
    from ai_engine.research.evidence.observations import NumericObservation
    from ai_engine.research.evidence.bands import bands_from_observations

    now = datetime.now(timezone.utc).isoformat()

    def O(metric, value, **kw):
        return NumericObservation(
            evidence_class=kw.get("ec", "salary_labor"),
            metric=metric,
            value=float(value),
            unit=kw.get("unit", "SAR/month"),
            geography="Riyadh",
            role_or_item=kw.get("role"),
            source_url=kw.get("url", "https://www.payscale.com/x"),
            retrieved_at=now,
            adapter_id="test",
            confidence=0.7,
            metadata=kw.get("meta") or {},
        )

    obs = [
        O("salary_monthly_sar", 3000, role="barista"),
        O("salary_monthly_sar", 4500, role="store_manager"),
        O("salary_monthly_sar", 3500, role="head_barista"),
        O("salary_monthly_sar", 2800, role="cashier"),
        O("salary_monthly_sar", 4000, role="statutory_minimum_wage", meta={"statutory_minimum_wage": True}, url="https://wageindicator.org/x"),
        O("staff_foh_guests_per", 30, unit="guests/foh_staff", url="https://shifty-app.com/x"),
        O("staff_boh_share_of_foh", 0.35, unit="ratio", url="https://shifty-app.com/x"),
        O("staff_mgr_per_shift", 1.0, unit="managers/shift", url="https://shifty-app.com/x"),
        O("dining_m2_per_seat", 1.2, unit="m2/seat", ec="cogs_inputs", url="https://bravecalculator.com/x"),
        O("dining_m2_per_seat", 1.4, unit="m2/seat", ec="cogs_inputs", url="https://bravecalculator.com/x"),
        O("store_area_m2", 57, unit="m2", ec="commercial_rent", url="https://wasalt.sa/x"),
        O("operating_hours_day", 13.5, unit="hours", ec="capacity_signals", url="https://overpass-api.de/x"),
        O("menu_item_sar", 18, unit="SAR", ec="menu_pricing", url="https://explore-saudi.com/x"),
        O("menu_item_sar", 24, unit="SAR", ec="menu_pricing", url="https://explore-saudi.com/x"),
        O("menu_item_sar", 30, unit="SAR", ec="menu_pricing", url="https://rimthancoffee.com/x"),
        O("food_cost_pct", 32, unit="percent", ec="cogs_inputs", url="https://squareup.com/x"),
        O("fitout_sar_per_m2", 1000, unit="SAR/m2", ec="fitout_capex", url="https://archskills.com/x"),
        O("fitout_sar_per_m2", 1800, unit="SAR/m2", ec="fitout_capex", url="https://archskills.com/x"),
    ]
    bands = bands_from_observations(obs, geography="Olaya, Riyadh", store_area_m2=57.0)
    by = {b.key: b for b in bands}
    assert "avg_ticket" in by
    assert by["avg_ticket"].base != 25 or by["avg_ticket"].low != 20  # not the old hardcoded 20/25/30 triple alone
    assert "labor_monthly" in by
    assert by["labor_monthly"].base > 10000  # role payroll, not 4000 floor
    assert "role_based" in (by["labor_monthly"].derivation or "").lower() or (
        (by["labor_monthly"].metadata or {}).get("payroll_model") == "role_based_staffing_ratios"
    )
    assert "seats_capacity" in by
    assert by["seats_capacity"].base > 10
    assert "food_cost_pct" in by
    assert abs(by["food_cost_pct"].base - 32) < 1
    assert "fitout_capex" in by
    assert by["fitout_capex"].base > 10000


def test_strategy_includes_opecon_benchmark_seeds():
    s = resolve_strategy(sector="fnb", city="Riyadh", district="Olaya", amenity="cafe", query="specialty coffee")
    joined = " ".join(s.seed_urls)
    assert "payscale.com" in joined
    assert "shifty-app.com" in joined
    assert "archskills.com" in joined
    assert "squareup.com" in joined
    assert "bravecalculator.com" in joined
    assert "explore-saudi.com" in joined or "rimthancoffee.com" in joined
