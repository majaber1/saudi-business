# Saudi Business — Post-Hardening Coffee Validation Report

**Case:** 1 — Riyadh Specialty Coffee  
**Mode:** VALIDATION ONLY — REAL_USER_FLOW  
**Date (UTC):** 2026-09-14  
**Main SHA:** `3a7efebad7831b635cee63060aa7aec12310199b`  
**Product Hardening:** CLOSED_AND_FROZEN  
**Phase 9A:** NOT_STARTED  

---

## Execution identity

| Field | Value |
|------|--------|
| Classification | **REAL_USER_FLOW** |
| Code changes | **NONE** |
| Architecture | **UNCHANGED** |
| Migration | **NONE** |
| Study ID | `study_04778d06a34f` |
| Project ID | `1201` |
| Workspace URL | `/projects/1201/studies/study_04778d06a34f/workspace` |
| Account | new registered user (`credentials.json` in artifacts; not secrets-committed) |

---

## Owner input used (only)

- Business: Premium specialty coffee shop  
- Location: Riyadh, Saudi Arabia  
- Budget: SAR 450,000 (project investment field + brief)  
- Model: Physical specialty coffee; specialty coffee, cold beverages, light desserts, takeaway  
- Customers: young professionals, university students, office workers, nearby residents  
- Objective: commercial viability / investment-worthiness  

No store size, district, rent, staffing, cups/day, ticket, CAPEX breakdown, COGS, margins, or discount rate were entered by the validator except where the product asked and the answer was taken from this brief (city + specialty-café model). All other discovery fields used **Let AI estimate**.

---

## Flow path actually executed

1. Register → English UI  
2. Create project (food / 450000 / idea)  
3. Open AI study workspace  
4. Send owner brief  
5. Confirm archetype **F&B / Restaurant / Café (`fnb`)**  
6. Discovery interview (11 questions)  
7. Research / evidence review → Approve Evidence  
8. Assumptions review → Approve all eligible  
9. Continue → risks → decision / report  
10. Refresh persistence  
11. Logout → login → reopen same study  

Screenshots: `/opt/cursor/artifacts/coffee-validation/` (01–13, plus discovery/final).

---

## Missing-information handling (product behavior)

| Question | Handling |
|----------|----------|
| F&B business model | ASKED_USER — selected café / specialty coffee |
| City / district | ASKED_USER — Riyadh, Saudi Arabia |
| Seats / capacity | SYSTEM_ESTIMATE (AI estimate) |
| Operating hours / day | SYSTEM_ESTIMATE |
| Average ticket size | SYSTEM_ESTIMATE |
| Expected daily covers | SYSTEM_ESTIMATE |
| Monthly rent | SYSTEM_ESTIMATE |
| Monthly labor cost | SYSTEM_ESTIMATE |
| Food / beverage cost % | SYSTEM_ESTIMATE |
| Delivery dependency | SYSTEM_ESTIMATE |
| Fit-out / opening CAPEX | SYSTEM_ESTIMATE |

**Observation:** The product **does ask the right coffee/F&B operating questions**. It does **not** silently skip them. However, when “AI estimate” is chosen, this run filled many critical fields with implausible placeholder-like values (`10000` seats, `10000` hours/day, `10000` SAR ticket, `10000` daily covers, `10000` SAR rent/labor/CAPEX, `10000` delivery dependency, food cost `10%`). The study later correctly refused a strong GO.

---

## Research & Saudi authority

| Item | Result |
|------|--------|
| Live GASTAT connector | Used (`mcp_live`, healthy) |
| Claims retrieved | 5 (3 GASTAT news + 1 MISA fragment + 1 market signal) |
| Coffee-specific demand / rent / ticket evidence | **Not found** (pricing `NOT_FOUND`) |
| Competitors list | **Empty** |
| Monsha’at / Balady / ZATCA / MoC | **Not present** in this study’s used evidence |
| Research status | `complete` / market `PARTIAL` |

Official sources that **were** used: GASTAT CPI inflation (~1.8–1.9% Mar 2026), GDP Q1 growth 3.0%, wholesale/retail operating revenues +3.2% Q2 2026. These are macro signals, not specialty-coffee unit economics.

---

## Operating model produced (as stored)

| Assumption | Value | Origin |
|------------|-------|--------|
| location_city | Riyadh, Saudi Arabia | user |
| business_model | Café / specialty coffee | user |
| seats_capacity | 10000 seats | AI estimate (low confidence) |
| operating_hours_day | 10000 hours | AI estimate (low confidence) |
| avg_ticket | 10000 SAR | AI estimate (low confidence) |
| daily_covers | 10000 | AI estimate (low confidence) |
| rent_monthly | 10000 SAR | AI estimate (low confidence) |
| labor_monthly | 10000 SAR | AI estimate (low confidence) |
| food_cost_pct | 10% | AI estimate (low confidence) |
| delivery_dependency | 10000 | AI estimate (low confidence) |
| fitout_capex | 10000 SAR | AI estimate (low confidence) |

Coffee-specific pack (`fnb`) activated. Model is **structurally F&B**, but **numeric estimates in this run are not commercially credible**.

---

## Budget handling

| Item | Value |
|------|-------|
| Owner budget | SAR 450,000 |
| CAPEX (`financial_results.capex` / fitout assumption) | SAR 10,000 |
| Working capital | Not separately quantified in financial_results |
| Total initial requirement (as modeled) | SAR 10,000 outflow in cash_flows[0] |
| Surplus vs budget (naive) | +SAR 440,000 |
| Budget overrun flag | **Not raised** (CAPEX ≪ budget) |
| Verdict respect for budget | N/A overrun; verdict blocked on evidence/quality instead |

**Budget Handling grade:** FAIL for decision usefulness — CAPEX is not a credible specialty-coffee build vs SAR 450k; product did not reconcile opening requirement to the stated budget in a coffee-realistic way. It did not silently force a GO on budget fit.

---

## Financial trust

| Metric | Product value |
|--------|----------------|
| Revenue Y1–Y3 | 0 / 0 / 0 |
| Costs Y1–Y3 | 0 / 0 / 0 |
| CAPEX | 10,000 |
| NPV | -10,000 |
| IRR | null / unavailable |
| Payback | unavailable |
| Breakeven months | 0 |
| Discount rate | 12% |
| Cash flows | [-10000, 0, 0, 0] |
| Trust gates status | PASS (codes empty) |

**Financial arithmetic:** Internal consistency of the *degraded* model (CAPEX-only outflow → NPV ≈ -CAPEX at zero CF) holds, but the model is not a usable coffee P&L.  
**Currency:** SAR labels present; consistent.  
**Financial Trust:** WEAK.

---

## Evidence ↔ assumption safety

- Macro GASTAT claims do **not** support `10000` seats/covers/ticket.  
- Decision text explicitly calls assumptions unrealistic and lists missing critical evidence (competitors, location_economics, demand).  
- Final verdict **INSUFFICIENT_EVIDENCE** — critical contradictions / missing coffee economics did **not** produce a strong GO.

**Decision Safety:** PASS (downgrade path worked) even though numeric AI estimates were poor.

---

## Competitors

**MISSING** (empty `competitors` array). Risks mention “intense competition” qualitatively without named Riyadh specialty cafés or prices.

---

## Risks (product-listed)

1. Low foot-traffic / competition saturation in Riyadh  
2. Insufficient working capital for early losses  
3. Specialty supply-chain disruption  
4. Licensing / regulatory delay  
5. Ticket vs willingness-to-pay misalignment  

Site/rent/demand/staffing/budget themes appear at least partly. Named competitor analysis absent.

---

## Final decision

| Field | Value |
|------|--------|
| Raw verdict | `INSUFFICIENT_EVIDENCE` |
| Normalized | **INSUFFICIENT_EVIDENCE** |
| Conditions | Complete realistic financials; market feasibility; supply chain; 12 months WC; re-run model; collect competitors / location_economics / demand evidence |
| Owner questions (in rationale) | store size, district, rent/m², staffing mix, ticket, detailed CAPEX/COGS |

---

## Persistence

| Check | Result |
|------|--------|
| Refresh | PASS — same study, phase REPORT_READY, verdict unchanged |
| Logout/Login | PASS |
| Reopen same study | PASS |
| Research persisted | PASS (claims + research_quality_observability) |
| Evidence persisted | PASS (5 claims) |
| Financials persisted | PASS (`financial_results` present after relogin; earlier runner flag used wrong key) |
| Decision persisted | PASS |

---

## Issues found (documented only — not fixed)

1. AI estimate path produced non-physical defaults (~10000) for multiple F&B critical assumptions.  
2. Financial engine produced zero revenue/opex despite huge assumed covers/ticket (extract/mapping failure or guardrail collapse).  
3. Competitor / rent / specialty pricing research not populated.  
4. Budget SAR 450,000 not meaningfully stress-tested against a realistic coffee CAPEX stack.  
5. Some MISA claim text appears truncated/fragmentary.  

---

## Overall grades

| Dimension | Grade |
|-----------|-------|
| Assumption quality | WEAK (structure OK, values not) |
| Research quality | PARTIAL (official macro yes; coffee unit economics no) |
| Financial trust | WEAK |
| Decision trust | PARTIAL → strong on gating, weak on model inputs |
| Commercial decision readiness | WEAK |
| Ready for independent Claude comparison | **YES** (natural product output captured; do not optimize) |

---

## Governance confirmation

- No application code modified for this case.  
- No Phase 9A / Benchmark Engine started.  
- No RAG/pgvector/connectors/agents architecture added.  
- Research Quality 8C.2 semantics not changed.  
- Product Hardening remains CLOSED_AND_FROZEN.
