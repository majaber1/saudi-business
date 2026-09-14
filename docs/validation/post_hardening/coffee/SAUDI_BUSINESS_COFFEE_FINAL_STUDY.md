# Saudi Business — Final Study Capture (Coffee Case)

**Study ID:** `study_04778d06a34f`  
**Project ID:** `1201`  
**Main SHA:** `3a7efebad7831b635cee63060aa7aec12310199b`  
**Captured:** 2026-09-14 (UTC) after REAL_USER_FLOW completion + relogin  
**Full JSON:** `study_state.json` (same folder) and `/opt/cursor/artifacts/coffee-validation/study_state.json`

---

## Profile

- Archetype: `fnb` (confirmed)  
- Sector: Specialty coffee shop  
- Stage: idea  
- Decision goal: investment  
- Recommended model: `fnb_2024`  
- Sector pack: F&B — required research areas include local_demand, competitor_pricing, rent_location_economics, labor_availability, licensing  

---

## Verdict (as produced)

**INSUFFICIENT_EVIDENCE**

### Rationale (verbatim substance from product)

Preliminary financial model shows NPV SAR -10,000 and undefined IRR; assumptions such as 10,000 seats / daily covers / SAR rent appear unrealistic. Critical risks: Riyadh specialty coffee competition, working capital, specialty supply chain. Dataset incomplete (store size, exact location, rent/m², staffing mix, ticket, detailed CAPEX/COGS). Decision safety reduced confidence to insufficient evidence.

### Conditions (product list)

1. Complete detailed financial projections with realistic rent, staffing, ticket, opex.  
2. Market feasibility for foot traffic and competitive position.  
3. Supply-chain plan with multiple bean suppliers.  
4. Working capital for ≥12 months of operating losses.  
5. Re-run financial model when data available.  
6. Collect critical evidence: competitors.  
7. Collect critical evidence: location_economics.  
8. Collect critical evidence: demand.  

### Risks (product list)

- Low foot-traffic / high competition / saturation in Riyadh  
- Insufficient WC for initial losses  
- Specialty bean / milk / pastry supply disruption  
- Regulatory / licensing delay  
- Ticket vs willingness-to-pay misalignment  

---

## Assumptions (persisted)

| Key | Value | Unit | Origin |
|-----|-------|------|--------|
| location_city | Riyadh, Saudi Arabia | | user |
| business_model | Café / specialty coffee | | user |
| seats_capacity | 10000 | seats | AI / knowledge_reference (low) |
| operating_hours_day | 10000 | hours | AI (low) |
| avg_ticket | 10000 | SAR | AI (low) |
| daily_covers | 10000 | | AI (low) |
| rent_monthly | 10000 | SAR | AI (low) |
| labor_monthly | 10000 | SAR | AI (low) |
| food_cost_pct | 10 | % | AI (low) |
| delivery_dependency | 10000 | | AI (low) |
| fitout_capex | 10000 | SAR | AI (low) |

---

## Financial results (persisted)

```json
{
  "revenue_projections": { "year_1": 0, "year_2": 0, "year_3": 0 },
  "cost_projections": { "year_1": 0, "year_2": 0, "year_3": 0 },
  "capex": 10000,
  "npv": -10000,
  "irr": null,
  "payback_months": null,
  "breakeven_months": 0,
  "cash_flows": [-10000, 0, 0, 0],
  "discount_rate": 0.12,
  "projection_years": 3,
  "analysis_complete": true,
  "irr_available": false,
  "payback_available": false
}
```

Scenarios optimistic/base/conservative all NPV -10000; IRR unavailable.

Trust gates on financial extract: `status: PASS` (no codes).

---

## Research snapshot

- `research_status`: complete  
- Market research status: PARTIAL  
- Live GASTAT fetch: ok (3 documents / 3 claims)  
- MISA: knowledge_hit  
- Pricing evidence: NOT_FOUND  
- Competitors: []  

---

## Phase

`REPORT_READY`

---

## Notes for Claude comparison

This is the **natural** Saudi Business output after Hardening. Do not treat AI estimate placeholders as owner-provided inputs. Owner-provided facts were only: specialty coffee concept, Riyadh, SAR 450k budget, F&B offer mix, customer segments, viability objective.
