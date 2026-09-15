# 10 — Data Requirements for UX

Conceptual data needs per screen. This does NOT redesign the database — it identifies what each screen must receive from the API.

## Command Center (S04)

```
GET /api/v2/dashboard
Response:
  studies: [{id, name, sector, status, phase, evidence_coverage, key_metric, last_updated, ai_insight}]
  inbox_count: number
  top_risks: [{id, study_id, name, severity, likelihood}]
  top_opportunities: [{id, title, relevance_score, potential, signal_type}]
  funding_status: [{study_id, readiness_score, gap}]
  recent_activity: [{timestamp, type, description, study_id}]
  ai_summary: string (portfolio-level insight)
```

## My Businesses (S04a)

```
GET /api/v2/businesses
Response:
  businesses: [{id, name, sector, location, status, health_score, latest_decision, evidence_coverage_pct, last_activity, study_count}]
```

## Business Home (S04b)

```
GET /api/v2/businesses/:bid
Response:
  profile: {name, sector, location, status, created_at}
  health: {score, factors: [{name, status}]}
  latest_baseline: {investment, revenue_base, break_even, decided_at}
  studies: [{id, name, status, phase, decision, created_at}]
  latest_decision: {outcome, decided_by, decided_at, conditions}
  evidence_health: {coverage_pct, fresh_count, aging_count, stale_count, gap_count}
  recent_activity: [{timestamp, type, description}]
  recommended_action: {label, action_url, reason}
```

## Workspace Overview (S07)

```
GET /api/v2/businesses/:bid/studies/:id/overview
Response:
  profile: {name, sector, location, status, last_updated}
  investment: {low, base, high, evidence_class, confidence}
  break_even: {months_low, months_base, months_high, calculable, evidence_class}
  budget_assessment: {budget, sufficient, conditions}
  revenue_scenarios: {low, base, high, evidence_class}
  evidence_summary: {verified_count, estimate_count, assumption_count, unknown_count, total}
  competitors: [{name, type, location, key_differentiator}] (top 3)
  location: {name, map_thumbnail_url, key_facts: [{label, value}]}
  risks: [{name, severity, mitigation_status}] (top 3)
  decision: {recommendation, reasoning_summary, conditions, confidence}
  next_steps: [{label, action_url, completed}]
```

## Workspace Tabs (S08-S11)

```
GET /api/v2/businesses/:bid/studies/:id/market
GET /api/v2/businesses/:bid/studies/:id/competitors
GET /api/v2/businesses/:bid/studies/:id/location
GET /api/v2/businesses/:bid/studies/:id/operations

Common response pattern:
  dimension_summary: string
  data_points: [{
    label, value, range_low, range_high,
    evidence_class, confidence, evidence_id,
    source_summary, last_updated
  }]
  evidence_coverage: {covered, total, gaps: [{label, status}]}
  research_status: "complete" | "in_progress" | "pending"
```

## Financials (S12)

```
GET /api/v2/businesses/:bid/studies/:id/financials
Response:
  investment: {
    capex: [{category, low, base, high, evidence_class, evidence_id}],
    working_capital: {low, base, high, evidence_class},
    total: {low, base, high}
  }
  revenue: {
    annual: {low, base, high, evidence_class},
    drivers: [{name, value, evidence_class, evidence_id}]
  }
  opex: {
    categories: [{name, monthly_low, monthly_base, monthly_high, evidence_class, evidence_id}],
    total_monthly: {low, base, high},
    total_annual: {low, base, high}
  }
  cash_flow: [{month, revenue, costs, net, cumulative}] (per scenario)
  break_even: {months, calculable, missing_inputs: [string], confidence}
  budget_sufficiency: {budget, required_low, required_high, verdict, conditions}
  sensitivity: [{variable, impact_pct, direction}]
```

## Evidence (S13, S16)

```
GET /api/v2/businesses/:bid/evidence
Query params: ?class=&source=&confidence_min=&sort=&page=&study_id=
Response:
  coverage: {dimensions: [{name, covered, total, status}]}
  summary: {verified: N, estimate: N, assumption: N, unknown: N}
  items: [{
    id, label, value, range_low, range_high,
    evidence_class, confidence, source_name, source_url,
    observation_count, date, geography, derivation_summary,
    decision_impact: "high" | "medium" | "low",
    editable: boolean
  }]
  gaps: [{label, dimension, impact, actions: ["request_research", "add_assumption"]}]

GET /api/v2/businesses/:bid/evidence/:eid (detail)
Response:
  ...full item fields...
  derivation_chain: [{step, description, source}]
  history: [{timestamp, change, by}]
  dependent_outputs: [{label, module}]
```

## Decision (S15)

```
GET /api/v2/businesses/:bid/studies/:id/decision
Response:
  recommendation: "GO" | "GO_WITH_CONDITIONS" | "DEFER" | "NO_GO"
  reasoning: [{step, question, answer, evidence_summary}]
  conditions: [{label, status, detail}]
  evidence_at_decision: {verified, estimate, assumption, unknown, coverage_pct}
  key_financials: {investment, revenue_base, break_even}
  key_risks: [{name, severity, acknowledged}]
  owner_decision: {outcome, decided_by, decided_at, override_reason} | null
  available_actions: ["approve", "override", "request_research"]
  next_steps: [{label, action, enabled}]

POST /api/v2/businesses/:bid/studies/:id/decision
Body: {action: "approve" | "override", override_outcome?, reason?}
```

## Funding (S20-S24)

```
GET /api/v2/businesses/:bid/funding
Response:
  readiness_score: {total, dimensions: [{name, score, max}]}
  requirement: {total, available, gap}
  documents: [{name, status: "ready"|"missing"|"draft", required, action}]
  programs: [{name, type, eligibility_pct, requirements, matched_reason}]
  packages: {investor: {status, generated_at}, bank: {status, generated_at}}
  timeline: [{milestone, target_date, status}]
```

## Opportunity Radar (S25-S27)

```
GET /api/v2/opportunities
Query params: ?signal_type=&sort=&page=
Response:
  opportunities: [{
    id, title, signal_type, why_now, evidence_count,
    potential: "low"|"medium"|"high", risk_level,
    relevance_score, relevance_reason,
    actions: ["create_study", "simulate", "save", "dismiss"]
  }]
```

## Simulator (S28-S31)

```
GET /api/v2/businesses/:bid/simulator
Response:
  baseline: {investment, revenue, opex, break_even, locked_at}
  parameters: [{name, current_value, min, max, step, unit, evidence_class}]
  saved_scenarios: [{id, name, created_at, summary}]

POST /api/v2/businesses/:bid/simulator/run
Body: {changes: [{parameter, new_value}]}
Response:
  scenario: {
    revenue: {low, base, high}, profit: {low, base, high},
    break_even, cash_flow: [...],
    delta: {revenue_pct, profit_pct, break_even_delta},
    risk_impact: [{risk, change}],
    evidence_sensitivity: [{parameter, beyond_evidence: boolean, warning}],
    recommendation: string
  }
```

## Monitoring (S32-S35)

```
GET /api/v2/businesses/:bid/monitoring
Response:
  kpis: [{name, planned, actual, variance_pct, status}]
  trends: [{period, planned_revenue, actual_revenue, planned_cost, actual_cost}]
  variance_alerts: [{metric, planned, actual, severity, recommendation}]
  assumption_freshness: [{assumption, age_days, status: "fresh"|"aging"|"stale"}]
  market_watch: [{type, title, date, impact, source}]
  ai_recommendations: [{id, text, priority, action}]
```

## Action Center (S05)

```
GET /api/v2/actions
Response:
  items: [{
    id, type, study_id, study_name, title, description,
    urgency: "high"|"medium"|"low", created_at,
    actions: [{label, action_url}]
  }]
  counts: {approvals: N, evidence_reviews: N, alerts: N, total: N}
```
