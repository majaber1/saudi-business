# Saudi Business — Financial Capture (Coffee Case)

**Study:** `study_04778d06a34f`  
**Main SHA:** `3a7efebad7831b635cee63060aa7aec12310199b`  
**Currency:** SAR  
**Forecast:** 3 years · discount rate 12%  

Values below are **exactly as produced** — not corrected.

---

## Owner budget

| Item | SAR |
|------|-----|
| Owner available budget | 450,000 |

---

## Initial funding (product)

| Item | SAR | Notes |
|------|-----|-------|
| CAPEX (`financial_results.capex`) | 10,000 | Matches `fitout_capex` assumption |
| Working capital (explicit line) | Not provided | Risks mention WC gap qualitatively |
| Total initial modeled outflow | 10,000 | `cash_flows[0]` |
| Budget surplus (naive) | +440,000 | CAPEX ≪ budget |
| Budget overrun flag | None | |

**Budget Handling assessment:** Product did not build a coffee-realistic CAPEX stack against SAR 450,000. It also did not silently invent a SAR 450k spend. Overrun handling: N/A. Decision usefulness vs budget test: **FAIL**.

---

## P&L / returns (product)

| Metric | Value |
|--------|-------|
| Revenue Y1 / Y2 / Y3 | 0 / 0 / 0 |
| Cost Y1 / Y2 / Y3 | 0 / 0 / 0 |
| Gross profit / margin | Not computed (zeros) |
| EBITDA / margin | Not computed |
| NPV | -10,000 |
| IRR | null (unavailable) |
| Payback months | null (unavailable) |
| Breakeven months | 0 |
| Cash flows | [-10000, 0, 0, 0] |

### Scenario pack

All of optimistic / base / conservative: NPV -10000; IRR cannot be calculated.

### IRR / Payback machine messages

- IRR: no sign change / extreme profile.  
- Payback: cumulative CF never recovers investment in window.

---

## Operating inputs feeding (or failing to feed) the model

| Assumption | Stored value | Appears in revenue math? |
|------------|--------------|---------------------------|
| avg_ticket | 10000 SAR | No — revenue remains 0 |
| daily_covers | 10000 | No — revenue remains 0 |
| rent_monthly | 10000 SAR | No — costs remain 0 |
| labor_monthly | 10000 SAR | No — costs remain 0 |
| food_cost_pct | 10% | No |
| fitout_capex | 10000 SAR | Yes — as CAPEX / CF0 |
| seats_capacity | 10000 | No capacity→revenue link visible |
| operating_hours_day | 10000 | Implausible; note `services_billable_period_defaulted_hours_x_12` in extract_notes |

---

## Trust checks (observer)

| Check | Result |
|------|--------|
| Currency consistency | PASS (SAR) |
| Period consistency | PASS (3y labels) |
| CAPEX reconciliation to fitout assumption | PASS (10000=10000) |
| Budget reconciliation to coffee reality | FAIL |
| Revenue arithmetic vs covers×ticket | FAIL (should be ≫0 if assumptions applied; got 0) |
| EBITDA arithmetic | N/A / FAIL usefulness |
| Break-even | Suspicious (`0` with zero revenue) |
| NPV arithmetic given CF | PASS (−10000 ≈ −CAPEX with zero later CF @ 12%) |
| IRR validity messaging | PASS (correctly unavailable) |
| Payback messaging | PASS (correctly unavailable) |
| Silent correction | `silent_correction_applied: false` |

**Financial Trust:** WEAK  
**Financial Arithmetic (engine on its own CF vector):** PASS for NPV identity; FAIL for assumption→P&L wiring.

---

## Hardening trust gates on financial extract

```json
{
  "status": "PASS",
  "codes": [],
  "messages": [],
  "confidence_penalty": 0,
  "requires_validation": false,
  "silent_correction_applied": false
}
```

Downstream decision still landed on **INSUFFICIENT_EVIDENCE** via decision rationale / missing evidence conditions — not via a typed financial trust gate code in this payload.
