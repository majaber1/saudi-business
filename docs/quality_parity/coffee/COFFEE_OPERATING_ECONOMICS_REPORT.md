# Coffee Operating Economics — End-to-End Validation Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** `4d7d6ef12834afd07e8d79b49b2eb708a3eba7c4`  
**PR:** #56  
**Verdict: PARTIAL — DO NOT MERGE**

End-to-end proof from brand-new **REAL_USER_FLOW RUF15** (`study_ac43c9e296f1` / project `1221`, artifacts `/workspace/artifacts/coffee-operating-economics-ruf15/`).  
Owner inputs only: specialty coffee, Olaya/Riyadh, SAR 450k budget, positioning. Ops numbers are SYSTEM_ESTIMATE from retrieved evidence.

---

## 1. Required check results (RUF15)

| Field | Status | Value (L/B/H) | Provenance |
|---|---|---|---|
| Rent | **RETRIEVED** | 5,833 / 8,316 / 10,723 SAR/mo | SYSTEM_ESTIMATE — Wasalt commercial comps |
| Area | **RETRIEVED** | 41 / 70 / 125 m² | SYSTEM_ESTIMATE — Wasalt listing areas |
| Ticket | **RETRIEVED** | 22 / 30 / 40 SAR | SYSTEM_ESTIMATE — Explore-Saudi + Rimthan (+ hosts); **not** hardcoded 20/25/30 (60 menu observations) |
| Hours/day | **RETRIEVED** | 13.5 | SYSTEM_ESTIMATE — OSM `opening_hours` |
| Seats | **DERIVED** | 27.2 / 36.4 / 47.1 | Area × customer fraction ÷ Brave dining m²/seat — **CAPACITY** |
| Daily covers | **DERIVED (DEMAND)** | 172 / 221 / 270 | CAPACITY × utilization 35–55% (competition density=7). ≠ seats |
| Labor | **PARTIAL** | 36,000 / 36,000 / 36,136 SAR/mo | Role **headcount** from Shifty ratios × seats/hours; pay **pinned to WageIndicator SAR 4,000 floor** per role (Payscale medians ≤ floor) |
| COGS % | **RETRIEVED** | 30 / 32 / 40 % | SYSTEM_ESTIMATE — Square + 7shifts |
| Equipment CAPEX | **RETRIEVED** | 114 / 2,568 / 36,856 SAR | Amazon catalog package |
| Other CAPEX | **RETRIEVED** | 138 / 1,316 / 10,208 SAR | Amazon furniture/POS package |
| Fit-out CAPEX | **RETRIEVED** | 58,100 / 128,600 / 350,000 SAR | ArchSkills SAR/m² × area |
| Working capital | **DERIVED** | ~205,388 SAR | 2× fixed opex + 2× monthly COGS on complete opex set |

---

## 2. What changed since RUF13

| Gap | Fix |
|---|---|
| Ticket UNKNOWN | Multi-source menu seeds + HTML fallback when connector truncates text |
| Labor = single 4k floor | Shifty role headcount × role salaries (pay still floor-pinned when surveys ≤ min wage) |
| COGS / fit-out / seats UNKNOWN | Square/7shifts, ArchSkills, Brave density seeds |
| WC incomplete heuristic | Gate on complete opex; then policy WC |
| Staffing mis-tagged as salary | Persist `role_or_item`; recover explicit metric tokens (ignore `salary_labor` prefix) |

---

## 3. Evidence sources (RUF15)

| Source | Host | Used for |
|---|---|---|
| Wasalt | `wasalt.sa` | rent, area |
| Explore-Saudi / Rimthan | `explore-saudi.com`, `rimthancoffee.com` | menu → ticket |
| Payscale SA | `payscale.com` | role salaries |
| WageIndicator | `wageindicator.org` | statutory 4,000 floor |
| Shifty | `shifty-app.com` | FOH=30, BOH=0.35, mgr/shift=1 |
| Square / 7shifts | `squareup.com`, `7shifts.com` | food_cost_pct |
| ArchSkills | `archskills.com` | fit-out SAR/m² |
| Amazon | `amazon.sa` | equipment / other CAPEX |
| OSM | Overpass mirrors | hours/day |
| Brave | `bravecalculator.com` | dining_m2_per_seat |

Labor composition (from estimate reasoning): `store_manager×3 + head_barista×3 + barista×2 + cashier×1` at floor 4,000 each → 36,000 SAR/mo.

---

## 4. Financial model (RUF15) — provisional

| Output | Result | Caveat |
|---|---|---|
| Revenue Y1 | ~2.19M SAR | DEMAND covers × ticket — optimistic for specialty coffee |
| Costs Y1 | ~1.23M SAR | Labor may be understated vs true market manager/barista pay |
| CAPEX booked | ~132.5k | Fit-out dominates |
| Opening need | CAPEX+WC ≈ 338k vs 450k budget | Model surplus ~112k |
| NPV / IRR / payback | ~2.4M / 731% / 1.7 mo | **Not investment-grade** (optimistic demand + floor labor) |
| Risk / GO | **Unavailable** | Risk agent 429; no GO issued |

CAPACITY ≠ DEMAND is enforced (utilization band on seats×hours capacity).

---

## 5. Remaining blockers

1. Labor **pay** still floor-pinned — need Saudi café role surveys above 4,000 SAR.  
2. Covers are methodology DEMAND, not footfall — 221/day is aggressive.  
3. No GO/risk verdict this run.  
4. `/opt/cursor/artifacts` store mount EIO in this VM — artifacts under `/workspace/artifacts/coffee-operating-economics-ruf15/`.

---

## 6. Tests

`tests/test_operating_economics_evidence.py` — **29 passed**.

---

## 7. Merge recommendation

**DO NOT MERGE.** Material progress (ticket, COGS, fit-out, seats, WC, role-headcount labor) but **not FULL PASS** until labor compensation quality, demand credibility, and decision/risk gate are investment-grade.
