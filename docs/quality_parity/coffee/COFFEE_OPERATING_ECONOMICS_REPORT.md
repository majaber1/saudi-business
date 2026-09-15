# Coffee Operating Economics — End-to-End Validation Report

**Branch:** `cursor/coffee-operating-economics-1831`  
**Base:** `cursor/coffee-research-depth-parity-1831`  
**SHA:** `39b2e777b6f2637e985101e0a3a6d07a913dd95a`  
**PR:** #56  
**Verdict: PARTIAL — DO NOT MERGE**

Brand-new REAL_USER_FLOW **RUF15** (`study_ac43c9e296f1` / project `1221`).  
Artifacts: `/workspace/artifacts/coffee-operating-economics-ruf15/`.  
Owner inputs only: specialty coffee, Olaya/Riyadh, SAR 450k, positioning.

---

## 1. Required checks (RUF15)

| Field | Status | L / B / H | Provenance |
|---|---|---|---|
| Rent | RETRIEVED | 5833.33 / 8315.57 / 10723.1 SAR/mo | Wasalt commercial comps |
| Area | RETRIEVED | 41.17 / 70 / 124.5 m² | Wasalt listing areas |
| Ticket | RETRIEVED | 22 / 30 / 40 SAR | Explore-Saudi + Rimthan (+ hosts); 60 menu obs — **not** hardcoded 20/25/30 |
| Hours/day | RETRIEVED | 13.5 / 13.5 / 13.5 | OSM opening_hours |
| Seats | DERIVED (CAPACITY) | 27.2 / 36.4 / 47.1 | Area × customer fraction ÷ Brave m²/seat |
| Daily covers | DERIVED (DEMAND) | 171.99 / 221.13 / 270.27 | Capacity × 35–55% utilization — ≠ seats |
| Labor | PARTIAL | 36000 / 36000 / 36135.9 SAR/mo | Shifty role headcount × seats/hours; pay pinned to WageIndicator **4,000** floor/role |
| COGS % | RETRIEVED | 30 / 32 / 40 % | Square + 7shifts |
| Equipment | RETRIEVED | 114 / 2568 / 36856 SAR | Amazon package |
| Other CAPEX | RETRIEVED | 138 / 1316 / 10208 SAR | Amazon furniture/POS |
| Fit-out | RETRIEVED | 58100 / 128600 / 350000 SAR | ArchSkills SAR/m² × area |
| Working capital | DERIVED | 205388 SAR | 2× fixed opex + 2× monthly COGS (complete opex) |

Labor composition: store_manager×3 + head_barista×3 + barista×2 + cashier×1 @ floor 4,000 = 36,000 SAR/mo.

---

## 2. Fixes since RUF13

- Multi-source ticket/COGS/fit-out/density seeds + HTML fallback for truncated connector text  
- Round-robin seed budget so equipment/COGS are not starved  
- Role×staffing payroll path; preserve `role_or_item`; stop `salary_labor` prefix from reclassifying staffing metrics  
- WC gated on complete opex  

---

## 3. Financial snapshot (provisional)

| Output | Value | Caveat |
|---|---|---|
| CAPEX | 132484 SAR | Fit-out dominates |
| WC | 205388 SAR | Policy on complete opex |
| Opening vs 450k | SURPLUS (gap -112128) | Model surplus — not a GO |
| Revenue Y1 | 2189187 SAR | Optimistic DEMAND×ticket |
| NPV / IRR / payback | 2401559 / 731.3% / 1.7 months | Not investment-grade |
| Risk / GO | Unavailable | Risk agent 429 |

CAPACITY ≠ DEMAND enforced.

---

## 4. Blockers for FULL PASS

1. Labor **pay** floor-pinned (need café role surveys > 4,000 SAR).  
2. Covers are methodology DEMAND, not footfall — 221/day is aggressive.  
3. No risk/GO verdict this run.  

---

## 5. Tests

`tests/test_operating_economics_evidence.py` — **29 passed**.

---

## 6. Merge recommendation

**DO NOT MERGE.** Advanced but not investment-grade coffee operating economics.
