# Coffee Operating Economics Sprint — Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** _(see git log)_  
**DO NOT MERGE**

## Verdict: PARTIAL

Competitor/location depth remains accepted. This sprint added **scalable evidence-class commercial acquisition** and retrieved **component CAPEX SYSTEM_ESTIMATE bands** from vendor catalogs. Material rent / ticket / salary / COGS / covers remain **UNKNOWN** due to external retrieval blockers — not silent invention. Investment-grade quantitative study is still incomplete.

## 1. Branch / SHA

See latest commits on `cursor/coffee-operating-economics-1831`.

## 2. Sources added or enabled (evidence-class strategy — not coffee allowlist patches)

| Domain class | Example hosts | Used for |
|---|---|---|
| `real_estate_listing` | bayut.sa, propertyfinder.sa, aqar.fm, haraj.com.sa | commercial_rent |
| `job_salary` | bayt.com, indeed, linkedin | salary_labor |
| `delivery_marketplace` | hungerstation, jahez, keeta | menu_pricing |
| `equipment_vendor` | amazon.sa, ikea.com, jarir.com, extra.com, noon.com | equipment_capex |
| `fitout_vendor` | amazon/ikea/jarir/extra | furniture_pos_opening / fitout |
| `official_saudi` / `open_geo_encyclopedia` / `search_index` | GASTAT, MISA, OSM, Wikipedia, DDG, Bing | scaffolding |

Sector packs declare `evidence_classes`; allowlists resolve from domain classes. Seed catalog URLs fetch when search is challenged.

## 3. Exact numeric evidence retrieved (RUF `study_6fb9eda95b1c` / project `1210`)

| Metric | Observations | Sources |
|---|---|---|
| `equipment_item_sar` | 24 Amazon catalog prices | `amazon.sa` commercial espresso search |
| `opening_item_sar` | 20 Amazon POS/furniture prices | `amazon.sa` POS + furniture seeds |

**Not retrieved (blockers):**

| Class | Blocker |
|---|---|
| commercial_rent | bayut 503, propertyfinder 404/blocked, aqar 403 from this IP |
| menu_pricing | Hungerstation homepage has no menu SAR; delivery deep-links inaccessible |
| salary_labor | Bayt/Indeed 403 |
| fitout_capex | No sourced fit-out quotes reachable |
| food_cost_pct | No sourced COGS % in allowlisted pages |
| DuckDuckGo | Bot challenge (202) — Bing fallback used but organic quality poor for SAR rent/salary |

## 4. Estimate derivations (SYSTEM_ESTIMATE only)

| Key | LOW | BASE | HIGH | Derivation |
|---|---|---|---|---|
| `equipment_capex` | 2736 | 3634.5 | 9597 | Package: sum(3 cheapest) / 3×median / sum(3 dearest) from vendor observations |
| `other_capex` | 560 | 908 | (varies) | 4-item furniture/POS package from vendor observations |

No SYSTEM_ESTIMATE without upstream observations.

## 5. Final operating assumptions (RUF)

| Key | Value | Provenance |
|---|---|---|
| location_city / owner_budget / business_model / delivery | owner prefs | USER_PROVIDED |
| equipment_capex | 3634.5 (2736–9597) | SYSTEM_ESTIMATE |
| rent / ticket / labor / covers / COGS / fitout / seats / hours | UNKNOWN | UNKNOWN |

## 6–8. Financial model / LBH / budget

- CAPEX (equipment only): **~3.6k SAR** (incomplete vs full café build)
- Revenue Y1–Y3: **0** (blocked: ticket + covers UNKNOWN)
- Working capital: **0** (blocked: no opex base)
- Budget status vs 450k: **SURPLUS on incomplete CAPEX only** — **not** a claim that 450k funds a full Olaya café
- Break-even / sensitivity: not commercially meaningful while revenue blocked

## 9. Evidence coverage

- Competitors: VERIFIED (OSM); filter tightened so seed/observation docs are not mined as competitors
- Location: VERIFIED
- Numeric coverage after recovery: **PARTIAL** — present `equipment_capex`, `other_capex`; gaps ticket/rent/labor/COGS/fitout/covers/WC
- CAPACITY/DEMAND: blocked (seats + hours missing; correctly not fabricated)

## 10. Runtime / model-path status

| Check | Result |
|---|---|
| `GROQ_API_KEY` / models configured | Yes (`openai/gpt-oss-120b`, fast `20b`) |
| Wiring | Fixed: `invoke_llm`, `key`/`name` alias, compact evidence context |
| RUF failure mode | **ProviderUnavailableError** during assumptions: primary model **413 Request too large** (context overflow — mitigated by compact estimates), fallback **429 TPD rate limit**. Not a missing-config issue; not hidden behind categorical silence — recorded in `assumption_llm_status`. |

## 11. Regression

- `tests/test_operating_economics_evidence.py` + depth parity: **24+ passed**
- Broader coffee parity suite: previously 47 passed including new tests

## 12. Final PASS / PARTIAL / FAIL

**PARTIAL** — architecture for reusable commercial-evidence acquisition is in place and CAPEX component bands work; commercially useful full P&L (ticket/rent/labor/covers/COGS/fit-out) cannot be honestly completed from reachable sources in this environment.

## 13. MERGE recommendation

**DO NOT MERGE** — owner review required. Do not treat DEFER/PARTIAL as Claude-Level Decision Usefulness PASS for investment-grade economics.

## REAL_USER_FLOW

- Study: `study_6fb9eda95b1c` (also `study_da756ea910b2` earlier restart)
- Project: `1210`
- Owner input: concept + Olaya/Riyadh + SAR 450k + positioning only; operating fields via `ai_estimates`
- Artifacts: `/opt/cursor/artifacts/coffee-operating-economics-ruf1/`
