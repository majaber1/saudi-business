# Coffee Operating Economics — End-to-End Validation Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** `1e866b7`  
**PR:** #56  
**Verdict: PARTIAL — DO NOT MERGE**

This report is the end-to-end proof from a **brand-new REAL_USER_FLOW** after the labor-promotion fix (`study_3503f2d24a1f` / project `1218`, artifacts `/opt/cursor/artifacts/coffee-operating-economics-ruf13/`).

---

## 1. Required check results (RUF13)

| Field | Status | Value (L/B/H) | Provenance |
|---|---|---|---|
| Rent | **RETRIEVED** | 5,983 / 7,921 / 9,778 SAR/mo | SYSTEM_ESTIMATE — Wasalt ≤250 m² F&B filter |
| Ticket | **UNKNOWN** | — | Bing/menu follow returned 0 menu claims this run |
| Labor | **RETRIEVED (floor only)** | 4,000 / 4,000 / 4,000 SAR/mo | SYSTEM_ESTIMATE — WageIndicator Saudi private-sector statutory minimum wage |
| COGS % | **UNKNOWN** | — | No sourced food-cost % on allowlisted hosts |
| CAPEX (equipment) | **RETRIEVED** | 114 / 2,568 / 36,856 SAR | SYSTEM_ESTIMATE — Amazon catalog package |
| CAPEX (other/POS/furniture) | **RETRIEVED** | 138 / 1,396 / 10,208 SAR | SYSTEM_ESTIMATE — Amazon package |
| Fit-out CAPEX | **UNKNOWN** | — | No sourced fit-out quotes |
| Working capital | **PARTIAL / unreliable** | ~23,842 SAR | 2× months opex heuristic on **incomplete** opex (missing COGS; labor is floor-only) |
| Hours/day | **RETRIEVED** | 13.5 | SYSTEM_ESTIMATE — OSM `opening_hours` via Overpass mirror |
| Seats → covers | **UNKNOWN** | — | OSM seats/capacity tags absent; covers correctly blocked |

**Feature is NOT complete.** Revenue, break-even, and investment-grade budget sufficiency remain blocked.

---

## 2. Branch / SHA / changed files

**Tip SHA:** `1e866b7`

**This follow-up (post-RUF11):**
- `ai_engine/research/evidence/domain_classes.py` — WageIndicator host
- `ai_engine/research/evidence/evidence_classes.py` — min-wage seed + queries
- `ai_engine/research/evidence/adapters.py` — min-wage salary parse; SAR year-steal fix
- `ai_engine/research/evidence/observations.py` — emit metric id in statements
- `ai_engine/research/market/service.py` — do not remap salary SAR/month → rent
- `backend/app/integrations/sources/commercial_discovery.py` — mail.ru Overpass mirror
- `tests/test_operating_economics_evidence.py` — WageIndicator + remap regression
- `docs/quality_parity/coffee/COFFEE_OPERATING_ECONOMICS_REPORT.md` — this report

---

## 3. Evidence sources (RUF13)

| Source | Host | Used for |
|---|---|---|
| Wasalt commercial/showroom SSR | `wasalt.sa` | rent_monthly, store_area_m2 |
| WageIndicator statutory min wage | `wageindicator.org` | salary_monthly_sar → labor_monthly **floor** |
| Amazon vendor catalogs | `amazon.sa` | equipment_capex, other_capex, input_cost_sar (not COGS%) |
| OSM Overpass | `maps.mail.ru` / mirrors | operating_hours_day (seats still empty) |
| Bing / DDG | blocked / flaky | menu ticket (0 claims this run) |
| Bayt / Indeed | 403 | role salaries |

---

## 4. Extracted observations → SYSTEM_ESTIMATE

| Observation metric | n (approx) | Band key | L / B / H | Confidence |
|---|---|---|---|---|
| `rent_monthly_sar` / `rent_sar_per_m2_year` + area | ~64 | `rent_monthly` | 5983 / 7921 / 9778 | ~0.78 |
| `store_area_m2` | ~32 | `store_area_m2` | 36 / 63 / 79 | ~0.78 |
| `salary_monthly_sar` (statutory min wage) | ≥1 | `labor_monthly` | 4000 / 4000 / 4000 | ~0.65 (floor, not staffing model) |
| `equipment_item_sar` | ~120 | `equipment_capex` | 114 / 2568 / 36856 | ~0.69 |
| `opening_item_sar` | ~236 | `other_capex` | 138 / 1396 / 10208 | ~0.69 |
| OSM opening_hours | 2 | `operating_hours_day` | 13.5 | ~0.6 |

**Derivations (honest):**
- Labor = **statutory private-sector minimum wage**, single-role / unscaled — **not** a multi-barista café payroll.
- Ingredient catalog SAR is **not** promoted to `food_cost_pct`.
- Covers remain blocked without seats (hours alone insufficient).

---

## 5. Financial model (RUF13) — incomplete by design

| Output | Result | Why |
|---|---|---|
| Revenue Y1–Y3 | **0 / 0 / 0** | Blocked: ticket UNKNOWN and/or covers UNKNOWN |
| Costs Y1–Y3 | **0 / 0 / 0** | No full P&L without COGS + real labor + covers |
| CAPEX booked | ~3,964 | Equipment + other only; **fit-out = 0 (UNKNOWN)** |
| NPV | -3,964 | No operating cash inflows modeled |
| IRR / payback | **unavailable** | No sign-changing cash flows |
| Break-even months | **not calculable** | Revenue path blocked |
| Working capital | ~23.8k | 2× incomplete opex — **not investment-grade** |
| Budget vs 450k | spurious “SURPLUS” | Understates true need (fit-out/labor/COGS missing) |

### Low / Base / High scenarios

| Scenario | Revenue | OpEx | Result |
|---|---|---|---|
| Low | UNKNOWN | UNKNOWN | **Cannot publish** |
| Base | UNKNOWN | UNKNOWN | **Cannot publish** |
| High | UNKNOWN | UNKNOWN | **Cannot publish** |

### Break-even
**UNKNOWN** — not 18–26 months. Any such number would be invention.

### Budget sufficiency (450k)
**Cannot certify.** Partial known opening cash (~28k understated) vs 450k looks “surplus” only because fit-out, true labor, COGS, and WC are missing. Correct statement: **450k feasibility UNKNOWN pending fit-out + staffing + covers + COGS.**

### Main risks (evidence-aligned)
1. **Rent + utilization** (covers/seats still unknown)  
2. **Labor understated** (only statutory floor, not café headcount)  
3. **Fit-out gap** (often the largest CAPEX line)  
4. **COGS % unknown**  
5. **Ticket retrieval flaky** (search/bot blockers)

---

## 6. Exact retrieval blockers (remaining UNKNOWN)

| Gap | Exact blocker |
|---|---|
| `avg_ticket` | DDG bot challenge; Bing from this IP returns weak/empty menu follows this run |
| `daily_covers` | Requires seats (+ hours). OSM seats/capacity tags = 0 near Olaya; capacity→covers correctly refused |
| `food_cost_pct` | No allowlisted page with sourced F&B COGS %; Amazon inputs stay `input_cost_sar` only |
| `fitout_capex` | No reachable fit-out SAR/m² or package quotes on allowlisted hosts |
| Full `labor_monthly` | Bayt/Indeed 403; only statutory min wage reachable — not role survey / headcount |
| Investment 420–580k card | Would require inventing fit-out + WC + payroll — **forbidden** |

---

## 7. Tests

`tests/test_operating_economics_evidence.py` — **22 passed** (Wasalt footprint, WageIndicator min-wage, salary↛rent remap, HTML slice, OSM capacity bands).

---

## 8. MERGE recommendation

### DO NOT MERGE

Reason: end-to-end study still cannot produce investment-grade revenue, break-even, or budget sufficiency. Closing rent + labor-floor + hours + component CAPEX is progress, but the product must not present a complete café feasibility card while ticket/covers/COGS/fit-out remain UNKNOWN.

**Do not treat DEFER/PARTIAL as Claude-Level Decision Usefulness PASS.**

---

## REAL_USER_FLOW log

| Run | Study | Wins | Gaps |
|---|---|---|---|
| RUF11 | `study_64691360abd8` | café-plausible rent/area; ticket; CAPEX | labor not promoted; hours flaky |
| RUF12 | `study_70025a81ed9e` | rent; CAPEX; WageIndicator fetched but remapped to rent | labor UNKNOWN (bug) |
| **RUF13** | **`study_3503f2d24a1f`** | **rent; labor floor 4000; hours 13.5; CAPEX** | **ticket; seats/covers; COGS%; fit-out; full payroll** |

Artifacts: `/opt/cursor/artifacts/coffee-operating-economics-ruf13/`
