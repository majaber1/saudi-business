# Coffee Final Study (REAL_USER_FLOW)

**Study:** `study_d4ff0d3d5c7b`  
**Verdict:** `INSUFFICIENT_EVIDENCE`  

## Decision rationale

Financial case is inconclusive (NPV=0.0, IRR=None). Defer full commitment until assumptions are de-risked. Decision safety gates reduced confidence: INSUFFICIENT_EVIDENCE.

## Conditions

- Improve evidence quality on revenue and cost drivers
- Collect critical evidence: competitors.
- Collect critical evidence: location_economics.
- Collect critical evidence: demand.

## Risks

- Market demand uncertainty
- Funding gap
- Execution capacity

## Assumptions

- `owner_budget` = 450000.0 (USER_PROVIDED)
- `location_city` = Riyadh, Saudi Arabia (USER_PROVIDED)
- `business_model` = Café / specialty coffee (USER_PROVIDED)
- `seats_capacity` = UNKNOWN (UNKNOWN)
- `operating_hours_day` = UNKNOWN (UNKNOWN)
- `avg_ticket` = UNKNOWN (UNKNOWN)
- `daily_covers` = UNKNOWN (UNKNOWN)
- `rent_monthly` = UNKNOWN (UNKNOWN)
- `labor_monthly` = UNKNOWN (UNKNOWN)
- `food_cost_pct` = UNKNOWN (UNKNOWN)
- `delivery_dependency` = Partial (<30%) (SYSTEM_ESTIMATE)
- `fitout_capex` = UNKNOWN (UNKNOWN)

## Financial snapshot

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

## Competitors

```json
[
  {
    "name": "",
    "source_url": null,
    "evidence_type": "none",
    "geography": "Saudi Arabia",
    "confidence": 0.0,
    "evidence_reference": "no_sourced_competitor_evidence",
    "status": "NOT_FOUND",
    "source_key": null,
    "document_id": null,
    "chunk_id": null
  }
]
```

Claude numbers were **not** copied into this study.
