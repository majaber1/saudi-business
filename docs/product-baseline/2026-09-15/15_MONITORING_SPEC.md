# 15 — Continuous Business Intelligence / Monitoring Specification

## Module Purpose

Transform the workspace from a one-time evaluation tool into a persistent business intelligence system. After launch, monitor actual performance against projections, track market changes, detect stale assumptions, and surface AI-powered recommendations.

## Entry Conditions

- Study must have a GO or GO_WITH_CONDITIONS decision
- Business must be in "launched" or "operating" state (user-confirmed)
- Financial baseline exists for comparison

## What Gets Monitored

### 1. Financial Performance (Actual vs Plan)

| Metric | Source | Frequency |
|--------|--------|-----------|
| Revenue | User input / POS integration (future) | Monthly |
| Costs by category | User input / accounting integration (future) | Monthly |
| Net profit | Computed | Monthly |
| Cash position | User input | Monthly |
| Customer count | User input / POS (future) | Monthly |
| Average ticket | User input / POS (future) | Monthly |

### 2. Market & Competition

| Signal | Source | Frequency |
|--------|--------|-----------|
| Competitor openings/closings | Web search, maps, news | Weekly |
| Competitor pricing changes | Web search, user report | Monthly |
| Market size/demand changes | Industry reports, search trends | Monthly |
| New entrants | Business registry, news | Weekly |

### 3. Assumption Freshness

Every evidence item has an age. The system tracks:
- **Fresh** (< 3 months): Evidence is current
- **Aging** (3-6 months): May need refresh
- **Stale** (> 6 months): Should be re-researched

Critical assumptions (high decision impact) have tighter thresholds.

### 4. External Signals

| Signal | Source | Frequency |
|--------|--------|-----------|
| Regulatory changes | Government, news | As detected |
| Funding program updates | Monsha'at, SDB, banks | Weekly |
| Economic indicators | GASTAT, central bank | Monthly |
| Sector trends | Industry reports | Monthly |

## Alert System

### Alert Types

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| **Revenue below plan** | Actual < Plan by >15% for 2+ months | High | Review pricing, demand, marketing |
| **Cost overrun** | Actual > Plan by >10% for any category | Medium | Review cost category, renegotiate |
| **Competitor threat** | Major competitor opens nearby or prices aggressively | Medium | Competitive analysis refresh |
| **Assumption stale** | Critical evidence item > 6 months old | Medium | Re-research |
| **Opportunity detected** | High-score opportunity matching user profile | Low | Review in Opportunity Radar |
| **Break-even at risk** | Projected break-even extended >30% from original | High | Review financials, simulate alternatives |
| **Funding signal** | New relevant funding program available | Low | Review in Funding Readiness |

### Alert Processing
1. System detects trigger condition
2. AI assesses severity and generates recommendation
3. Alert appears in Action Center + Monitoring Dashboard
4. User acknowledges and acts (or dismisses with reason)
5. Resolution tracked

### Alert Notification Preferences (Settings)
- In-app notification (always)
- Email digest (daily/weekly, configurable)
- Push notification for High severity (future, mobile app)

## Dashboard Layout

### Performance Section
```
┌─────────────────────────────────────────────┐
│ Revenue (Monthly)          Actual vs Plan   │
│ ┌─────────────────────────────────────────┐ │
│ │ [Line chart: Plan line + Actual line]   │ │
│ │ [Variance band highlighted]             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Sep 2026:  Plan: 85k SAR  Actual: 72k SAR  │
│ Variance: -15% ⚠                           │
└─────────────────────────────────────────────┘
```

### KPI Tiles
```
Revenue    │  Costs     │  Profit    │  Customers │ Avg Ticket
72k SAR    │  58k SAR   │  14k SAR   │  420       │ 28 SAR
-15% ▼     │  +3% ▲     │  -42% ▼    │  -12% ▼    │ -3% ▼
vs plan    │  vs plan   │  vs plan   │  vs plan   │ vs plan
```

### Assumption Freshness Tracker
```
┌──────────────────────────────────────┐
│ Assumption Freshness                 │
│                                      │
│ ● Rent benchmark      Fresh  (2mo)  │
│ ● Competitor count     Aging  (4mo)  │
│ ● Market demand        Stale  (7mo)  │
│ ● Labor cost           Fresh  (1mo)  │
│ ● COGS benchmark       Aging  (5mo)  │
│                                      │
│ [Refresh Stale Items]                │
└──────────────────────────────────────┘
```

## AI Recommendations Engine

The Monitoring Agent generates actionable recommendations:

```
Based on 3 months of actual data:

1. Revenue is consistently 15% below base case projection.
   → Consider: price adjustment simulation, marketing increase,
     or demand re-research in current location.

2. Competitor "Barn's" opened a new branch 500m from your location.
   → Consider: competitive positioning review, differentiation strategy.

3. Your rent assumption (5,983 SAR) was estimated 7 months ago.
   → Consider: re-validating with current market rates.
```

Each recommendation links to the relevant module: Simulator, Feasibility (re-research), or Evidence Center.

## Data Input

### Manual Input (MVP)
- Monthly data entry form: revenue, costs by category, customer count
- Simplified: "Enter your key numbers for [month]"
- Guided: shows which fields map to which plan items

### Integrated Input (Future)
- POS system integration (revenue, transactions, tickets)
- Accounting software integration (costs)
- Bank feed integration (cash position)
- Automated reconciliation with plan categories

## Persistence

- All actual data stored as time series
- Plan baseline preserved (immutable)
- Alert history retained
- AI recommendations logged with resolution status
- Assumption freshness updated automatically

## Empty State

"Your business is launched! Start entering monthly actuals to track performance against your plan. [Enter first month's data]"

With explanation: "Monitoring helps you compare real performance to your feasibility projections and alerts you when market conditions change."

## Error/Degraded State

- No data entered for 2+ months: "Your monitoring data is behind. Enter actuals for [months] to keep insights current."
- External source unavailable: "Some market monitoring sources are temporarily unavailable. Financial tracking continues normally."

## Mobile Behavior

- KPI tiles in 2-column grid
- Charts simplified (no hover detail)
- Alert list scrollable
- Data entry available (simplified form)
- Recommendations as notification-style cards
