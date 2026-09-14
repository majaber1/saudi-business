# Coffee Research Depth Parity — Implementation Report

**Branch:** `cursor/coffee-research-depth-parity-1831`  
**Acceptance study:** `study_4084c78b17fe` / project `1205`  
**Classification:** REAL_USER_FLOW (empty/new project)  
**DO NOT MERGE** until owner review.

## Final parity (honest)

| Dimension | Result | Notes |
|---|---|---|
| Claude-Level Coverage | **PASS** | 10 VERIFIED Olaya/Riyadh competitors + location density + district wiki context + GASTAT/MISA |
| Claude-Level Decision Usefulness | **PASS** | Verdict `DEFER` with actionable next steps; UNKNOWN ops do not collapse into a shallow empty report |
| Investment-Grade Study | **PARTIAL** | Competitors + location present, but critical numeric ops (rent/ticket/labor/covers/COGS/CAPEX) remain UNKNOWN without sourced numeric SYSTEM_ESTIMATE bands |

## What closed

1. **Multi-source commercial discovery** via existing `SourceConnector` (`commercial_discovery`): Nominatim POIs, Wikipedia district/city, Overpass density (best-effort), DuckDuckGo HTML multi-query, documented exhaustion log.
2. **LOCATION** research type + location-economics extractor (density + district context).
3. **SYSTEM_ESTIMATE** synthesizer that only emits values from sourced numerics near keywords (no invention).
4. **Incomplete-evidence synthesis** distinguishing VERIFIED / SYSTEM_ESTIMATE / USER_ASSUMPTION / UNKNOWN.
5. **Geography wiring** from `location_city` structured answers into market/gap planners.
6. Always live-fetch commercial discovery (knowledge hits no longer skip depth).

## REAL_USER_FLOW evidence (ruf3)

- Email: new user `coffee_depth3_*@example.com`
- Study: `study_4084c78b17fe`
- Claims: 37; Competitors: 10 VERIFIED in Riyadh/Olaya (Starbucks, Urth Caffe, Gloria Jeans, Coffee Day, LAS Cafe, Foam, Lucky Cafe, …) with OSM URLs + relevance
- Location: competition_density ≈ 11 Nominatim POIs; Olaya + Riyadh Wikipedia context
- Operating estimates: none (correct — no allowlisted sourced rent/ticket/labor figures)
- Assumptions: owner `location_city` + `owner_budget`; critical F&B ops UNKNOWN
- Financials: revenue Y1–Y3 = 0, CAPEX/WC = 0, budget SURPLUS — blocked on UNKNOWN (internally consistent)
- Verdict: `DEFER` with conditions to collect rent/ticket/CAPEX primary quotes
- Persistence: refresh + logout/login PASS

Artifacts: `/opt/cursor/artifacts/coffee-research-depth-ruf3/`

## Remaining blockers (exact)

1. **No sourced numeric rent / ticket / labor / CAPEX** from allowlisted commercial pages → cannot emit defensible SYSTEM_ESTIMATE bands → Investment-Grade stays PARTIAL.
2. DuckDuckGo HTML results rarely yield followable allowlisted pages with SAR operating figures.
3. LLM assumption path unavailable in this environment → categorical rule fallbacks only for non-numeric fields.
4. Wikipedia location cards occasionally tagged as `commercial_rent_signal` PARTIAL without numbers (cosmetic classifier noise).

## Regression

- `tests/test_research_depth_parity.py` + `tests/test_coffee_quality_parity.py` → **36 passed**

## MERGE recommendation

**DO NOT MERGE** — owner review required. Product progress is real on competitors + location depth, but Investment-Grade numeric operating evidence is still incomplete.
