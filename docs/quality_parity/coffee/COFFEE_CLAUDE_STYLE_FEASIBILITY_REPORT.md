# Riyadh Specialty Coffee — Feasibility Study

**Product:** Saudi Business  
**Study ID:** `study_d4ff0d3d5c7b`  
**Project ID:** `1202`  
**Classification:** REAL_USER_FLOW  
**Currency:** SAR  
**As of:** 2026-09-14  

**Final verdict:** `INSUFFICIENT_EVIDENCE`

> This report follows the **same decision-section structure** as a Claude-style investment feasibility pack.  
> It is built **only** from Saudi Business study outputs for this run.  
> **No Claude numbers, competitors, CAPEX, OPEX, margins, or verdict were copied.**

---

## 1. Executive Summary

The owner proposes a **premium specialty coffee shop** in **Riyadh, Saudi Arabia**, with an available budget of **SAR 450,000**, serving specialty coffee, cold beverages, light desserts, and takeaway to young professionals, university students, office workers, and nearby residents.

Saudi Business completed the governed study path (profile → discovery → research → assumptions → financials → decision → report). Decision safety behaved correctly: the system **did not issue an unsupported GO**.

| Question | Answer from this study |
|---|---|
| Is SAR 450k enough? | **Cannot confirm.** CAPEX / WC components are UNKNOWN, so funding requirement is incomplete. Budget status vs computed total funding is not investment-grade. |
| Plausible café configuration? | **Not yet.** Seats, hours, area, ticket, and covers are UNKNOWN. |
| Rent / staffing / CAPEX? | **UNKNOWN** — not fabricated. |
| Competitors / pricing? | **NOT_FOUND** in sourced evidence for this run. |
| Break-even / NPV / IRR / payback? | Revenue blocked → NPV/IRR/payback **not decision-grade**. |
| What next? | Close evidence gaps below before any GO / GO_WITH_CONDITIONS. |

**Bottom line:** Macro Saudi context is partially available (GASTAT). Operating economics, competitors, location rent, and component CAPEX are **not** yet evidenced. Verdict remains **INSUFFICIENT_EVIDENCE**.

---

## 2. Project Profile

| Field | Value | Provenance |
|---|---|---|
| Concept | Premium specialty coffee shop | USER_PROVIDED |
| City | Riyadh, Saudi Arabia | USER_PROVIDED |
| Format | Physical café / specialty coffee | USER_PROVIDED |
| Offer | Specialty coffee, cold beverages, light desserts, takeaway | USER_PROVIDED |
| Target customers | Young professionals, university students, office workers, nearby residents | USER_PROVIDED |
| Owner budget | SAR 450,000 | USER_PROVIDED |
| Exact district | Not provided | GAP |
| Store area (m²) | UNKNOWN | UNKNOWN |
| Seats | UNKNOWN | UNKNOWN |

---

## 3. Market Analysis

### 3.1 Macro context (evidence-backed)

Saudi Business retrieved official macro signals. These support **macro environment**, not café unit economics.

| Signal | Value | Source | Directly supports café ticket/rent/orders? |
|---|---|---|---|
| CPI inflation | ~1.8–1.9% (Mar 2026) | GASTAT | **No** |
| GDP / economy growth | Q1 2026 growth cited (~3.0%) | GASTAT | **No** |
| Wholesale & retail operating revenues index | +3.2% (Q2 2026) | GASTAT | **Weak / indirect only** |

**Principle applied:** Macro evidence ≠ operating evidence.

### 3.2 Sector / specialty coffee context

| Item | Status |
|---|---|
| Saudi/GCC specialty coffee market sizing | **Not evidenced in this run** |
| Riyadh café demand elasticity | **Not evidenced** |
| Delivery vs dine-in mix for specialty coffee | System estimate only: Partial (<30%) delivery dependency |

### 3.3 Local commercial evidence

| Item | Status |
|---|---|
| District footfall | GAP — district unknown |
| High-street vs secondary rent | GAP |
| Nearby office/university catchment | Qualitative owner intent only |

---

## 4. Saudi / Riyadh Context

**What is known**
- Project geography: Riyadh, KSA
- Official statistics connectors returned GASTAT macro claims
- Regulatory placeholders noted (ZATCA tax/e-invoicing, municipal licensing relevance) but **not fully live-validated** as café-specific licensing packs in this run

**What is not known**
- Exact municipality / district licensing path for this site
- Site-specific Balady / commercial license timeline
- Fit-out permit lead times for the chosen unit

---

## 5. Competitor Analysis

| Status | Detail |
|---|---|
| Sourced competitors | **NOT_FOUND** |
| Fabricated competitors | **None** (correct safety behavior) |
| Pricing from competitor menus | **NOT_FOUND** |
| Positioning map | Cannot be drawn without primary evidence |

**Implication:** Without competitor and pricing evidence, average ticket and differentiation claims cannot support a strong GO.

---

## 6. Customer / Positioning

| Segment | Owner intent | Evidence depth |
|---|---|---|
| Young professionals | Yes | Intent only |
| University students | Yes | Intent only |
| Office workers | Yes | Intent only |
| Nearby residents | Yes | Intent only |

**Positioning hypothesis (unvalidated):** Premium specialty coffee + light desserts + takeaway in Riyadh.  
**Status:** Hypothesis only — not evidence-backed.

---

## 7. Operating Model

Required café operating model (architecture-supported):

| Block | Required inputs | This study |
|---|---|---|
| Store | area, seats, hours/day, days/year | seats / hours = **UNKNOWN** |
| Demand | daily covers, ramp, avg ticket | covers / ticket = **UNKNOWN** |
| Staffing | roles, HC, salaries | labor monthly = **UNKNOWN** |
| Direct cost | beverage/food COGS % | food_cost_pct = **UNKNOWN** |
| Delivery | dependency | Partial (<30%) — SYSTEM_ESTIMATE |
| Fixed OPEX | rent, utilities, marketing, etc. | rent = **UNKNOWN** |

**Revenue identity (governed):**

```
Daily revenue   = daily_covers × avg_ticket
Annual revenue  = daily_covers × avg_ticket × operating_days
```

Because `daily_covers` and `avg_ticket` are UNKNOWN, **revenue is blocked** (not zero as a business claim — blocked as incomplete).

---

## 8. Key Assumptions

| Assumption | Value | Unit | Provenance | Decision impact |
|---|---|---|---|---|
| Owner budget | 450,000 | SAR | USER_PROVIDED | Hard funding constraint |
| Location city | Riyadh, Saudi Arabia | text | USER_PROVIDED | Geography |
| Business model | Café / specialty coffee | categorical | USER_PROVIDED | Operating model |
| Seats capacity | UNKNOWN | seats | UNKNOWN | Demand / labor / fit-out |
| Operating hours / day | UNKNOWN | hours/day | UNKNOWN | Capacity |
| Average ticket | UNKNOWN | SAR/txn | UNKNOWN | Revenue |
| Daily covers | UNKNOWN | txn/day | UNKNOWN | Revenue |
| Monthly rent | UNKNOWN | SAR/month | UNKNOWN | OPEX / break-even |
| Monthly labor | UNKNOWN | SAR/month | UNKNOWN | OPEX |
| Food / beverage cost % | UNKNOWN | % | UNKNOWN | COGS / margin |
| Delivery dependency | Partial (<30%) | categorical | SYSTEM_ESTIMATE | Channel mix |
| Fit-out CAPEX | UNKNOWN | SAR | UNKNOWN | Initial funding |

**Placeholder check:** No generic `10000` sentinel values survived.

---

## 9. Staffing Model

| Role | Headcount | Monthly salary (SAR) | Evidence |
|---|---|---|---|
| Store manager | UNKNOWN | UNKNOWN | Not evidenced |
| Head / senior barista | UNKNOWN | UNKNOWN | Not evidenced |
| Barista(s) | UNKNOWN | UNKNOWN | Not evidenced |
| Support / cashier | UNKNOWN | UNKNOWN | Not evidenced |
| **Monthly labor total** | — | **UNKNOWN** | — |

---

## 10. CAPEX (component-based)

| Component | Amount (SAR) | Status |
|---|---|---|
| Coffee equipment | 0.0 (unresolved) | UNKNOWN / not evidenced |
| Fit-out | 0.0 (unresolved) | UNKNOWN / not evidenced |
| Furniture / other | 0.0 (unresolved) | UNKNOWN / not evidenced |
| POS / technology | not separated | GAP |
| Deposits / licenses / opening | not separated | GAP |
| Initial inventory | not separated | GAP |
| Contingency | not modeled | GAP |
| **Total CAPEX** | **0.0 computed** | **Incomplete — not a claim that CAPEX is zero** |

Extract notes: `fnb_capex_missing_or_unknown`.

---

## 11. OPEX

| Line | Monthly | Annual | Status |
|---|---|---|---|
| Rent | UNKNOWN | UNKNOWN | Blocks OPEX |
| Labor | UNKNOWN | UNKNOWN | Blocks OPEX |
| Utilities | not set | — | GAP |
| Marketing | not set | — | GAP |
| Maintenance / software / licenses | not set | — | GAP |
| Delivery fees | depends on dependency | — | Partial estimate only |

---

## 12. Revenue Model

| Driver | Value | Status |
|---|---|---|
| Avg ticket | UNKNOWN | Blocks revenue |
| Daily covers | UNKNOWN | Blocks revenue |
| Operating days / year | not confirmed | Default path unused because ticket/covers blocked |
| Y1 / Y2 / Y3 revenue | 0.0 displayed | **Blocked incomplete**, not a business forecast |

Extract note: `fnb_revenue_blocked_missing_or_unknown_ticket_or_covers`.

---

## 13. Financial Forecast

| Metric | Y1 | Y2 | Y3 | Status |
|---|---|---|---|---|
| Revenue | 0.0* | 0.0* | 0.0* | Blocked |
| COGS | n/a | n/a | n/a | Blocked |
| Gross profit | n/a | n/a | n/a | Blocked |
| OPEX | n/a | n/a | n/a | Blocked |
| EBITDA | n/a | n/a | n/a | Blocked |

\* Displayed zeros reflect incomplete inputs, not a validated no-revenue business case.

Discount rate used by engine when computable: 12% (standard path). Not meaningful until cash flows exist.

---

## 14. Break-even

| Metric | Result |
|---|---|
| Break-even months | Not mathematically supportable |
| Reason | Missing ticket, covers, rent, labor, COGS |

---

## 15. Cash Flow

| Period | Cash flow (SAR) |
|---|---|
| t0 (initial) | Incomplete (CAPEX/WC UNKNOWN) |
| Y1–Y3 | Not decision-grade |

---

## 16. NPV / IRR / Payback

| Metric | Result | Validity |
|---|---|---|
| NPV | 0.0 (incomplete path) | **Not investment-grade** |
| IRR | Unavailable | Correct — no valid sign-change cash flows |
| Payback | Unavailable | Correct — cumulative CF does not cross zero on a real forecast |

Trust gates: no silent currency mixing; incomplete extract flagged.

---

## 17. Budget Sufficiency (SAR 450,000)

| Item | Value |
|---|---|
| Owner budget | SAR 450,000 |
| Computed CAPEX | Incomplete (0.0 unresolved) |
| Computed working capital | Incomplete (0.0 unresolved) |
| Total initial funding (computed) | Incomplete |
| Budget status (engine) | SURPLUS vs incomplete total |
| **Investment interpretation** | **Do not treat as “450k is enough.”** Until CAPEX+WC are evidenced, sufficiency is **unknown**. |

Hard rule preserved: system must **not** shrink realistic costs to fit the budget once costs are known.

---

## 18. Regulatory / Licensing

| Topic | Status |
|---|---|
| Commercial registration / MoC | Relevant — not site-validated |
| Municipal / Balady food premises | Relevant — district unknown |
| ZATCA VAT / e-invoicing | Flagged as likely applicable |
| Food safety / municipality health | Required for café — timeline UNKNOWN |

---

## 19. Risks

Derived from this project’s gaps (not hardcoded Claude risks):

1. **Location / site risk** — district unresolved; rent and demand unknown  
2. **Demand ramp risk** — covers/ticket unknown  
3. **Competition risk** — no sourced competitor set  
4. **Staffing / barista risk** — labor model unknown  
5. **Budget / funding risk** — CAPEX+WC incomplete vs SAR 450k constraint  
6. **Working capital risk** — WC not evidenced  
7. **Licensing / execution risk** — timeline and site approvals unknown  
8. **Evidence risk** — macro data over-weighted vs operating evidence  

---

## 20. Evidence Register

| # | Claim (summary) | Source | Type | Geography | Supports operating assumption? |
|---|---|---|---|---|---|
| 1 | CPI inflation ~1.8–1.9% Mar 2026 | GASTAT | Official | KSA | No (macro only) |
| 2 | Economy / GDP growth Q1 2026 | GASTAT | Official | KSA | No |
| 3 | Wholesale & retail operating revenues +3.2% Q2 2026 | GASTAT | Official | KSA | Indirect only |
| 4 | Competitor set | — | — | Riyadh | **NOT_FOUND** |
| 5 | Pricing / menu evidence | — | — | Riyadh | **NOT_FOUND** |

---

## 21. Evidence Gaps

High-impact gaps blocking investment-grade GO:

1. Riyadh competitor primary evidence (names, sites, pricing)  
2. District / rent / m² location economics  
3. Average ticket evidence (specialty coffee / café)  
4. Daily transaction / demand evidence  
5. Staffing salaries (barista / manager)  
6. Equipment supplier quotes (espresso, grinders, refrigeration, POS)  
7. Fit-out SAR basis (scope, m², geography)  
8. Working capital / opening inventory basis  
9. Licensing timeline for chosen site  

---

## 22. Contradiction Check

| Check | Result |
|---|---|
| Placeholder 10000 vs physical limits | **PASS** — no placeholders |
| Hours > 24 | **PASS** — hours UNKNOWN, not absurd |
| Budget silently forced to equal CAPEX | **PASS** — owner budget not used as CAPEX |
| Macro GDP used as ticket proof | **Rejected by report logic** |
| Unsupported strong GO | **Blocked** → INSUFFICIENT_EVIDENCE |
| Numeric evidence vs assumptions | No comparable operating contradictions because operating values are UNKNOWN |

---

## 23. Owner Questions (material only)

Answer these to unlock a decision-grade model:

1. **Which Riyadh district / street type** (premium high-street vs secondary / mixed use)?  
2. **Target store size (m²)** and seating preference?  
3. **Expected opening hours** and days/week?  
4. Any **hard constraints** on delivery vs dine-in?  
5. Do you already have **quotes** for rent, fit-out, or espresso equipment?  
6. Is SAR 450,000 **all-in** (CAPEX + WC), or is additional funding available?

---

## 24. Final Decision

| Field | Value |
|---|---|
| Verdict | **INSUFFICIENT_EVIDENCE** |
| Strong GO | **Blocked** |
| Rationale | Financial case inconclusive; operating assumptions and competitor/location evidence missing; decision safety reduced confidence |
| Conditions to reopen decision | Close gaps in §21; re-run research → assumptions → financials |
| Recommended owner action | Supply district + any quotes; authorize deeper operating research; do **not** commit CAPEX yet |

---

## Appendix A — How to read this vs a Claude-style packed study

Claude-style packs typically fill every section with **specific numbers**.  
This Saudi Business report intentionally leaves sections **UNKNOWN** where evidence does not support precision.

That is a **feature of decision safety**, not a formatting defect.

When operating evidence is later retrieved and governed, the same section skeleton can carry:

- component CAPEX totals  
- rent / labor OPEX  
- covers × ticket revenue  
- COGS / EBITDA  
- WC + budget SURPLUS/SHORTFALL  
- NPV / IRR / payback when mathematically valid  

---

## Appendix B — Study metadata

| Field | Value |
|---|---|
| Study | `study_d4ff0d3d5c7b` |
| Project | `1202` |
| Phase | REPORT_READY |
| Claude data used as evidence | **NO** |
| Claude numbers copied | **NO** |
