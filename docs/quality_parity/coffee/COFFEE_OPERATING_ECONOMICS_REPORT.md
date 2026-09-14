# Coffee Operating Economics Sprint — Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** _(see latest commit on branch)_  
**DO NOT MERGE**

## Verdict: PARTIAL

Competitor/location depth remains accepted. This sprint added **scalable evidence-class commercial acquisition** and now retrieves:

- Component CAPEX `SYSTEM_ESTIMATE` bands from vendor catalogs
- Menu / average ticket `SYSTEM_ESTIMATE` on some runs (Bing/menu follow is flaky)
- **Commercial rent + store area `SYSTEM_ESTIMATE`** from Wasalt SSR `__NEXT_DATA__` listings
- **Operating hours/day `SYSTEM_ESTIMATE`** from OSM `opening_hours` (Overpass mirrors)

Material labor / COGS% / seats→covers / fit-out / working capital remain **UNKNOWN** due to external retrieval blockers — not silent invention. Investment-grade quantitative study is still incomplete.

## 1. Branch / SHA

See latest commits on `cursor/coffee-operating-economics-1831`.

## 2. Sources added or enabled (evidence-class strategy — not coffee allowlist patches)

| Domain class | Example hosts | Used for |
|---|---|---|
| `real_estate_listing` | bayut.sa, propertyfinder.sa, aqar.fm, haraj.com.sa, **wasalt.sa** | commercial_rent |
| `job_salary` | bayt.com, indeed, linkedin | salary_labor |
| `delivery_marketplace` | hungerstation, jahez, keeta | menu_pricing |
| `local_brand_website` | *(no static list — OSM website tags + search discovery)* | menu_pricing |
| `equipment_vendor` | amazon.sa, ikea.com, jarir.com, extra.com, noon.com | equipment_capex / cogs input catalogs |
| `fitout_vendor` | amazon/ikea/jarir/extra | furniture_pos_opening / fitout |
| `official_saudi` / `open_geo_encyclopedia` / `search_index` | GASTAT, MISA, OSM/Overpass mirrors, Wikipedia, DDG, Bing | scaffolding |

### Retrieval fixes (this iteration)

- Wasalt commercial + showroom category SSR seeds; adapter parses `__NEXT_DATA__` `searchResult.properties`
- `_adapter_html_slice` preserves `__NEXT_DATA__` when HTML exceeds a naive 200KB cut (critical rent fix)
- Retail footprint filter: keep only **20–250 m²** F&B-plausible units (exclude oversized معرض that skew café rent/area)
- Overpass: try `overpass.osm.ch` then DE mirrors (primary DE often 406 from this IP)
- Bing `setmkt=en-SA&cc=SA`; owner concept blurbs mapped to amenity tokens

## 3. Exact numeric evidence — RUF10 (`study_1fe42725a83c` / project `1215`)

| Metric | Observations | Sources |
|---|---|---|
| `rent_monthly_sar` / `store_area_m2` | Wasalt commercial (6) + showroom (74) listings | `wasalt.sa` SSR |
| `operating_hours_day` | OSM opening_hours → 13.5 h/day | Overpass |
| `equipment_item_sar` / `opening_item_sar` | Vendor catalog prices | `amazon.sa` seeds |
| `menu_item_sar` | **0 this run** (ticket UNKNOWN; prior RUF8 had ~55–70–85) | Bing/menu flaky |
| `input_cost_sar` | Ingredient catalogs | amazon seeds (**not** → food_cost_pct) |

**Still not retrieved:**

| Class | Blocker |
|---|---|
| salary_labor | Bayt/Indeed 403; no role-specific SAR page reachable |
| food_cost_pct | No sourced COGS % on allowlisted hosts |
| seats_capacity → daily_covers | OSM seats/capacity tags rare; covers correctly blocked |
| fitout_capex / WC | No sourced fit-out / WC quotes |
| DuckDuckGo | Bot challenge (202) |

## 4. Estimate derivations (SYSTEM_ESTIMATE only) — RUF10

| Key | LOW | BASE | HIGH | Derivation |
|---|---|---|---|---|
| `rent_monthly` | 6667 | 15000 | 36781 | Wasalt listing monthly (showroom-skewed before ≤250 m² filter) |
| `store_area_m2` | 70 | 669 | 981 | Listing areas (showroom-skewed; filter tightening for RUF11+) |
| `operating_hours_day` | 13.5 | 13.5 | 13.5 | Parsed OSM opening_hours |
| `equipment_capex` | 114 | 2532 | 36856 | Vendor package |
| `other_capex` | 138 | 1296 | 10208 | Furniture/POS package |
| `avg_ticket` | — | UNKNOWN | — | No menu claims this run |

No SYSTEM_ESTIMATE without upstream observations. Ingredient SAR ≠ `food_cost_pct`. Capacity ≠ demand copy.

## 5. Final operating assumptions (RUF10)

| Key | Value | Provenance |
|---|---|---|
| location / budget / model / delivery | owner prefs | USER_PROVIDED |
| rent_monthly | 15000 (6667–36781) | SYSTEM_ESTIMATE / ai_estimated |
| store_area_m2 | ~669 | SYSTEM_ESTIMATE |
| operating_hours_day | 13.5 | SYSTEM_ESTIMATE |
| equipment_capex / other_capex | ~2532 / ~1296 | SYSTEM_ESTIMATE |
| avg_ticket / labor / covers / COGS% / fitout / seats / WC | UNKNOWN | UNKNOWN |

## 6–8. Financial model / LBH / budget

- Revenue still blocked while **daily_covers** UNKNOWN (hours alone insufficient; seats missing)
- Working capital: UNKNOWN (no full opex base)
- Budget vs 450k: **not** investment-grade while labor/fit-out/covers/COGS remain unknown
- Break-even / sensitivity: not commercially meaningful while covers blocked

## 9. Evidence coverage

- Competitors / location: VERIFIED (OSM)
- Numeric coverage: **PARTIAL** — rent, area, hours, component CAPEX; gaps ticket (this run), labor, COGS%, seats/covers, fitout, WC
- CAPACITY→DEMAND: seats missing → covers blocked (correct)

## 10. Runtime / model-path status

| Check | Result |
|---|---|
| Models / `invoke_llm` wiring | Configured |
| Commercial discovery | Wasalt rent path live after HTML-slice fix; Overpass via CH mirror fallback |
| Search | DDG challenged; Bing used (menu still flaky) |

## 11. Regression

- `tests/test_operating_economics_evidence.py`: **19 passed** (Wasalt fixture + oversized showroom exclusion + HTML-slice + OSM capacity bands)

## 12. Final PASS / PARTIAL / FAIL

**PARTIAL** — rent + hours retrieved with evidence provenance; full P&L still blocked on labor / COGS% / seats→covers / fit-out / WC. Ticket intermittent.

## 13. MERGE recommendation

**DO NOT MERGE** — owner review required. Do not treat DEFER/PARTIAL as Claude-Level Decision Usefulness PASS for investment-grade economics.

## REAL_USER_FLOW

### RUF10 (post HTML-slice rent fix)

- Study: `study_1fe42725a83c` / project `1215`
- Owner input only: concept, Olaya/Riyadh, SAR 450k, positioning; ops via AI estimates
- Artifacts: `/opt/cursor/artifacts/coffee-operating-economics-ruf10/`
- Wins: `rent_monthly`, `store_area_m2`, `operating_hours_day`, CAPEX components
- Gaps: ticket (0 menu claims), seats, covers, labor, food_cost_pct, fitout, WC

### Follow-ups queued

- RUF11+: re-run after ≤250 m² Wasalt filter + Overpass CH mirror; expect tighter rent/area bands; hours should remain if mirror works; seats still unlikely
