# Coffee REAL_USER_FLOW Report

**Classification:** REAL_USER_FLOW  
**Study ID:** `study_d4ff0d3d5c7b`  
**Project ID:** `1202`  
**Phase:** `REPORT_READY`  
**Verdict:** `INSUFFICIENT_EVIDENCE`  
**Owner input modified:** NO  
**Manual Claude injection:** NO  

## Owner input (exact)

- Business: Premium specialty coffee shop
- Location: Riyadh, Saudi Arabia
- Budget: SAR 450,000
- Model: Physical specialty coffee; specialty coffee, cold beverages, light desserts, takeaway
- Customers: young professionals, university students, office workers, nearby residents

## Assumption quality (post-fix)

| Key | Value | Provenance |
|---|---|---|
| `owner_budget` | 450000.0 | USER_PROVIDED |
| `location_city` | Riyadh, Saudi Arabia | USER_PROVIDED |
| `business_model` | Café / specialty coffee | USER_PROVIDED |
| `seats_capacity` | UNKNOWN | UNKNOWN |
| `operating_hours_day` | UNKNOWN | UNKNOWN |
| `avg_ticket` | UNKNOWN | UNKNOWN |
| `daily_covers` | UNKNOWN | UNKNOWN |
| `rent_monthly` | UNKNOWN | UNKNOWN |
| `labor_monthly` | UNKNOWN | UNKNOWN |
| `food_cost_pct` | UNKNOWN | UNKNOWN |
| `delivery_dependency` | Partial (<30%) | SYSTEM_ESTIMATE |
| `fitout_capex` | UNKNOWN | UNKNOWN |

**Placeholder 10000 hits:** `[]` (must be empty)

## Financial (after CAPEX/owner-budget fix)

```json
{
  "capex": 0.0,
  "capex_components": {
    "equipment_capex": 0.0,
    "fitout_capex": 0.0,
    "other_capex": 0.0
  },
  "working_capital": 0.0,
  "total_initial_funding": 0.0,
  "owner_budget": 450000.0,
  "budget_status": "SURPLUS",
  "budget_gap": -450000.0,
  "currency": "SAR",
  "revenue_projections": {
    "year_1": 0.0,
    "year_2": 0.0,
    "year_3": 0.0
  },
  "cost_projections": {
    "year_1": 0.0,
    "year_2": 0.0,
    "year_3": 0.0
  },
  "npv": 0.0,
  "irr": null,
  "payback_months": null,
  "extract_notes": [
    "fnb_revenue_blocked_missing_or_unknown_ticket_or_covers",
    "fnb_capex_missing_or_unknown",
    "fnb_working_capital_unknown",
    "fnb_budget_surplus",
    "fnb_extract_incomplete_insufficient_numeric_inputs"
  ]
}
```

Notes:
- Revenue blocked while ticket/covers are UNKNOWN (correct — no fake precision).
- CAPEX no longer equals owner budget (was a LLM-explain overwrite bug; fixed).
- Budget status SURPLUS vs total funding 0 reflects incomplete CAPEX/WC — not a claim that SAR 450k is enough for a built café.
- Verdict remains `INSUFFICIENT_EVIDENCE` (decision safety preserved).

## Market / competitors

- Claims: 5 (mostly GASTAT macro)
- Competitors: `[{'name': '', 'source_url': None, 'evidence_type': 'none', 'geography': 'Saudi Arabia', 'confidence': 0.0, 'evidence_reference': 'no_sourced_competitor_evidence', 'status': 'NOT_FOUND', 'source_key': None, 'document_id': None, 'chunk_id': None}]`
- Market status: `PARTIAL`

## Persistence

- PASS via refresh + logout/login reopen during automation, and API re-fetch after approve/continue.

## Performance (approx)

- Initial UI discovery→assumptions automation: ~8–10 min (includes language/discovery hang recovery)
- Research/evidence: embedded in discovery submit (~1–2 min for 5 claims)
- Analysis/decision continues: <2 min after approve
- Primary delay: **MIXED** (CURSOR_AUTOMATION_LATENCY early + PRODUCT_LATENCY / EXTERNAL_API for research)

## Screenshots

Under `/opt/cursor/artifacts/coffee-parity-ruf/` (01–13, 20–23, 30–32).
