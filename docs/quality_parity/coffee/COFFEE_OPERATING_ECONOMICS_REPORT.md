# Coffee Operating Economics Sprint — Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** `ee7bee343d2b610ece23577db6235fe35d9b87e3`  
**DO NOT MERGE**

## Verdict: PARTIAL

Competitor/location depth remains accepted. This sprint added **scalable evidence-class commercial acquisition** and now retrieves:

- Component CAPEX `SYSTEM_ESTIMATE` bands from vendor catalogs
- **Menu / average ticket `SYSTEM_ESTIMATE`** from discovered brand/venue menu pages (Bing follow + local brand host session-merge)

Material rent / salary / COGS% / covers / fit-out / working capital remain **UNKNOWN** due to external retrieval blockers — not silent invention. Investment-grade quantitative study is still incomplete.

## 1. Branch / SHA

See latest commits on `cursor/coffee-operating-economics-1831`.

## 2. Sources added or enabled (evidence-class strategy — not coffee allowlist patches)

| Domain class | Example hosts | Used for |
|---|---|---|
| `real_estate_listing` | bayut.sa, propertyfinder.sa, aqar.fm, haraj.com.sa | commercial_rent |
| `job_salary` | bayt.com, indeed, linkedin | salary_labor |
| `delivery_marketplace` | hungerstation, jahez, keeta | menu_pricing |
| `local_brand_website` | *(no static list — OSM website tags + search discovery)* | menu_pricing |
| `equipment_vendor` | amazon.sa, ikea.com, jarir.com, extra.com, noon.com | equipment_capex / cogs input catalogs |
| `fitout_vendor` | amazon/ikea/jarir/extra | furniture_pos_opening / fitout |
| `official_saudi` / `open_geo_encyclopedia` / `search_index` | GASTAT, MISA, OSM, Wikipedia, DDG, Bing | scaffolding |

Sector packs declare `evidence_classes`; allowlists resolve from domain classes. Seed catalog URLs fetch when search is challenged. Discovered brand hosts are session-merged when `local_brand_website` is opted in.

### Search follow-up fixes (this iteration)

- DDG remains bot-challenged (202) from this environment
- Bing fallback prioritizes menu/rent/salary queries, unwraps `/ck` redirect URLs, and follows discovered brand menu pages
- Owner concept **blurbs** are no longer injected into Bing queries (mapped to amenity tokens like `cafe`) so searches do not collapse to irrelevant “FNB bank” hits

## 3. Exact numeric evidence retrieved (RUF `study_4700e3dfb62b` / project `1213`)

| Metric | Observations | Sources |
|---|---|---|
| `equipment_item_sar` | Amazon catalog prices | `amazon.sa` commercial espresso search |
| `opening_item_sar` | Amazon POS/furniture prices | `amazon.sa` POS + furniture seeds |
| `menu_item_sar` | Brand/venue menu page prices | Discovered menu URLs via Bing (e.g. cafe brand / menu pages) |
| `input_cost_sar` | Ingredient catalog prices | `amazon.sa` milk/beans seeds (**not** promoted to food_cost_pct) |

**Not retrieved (blockers):**

| Class | Blocker |
|---|---|
| commercial_rent | bayut 503, propertyfinder/aqar blocked from this IP; Haraj JS-thin |
| salary_labor | Bayt/Indeed 403 |
| fitout_capex | No sourced fit-out quotes reachable |
| food_cost_pct | No sourced COGS %; ingredient SAR kept as input_cost only |
| daily_covers / capacity | seats + hours still UNKNOWN — demand correctly not fabricated |
| DuckDuckGo | Bot challenge (202) — Bing fallback used |

## 4. Estimate derivations (SYSTEM_ESTIMATE only)

| Key | LOW | BASE | HIGH | Derivation |
|---|---|---|---|---|
| `avg_ticket` | 55 | 70 | 85 | Menu-item observations → ticket band (SYSTEM_ESTIMATE) |
| `equipment_capex` | 129 | 2229 | 7839 | Package from vendor catalog observations |
| `other_capex` | 138 | 686 | 6752 | Furniture/POS package from vendor observations |

No SYSTEM_ESTIMATE without upstream observations. Ingredient catalog prices do **not** become `food_cost_pct`.

## 5. Final operating assumptions (RUF)

| Key | Value | Provenance |
|---|---|---|
| location_city / owner_budget / business_model / delivery | owner prefs | USER_PROVIDED |
| avg_ticket | 70 (55–85) | SYSTEM_ESTIMATE / ai_estimated |
| equipment_capex | ~2229 | SYSTEM_ESTIMATE |
| other_capex | ~686 | SYSTEM_ESTIMATE |
| rent / labor / covers / COGS% / fitout / seats / hours | UNKNOWN | UNKNOWN |

## 6–8. Financial model / LBH / budget

- CAPEX (equipment + other components only): incomplete vs full café build
- Revenue: still blocked while **daily_covers** UNKNOWN (ticket alone is insufficient)
- Working capital: 0 / UNKNOWN (no full opex base)
- Budget vs 450k: **not** an investment-grade funding claim while rent/labor/fit-out/covers remain unknown
- Break-even / sensitivity: not commercially meaningful while covers blocked

## 9. Evidence coverage

- Competitors: VERIFIED (OSM)
- Location: VERIFIED
- Numeric coverage after recovery: **PARTIAL** — present `avg_ticket`, `equipment_capex`, `other_capex`; gaps rent/labor/COGS%/fitout/covers/WC
- CAPACITY/DEMAND: blocked (seats + hours missing; correctly not fabricated)

## 10. Runtime / model-path status

| Check | Result |
|---|---|
| `GROQ_API_KEY` / models configured | Yes |
| Wiring | `invoke_llm`, key/name alias, compact evidence context |
| Commercial discovery | Bing menu follow + brand host merge operational; DDG challenged |

## 11. Regression

- `tests/test_operating_economics_evidence.py`: **15 passed**

## 12. Final PASS / PARTIAL / FAIL

**PARTIAL** — reusable commercial-evidence acquisition now yields ticket + component CAPEX bands; full P&L still blocked on rent/labor/covers/COGS%/fit-out.

## 13. MERGE recommendation

**DO NOT MERGE** — owner review required. Do not treat DEFER/PARTIAL as Claude-Level Decision Usefulness PASS for investment-grade economics.

## REAL_USER_FLOW

- Study: `study_4700e3dfb62b`
- Project: `1213`
- Owner input: concept + Olaya/Riyadh + SAR 450k + positioning only; operating fields via `ai_estimates`
- Artifacts: `/opt/cursor/artifacts/coffee-operating-economics-ruf8/`
