# 14 — Business Decision Simulator Specification

## Module Purpose

A real what-if decision workspace that lets users test how business changes affect financial outcomes, risks, and evidence sensitivity — without modifying the approved baseline until the user explicitly applies a scenario.

## Core Concept

The Simulator operates on a **locked baseline** from the approved feasibility study. Users adjust parameters, and the system computes the impact in real-time, showing current vs scenario across all key metrics.

## Entry Conditions

- Study must have an approved financial model (minimum: revenue + OPEX + investment)
- Baseline is locked at the time of the last owner-approved decision
- User can create scenarios even with partial evidence (system warns about reduced confidence)

## Scenario Parameters

### Adjustable Parameters (domain-configured)

| Category | Parameter | Unit | Example Range |
|----------|-----------|------|---------------|
| **Revenue** | Average ticket / price | SAR | ±50% |
| | Daily transactions / customers | count | ±50% |
| | Operating days per year | days | 300-365 |
| | Capacity utilization | % | 30-100% |
| **Costs** | Rent | SAR/month | ±100% |
| | Labor cost | SAR/month | ±100% |
| | COGS percentage | % | ±20 points |
| | Utilities | SAR/month | ±50% |
| | Marketing | SAR/month | 0 - 2x |
| **Investment** | Equipment / CAPEX | SAR | ±50% |
| | Fit-out / renovation | SAR | ±50% |
| | Working capital months | months | 1-12 |
| **Expansion** | New branch | toggle | Add location |
| | Additional staff | count | +1 to +20 |
| | New product/service line | toggle | Add revenue stream |
| **External** | Market growth rate | % | -10% to +30% |
| | Competitor intensity | qualitative | Low/Medium/High |
| | Funding interest rate | % | 0-15% |

### Parameter Input UX
- **Sliders** for continuous numeric parameters (with direct input override)
- **Toggle** for boolean parameters (new branch: yes/no)
- **Dropdown** for qualitative parameters
- **Evidence link** shown next to each parameter: current value's evidence class and source

## Impact Display

### Comparison Table

```
┌──────────────────┬───────────┬───────────┬──────────┐
│ Metric           │ Current   │ Scenario  │ Delta    │
├──────────────────┼───────────┼───────────┼──────────┤
│ Annual Revenue   │           │           │          │
│   Low            │ 420k SAR  │ 462k SAR  │ +10%     │
│   Base           │ 680k SAR  │ 748k SAR  │ +10%     │
│   High           │ 1.1M SAR  │ 1.21M SAR │ +10%     │
├──────────────────┼───────────┼───────────┼──────────┤
│ Annual OPEX      │ 540k SAR  │ 540k SAR  │ 0%       │
├──────────────────┼───────────┼───────────┼──────────┤
│ Net Profit (Base)│ 140k SAR  │ 208k SAR  │ +49%     │
├──────────────────┼───────────┼───────────┼──────────┤
│ Break-even       │ 22 months │ 16 months │ -6 mo    │
├──────────────────┼───────────┼───────────┼──────────┤
│ Investment Req.  │ 480k SAR  │ 480k SAR  │ 0%       │
├──────────────────┼───────────┼───────────┼──────────┤
│ Profit Margin    │ 21%       │ 28%       │ +7pts    │
└──────────────────┴───────────┴───────────┴──────────┘
```

### Visual Indicators
- **Green delta**: Improvement
- **Red delta**: Deterioration
- **Gray delta**: No change
- **Warning icon**: When scenario pushes beyond evidence-supported range

## Evidence Sensitivity Analysis

When a scenario changes a parameter beyond the evidence-supported range, the system warns:

```
⚠ Evidence Sensitivity Warning

"Price +15%" pushes average ticket to 35 SAR.
Evidence supports a range of 25-32 SAR (SYSTEM_ESTIMATE, confidence 72%).
This scenario assumes conditions beyond current evidence.

Impact: Revenue projections have REDUCED CONFIDENCE in this scenario.
```

This is a key differentiator: the simulator doesn't just compute numbers — it tells you when you're operating beyond what the evidence supports.

## Risk Impact Assessment

For each scenario, show how the risk profile changes:

| Risk | Current Level | Scenario Level | Change |
|------|--------------|----------------|--------|
| Rent affordability | Medium | Medium | → |
| Demand shortfall | Medium | Low | ↓ (price increase may reduce volume) |
| Staffing cost | Low | Low | → |
| Competition | High | High | → |

## Scenario Management

### Save Scenario
- Name the scenario (e.g., "Price increase 10%", "Dammam branch expansion")
- Saved with all parameter changes and computed results
- Versioned: same-name save creates a new version

### Compare Scenarios
- Side-by-side comparison of up to 3 scenarios + baseline
- Highlight best/worst per metric
- AI recommendation per scenario

### Apply Scenario
- Requires owner approval
- Replaces the approved baseline with the scenario's parameters
- Creates a new decision version
- Triggers re-assessment of funding readiness, risk profile

## AI Recommendation Per Scenario

For each scenario, the Decision Advisor agent assesses:

```
Scenario: "Price increase 10%"

Recommendation: FAVORABLE

This scenario improves profitability by 49% and reduces break-even by 6 months.
However, the price increase pushes average ticket beyond evidence-supported range.
Consider validating customer price sensitivity before applying.

Confidence: Medium (evidence gap on price elasticity)
```

## Multi-Variable Scenarios

Users can combine multiple parameter changes:

```
Scenario: "Aggressive growth"
  - Price +10%
  - Capacity +20% (extended hours)
  - Staff +2 employees
  - Marketing +50%
  - Rent +5% (larger space)

Combined impact computed holistically, not as sum of individual changes.
```

## Scenario Examples (Pre-Built Templates)

| Template | Parameters Changed | Use Case |
|----------|-------------------|----------|
| Price sensitivity | Price ±10%, ±20% | "What if I charge more/less?" |
| Cost pressure | Rent +15%, COGS +5% | "What if costs increase?" |
| Expansion | +1 branch, +staff, +CAPEX | "What if I open a second location?" |
| Downside | Revenue -20%, Costs +10% | "What's the worst case?" |
| Funding structure | Interest rate, term changes | "What if my loan terms change?" |

## Empty State

"The Decision Simulator lets you test how changes affect your business outcomes. Your approved financial baseline is locked and ready. Choose a parameter to start exploring scenarios."

## Error/Recovery

- Model computation error: "Unable to compute this scenario. Try adjusting parameters." + show last valid result
- Extreme parameters: "Parameters are outside reasonable range. Results may not be meaningful." (still compute, but warn)
- Baseline not available: "A completed financial model is needed before simulation. Complete your feasibility study first."

## Mobile Behavior

- Parameter sliders work touch-friendly
- Comparison table scrolls horizontally
- Simplified view: key metrics only (Revenue, Profit, Break-even)
- Full comparison requires desktop
