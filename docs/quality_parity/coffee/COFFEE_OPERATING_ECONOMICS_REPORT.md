# Coffee Operating Economics — End-to-End Validation Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** `4bbc301c746dfb30c44ca9cd708f17e23a9cb9cf`  
**PR:** #56  
**Verdict: PARTIAL — DO NOT MERGE**

End-to-end proof from brand-new **REAL_USER_FLOW RUF15** (`study_ac43c9e296f1` / project `1221`, artifacts `/workspace/artifacts/coffee-operating-economics-ruf15/`).  
Owner inputs only: specialty coffee, Olaya/Riyadh, SAR 450k budget, positioning. Ops numbers are SYSTEM_ESTIMATE from retrieved evidence.

---

## 1. Required check results (RUF15)

| Field | Status | Value (L/B/H) | Provenance |
|---|---|---|---|
| Rent | **RETRIEVED** | 5,833 / 8,316 / 10,723 SAR/mo | SYSTEM_ESTIMATE — Wasalt ≤250 m² F&B filter |
| Area | **RETRIEVED** | 41 / 70 / 125 m² | SYSTEM_ESTIMATE — Wasalt listing areas |
| Ticket | **RETRIEVED** | 22 / 30 / 40 SAR | SYSTEM_ESTIMATE — Explore-Saudi + Rimthan (+ other menu hosts); **not** hardcoded 20/25/30 |
| Hours/day | **RETRIEVED** | 13.5 | SYSTEM_ESTIMATE — OSM `opening_hours` |
| Seats | **DERIVED** | 27 / 36 / 47 | Area × customer fraction ÷ Brave dining m²/seat — **CAPACITY**, not demand |
| Daily covers | **DERIVED (DEMAND)** | 172 / 221 / 270 | CAPACITY × utilization 35–55% (competition density=7). Distinct from seats |
| Labor | **PARTIAL** | 36,000 / 36,000 / 36,136 SAR/mo | Role **headcount** from Shifty FOH/BOH/mgr ratios × seats/hours; pay levels **pinned to WageIndicator SAR 4,000 floor** (Payscale role medians ≤ floor for most roles) |
| COGS % | **RETRIEVED** | 30 / 32 / 40 % | SYSTEM_ESTIMATE — Square + 7shifts food-cost benchmarks |
| Equipment CAPEX | **RETRIEVED** | 114 / 2,568 / 36,856 SAR | Amazon catalog package |
| Other CAPEX | **RETRIEVED** | 138 / 1,316 / 10,208 SAR | Amazon furniture/POS package |
| Fit-out CAPEX | **RETRIEVED** | 58,100 / 128,600 / 350,000 SAR | ArchSkills SAR/m² × area + totals |
| Working capital | **DERIVED** | ~205,388 SAR | Policy 2× fixed opex + 2× monthly COGS on **complete** opex (ticket/covers/labor/COGS/rent present; labor is role-headcount not single-floor) |

---

## 2. What changed since RUF13

| Gap | Fix |
|---|---|
| Ticket UNKNOWN | Multi-source menu seeds (Explore-Saudi, Rimthan, DrCafe) + HTML fallback when connector truncates text |
| Labor = 4k floor only | Payscale/Talent role salaries + Shifty staffing ratios → role headcount payroll (pay still floor-pinned when survey medians ≤ statutory min) |
| COGS UNKNOWN | Square/7shifts food-cost % seeds |
| Fit-out UNKNOWN | ArchSkills Riyadh SAR/m² seeds |
| Seats/covers UNKNOWN | Brave density → seats from area; demand ≠ capacity |
| WC incomplete heuristic | Gate requires complete opex; then 2× fixed + 2× COGS |
| Staffing mis-tagged as salary | Preserve `role_or_item`; do not match `salary_labor` prefix when recovering metrics |

**Tip SHA:** `4bbc301c746dfb30c44ca9cd708f17e23a9cb9cf`

---

## 3. Evidence sources (RUF15)

| Source | Host | Used for |
|---|---|---|
| Wasalt commercial SSR | `wasalt.sa` | rent_monthly, store_area_m2 |
| Explore-Saudi / Rimthan | `explore-saudi.com`, `rimthancoffee.com` | menu_item_sar → avg_ticket |
| Payscale SA jobs | `payscale.com` | role salary_monthly_sar |
| WageIndicator | `wageindicator.org` | statutory floor 4,000 SAR/mo |
| Shifty staffing calculator | `shifty-app.com` | FOH guests/staff=30, BOH=0.35, mgr/shift=1 |
| Square / 7shifts | `squareup.com`, `7shifts.com` | food_cost_pct |
| ArchSkills | `archskills.com` | fitout_sar_per_m2 / totals |
| Amazon | `amazon.sa` | equipment / other CAPEX |
| OSM Overpass | mirrors | operating_hours_day |
| Brave Calculator | `bravecalculator.com` | dining_m2_per_seat |

---

## 4. Financial model (RUF15) — provisional

| Output | Result | Caveat |
|---|---|---|
| Revenue Y1 | ~2.19M SAR | Driven by DEMAND covers (221/day) × ticket 30 — **optimistic vs specialty-coffee reality**; validate with primary footfall |
| Costs Y1 | ~1.23M SAR | Labor understated if true manager/barista market pay ≫ statutory floor |
| CAPEX | ~132k (equip+fitout+other) | Fit-out dominates |
| Opening need | CAPEX + WC ≈ 338k vs budget 450k | Model says surplus ~112k |
| NPV / IRR / payback | ~2.4M / 731% / 1.7 mo | **Not investment-grade** — demand utilization + floor-pinned labor inflate returns |
| Risk / GO decision | **Unavailable** | Risk agent rate-limited (429); no GO/GO_WITH_CONDITIONS issued |

### CAPACITY ≠ DEMAND
- Capacity ≈ seats×hours path before utilization (~444 covers/day capacity estimate in payload).
- Demand = capacity × 35–55% utilization → 172/221/270. Correctly separated.

---

## 5. Remaining blockers (honest)

1. **Labor pay levels** still collapse to statutory 4,000 SAR/role after floor — need stronger Saudi café role surveys above the floor (Talent outliers filtered; Payscale SA medians low).
2. **Demand/covers** are methodology estimates, not footfall sensors — specialty coffee at 221 covers/day is aggressive.
3. **No owner GO gate** — risk model failed this run; do not treat surplus/IRR as a pass.
4. Artifact store mount (`/opt/cursor/artifacts`) is broken in this VM (EIO); evidence kept under `/workspace/artifacts/coffee-operating-economics-ruf15/`.

---

## 6. Tests

`tests/test_operating_economics_evidence.py` — **29 passed** (includes staffing-metric recovery regression).

---

## 7. Merge recommendation

**DO NOT MERGE.** Feature is materially advanced (ticket/COGS/fit-out/seats/WC/role-headcount labor) but **not FULL PASS**: labor compensation quality, demand credibility, and decision/risk gate remain insufficient for investment-grade coffee operating economics.
