# Coffee Operating Economics Sprint — Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** `41cd737`  
**DO NOT MERGE**

## Verdict: PARTIAL

Competitor/location depth remains accepted. This sprint added **scalable evidence-class commercial acquisition** and now retrieves:

- Component CAPEX `SYSTEM_ESTIMATE` bands from vendor catalogs
- Menu / average ticket `SYSTEM_ESTIMATE` (Bing/menu follow is intermittent across runs)
- **Commercial rent + store area `SYSTEM_ESTIMATE`** from Wasalt SSR `__NEXT_DATA__` listings, with an F&B footprint filter (20–250 m²)
- **Operating hours/day `SYSTEM_ESTIMATE`** on some runs from OSM `opening_hours` (Overpass mirrors; tag coverage flaky)

Material labor / COGS% / seats→covers / fit-out / working capital remain **UNKNOWN** due to external retrieval blockers — not silent invention. Investment-grade quantitative study is still incomplete.

## 1. Branch / SHA

Latest: `41cd737` on `cursor/coffee-operating-economics-1831`.

## 2. Sources added or enabled (evidence-class strategy — not coffee allowlist patches)

| Domain class | Example hosts | Used for |
|---|---|---|
| `real_estate_listing` | bayut.sa, propertyfinder.sa, aqar.fm, haraj.com.sa, **wasalt.sa** | commercial_rent |
| `job_salary` | bayt.com, indeed, linkedin | salary_labor |
| `delivery_marketplace` | hungerstation, jahez, keeta | menu_pricing |
| `local_brand_website` | *(no static list — OSM website tags + search discovery)* | menu_pricing |
| `equipment_vendor` | amazon.sa, ikea.com, jarir.com, extra.com, noon.com | equipment_capex / cogs input catalogs |
| `fitout_vendor` | amazon/ikea/jarir/extra | furniture_pos_opening / fitout |
| `official_saudi` / `open_geo_encyclopedia` / `search_index` | GASTAT, MISA, OSM / Overpass mirrors (`overpass.osm.ch`, DE), Wikipedia, DDG, Bing | scaffolding |

### Retrieval fixes (this iteration)

- Wasalt commercial + showroom category SSR seeds; adapter parses `__NEXT_DATA__` `searchResult.properties`
- `_adapter_html_slice` preserves `__NEXT_DATA__` when HTML exceeds a naive 200KB cut (critical rent fix)
- Retail footprint filter: keep only **20–250 m²** F&B-plausible units (exclude oversized معرض that skew café rent/area)
- Overpass: try `overpass.osm.ch` then DE mirrors (primary DE often 406 from this IP)
- Bing `setmkt=en-SA&cc=SA`; owner concept blurbs mapped to amenity tokens

## 3. Exact numeric evidence — RUF11 (`study_64691360abd8` / project `1216`)

| Metric | Observations | Sources |
|---|---|---|
| `rent_monthly_sar` / `store_area_m2` | Wasalt listings after ≤250 m² filter | `wasalt.sa` SSR |
| `menu_item_sar` → ticket | Menu/follow prices this run | Bing / brand pages |
| `equipment_item_sar` / `opening_item_sar` | Vendor catalog prices | `amazon.sa` seeds |
| `input_cost_sar` | Ingredient catalogs | amazon seeds (**not** → food_cost_pct) |
| `operating_hours_day` | **Not promoted this run** (Overpass CH mirror reached; opening_hours tags insufficient / not banded) | Overpass |

**Still not retrieved:**

| Class | Blocker |
|---|---|
| salary_labor | Bayt/Indeed 403; no role-specific SAR page reachable |
| food_cost_pct | No sourced COGS % on allowlisted hosts |
| seats_capacity → daily_covers | OSM seats/capacity tags rare; covers correctly blocked |
| fitout_capex / WC | No sourced fit-out / WC quotes |
| DuckDuckGo | Bot challenge (202) |

## 4. Estimate derivations (SYSTEM_ESTIMATE only) — RUF11

| Key | LOW | BASE | HIGH | Derivation |
|---|---|---|---|---|
| `rent_monthly` | 5833 | 8216 | 10000 | Wasalt listing monthly after F&B footprint filter |
| `store_area_m2` | 36 | 57 | 70 | Listing areas ≤250 m² (café-plausible) |
| `avg_ticket` | 20 | 25 | 30 | Menu-item observations → ticket band |
| `equipment_capex` | 114 | 2399 | 36856 | Vendor package |
| `other_capex` | 138 | 1286 | 10208 | Furniture/POS package |
| `operating_hours_day` | — | UNKNOWN | — | OSM hours not banded this run |

No SYSTEM_ESTIMATE without upstream observations. Ingredient SAR ≠ `food_cost_pct`. Capacity ≠ demand copy.

### RUF10 comparison (pre-footprint tighten)

| Key | RUF10 | RUF11 |
|---|---|---|
| `rent_monthly` | 6667–15000–36781 (showroom-skewed) | **5833–8216–10000** |
| `store_area_m2` | 70–669–981 (showroom-skewed) | **36–57–70** |
| `operating_hours_day` | 13.5 | UNKNOWN (flaky tags/mirror content) |
| `avg_ticket` | UNKNOWN | **20–25–30** |

## 5. Final operating assumptions (RUF11)

| Key | Value | Provenance |
|---|---|---|
| location / budget / model / delivery | owner prefs | USER_PROVIDED |
| rent_monthly | 8216 (5833–10000) | SYSTEM_ESTIMATE / ai_estimated |
| store_area_m2 | ~57 | SYSTEM_ESTIMATE |
| avg_ticket | 25 (20–30) | SYSTEM_ESTIMATE |
| equipment_capex / other_capex | ~2399 / ~1286 | SYSTEM_ESTIMATE |
| hours / labor / covers / COGS% / fitout / seats / WC | UNKNOWN | UNKNOWN |

## 6–8. Financial model / LBH / budget

- Revenue still blocked while **daily_covers** UNKNOWN (ticket alone insufficient; seats + hours missing this run)
- Working capital: UNKNOWN (no full opex base)
- Budget vs 450k: **not** investment-grade while labor/fit-out/covers/COGS remain unknown
- Break-even / sensitivity: not commercially meaningful while covers blocked

## 9. Evidence coverage

- Competitors / location: VERIFIED (OSM)
- Numeric coverage: **PARTIAL** — rent, area, ticket, component CAPEX; gaps hours (this run), labor, COGS%, seats/covers, fitout, WC
- CAPACITY→DEMAND: seats/hours missing → covers blocked (correct)

## 10. Runtime / model-path status

| Check | Result |
|---|---|
| Models / `invoke_llm` wiring | Configured |
| Commercial discovery | Wasalt rent path live after HTML-slice + footprint filter; Overpass via CH mirror |
| Search | DDG challenged; Bing used (menu intermittent) |

## 11. Regression

- `tests/test_operating_economics_evidence.py`: **19 passed** (Wasalt fixture + oversized showroom exclusion + HTML-slice + OSM capacity bands)

## 12. Final PASS / PARTIAL / FAIL

**PARTIAL** — café-plausible rent/area bands + ticket + component CAPEX retrieved with evidence provenance; full P&L still blocked on labor / COGS% / seats→covers / fit-out / WC. Hours intermittent.

## 13. MERGE recommendation

**DO NOT MERGE** — owner review required. Do not treat DEFER/PARTIAL as Claude-Level Decision Usefulness PASS for investment-grade economics.

## REAL_USER_FLOW

### RUF10 (post HTML-slice rent fix; pre-footprint tighten)

- Study: `study_1fe42725a83c` / project `1215`
- Artifacts: `/opt/cursor/artifacts/coffee-operating-economics-ruf10/`
- Wins: rent + area (showroom-skewed) + hours + CAPEX
- Gaps: ticket, seats, covers, labor, food_cost_pct, fitout, WC

### RUF11 (after ≤250 m² filter + Overpass CH mirror)

- Study: `study_64691360abd8` / project `1216`
- Owner input only: concept, Olaya/Riyadh, SAR 450k, positioning; ops via AI estimates
- Artifacts: `/opt/cursor/artifacts/coffee-operating-economics-ruf11/`
- Wins: **tight rent/area**, ticket, CAPEX components
- Gaps: hours (this run), seats, covers, labor, food_cost_pct, fitout, WC
