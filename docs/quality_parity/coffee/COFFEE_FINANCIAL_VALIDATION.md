# Coffee Financial Validation

## Formulas (deterministic F&B extract)

- Daily revenue = `daily_covers × avg_ticket`
- Annual revenue Y1 = `daily_covers × avg_ticket × operating_days_year` (default days=330 if omitted)
- Y2/Y3 = Y1 × 1.08 / ×1.08² (existing ramp structure)
- COGS = Revenue × food_cost_pct (default 32% only when food_cost missing — noted as SYSTEM estimate note)
- Fixed OPEX annual = (rent + labor + utilities + marketing) × 12
- Annual costs = COGS + fixed OPEX (+ mild inflation on fixed for Y2/Y3)
- CAPEX = equipment + fitout + other
- WC = explicit assumption OR estimate 2 × monthly (fixed + COGS/12)
- Total initial funding = CAPEX + WC
- Budget gap = total initial − owner_budget → SHORTFALL if > 0 else SURPLUS

## Trust rules preserved

- Currency: SAR explicit
- No silent currency mixing
- IRR only when mathematically valid
- Payback only when cumulative CF crosses zero
- Placeholder / hours / % / seats / ticket / orders gates
- Unsupported strong GO remains blocked

## Test evidence

See `tests/test_coffee_quality_parity.py` (22 passed) plus Phase 8C.2 / 8C.3 / Product Hardening / P1-A / financial trust regressions.

## Claude numbers

**Not used** as defaults, fixtures, or expected values.
