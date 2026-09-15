# 13 — Opportunity Radar Specification

## Module Purpose

AI-powered opportunity intelligence that continuously surfaces business opportunities from market, sector, policy, competitor, and demand signals — with evidence, scoring, and actionable next steps.

## Opportunity Discovery Workflow

```
SIGNALS (continuous collection)
    ↓
OPPORTUNITY CANDIDATE (pattern detection)
    ↓
EVIDENCE (supporting data gathered)
    ↓
MARKET RELEVANCE (contextual fit assessment)
    ↓
BUSINESS/USER FIT (relevance to user's profile and businesses)
    ↓
OPPORTUNITY SCORE (composite)
    ↓
RECOMMENDED ACTION (Create Study / Simulate / Save / Dismiss)
```

## Signal Sources

| Signal Type | Sources | Example |
|-------------|---------|---------|
| **Market** | Industry reports, market data, economic indicators | "Saudi F&B market grew 12% YoY" |
| **Policy / Regulatory** | Government announcements, Vision 2030 updates, new regulations | "New Monsha'at program for food manufacturing" |
| **Competitor** | Business registry, news, social media, location data | "Major competitor closed 3 locations in Riyadh" |
| **Demand** | Search trends, consumer data, foot traffic, demographic shifts | "Growing demand for EV charging in Eastern Province" |
| **Sector** | Industry news, trade data, supply chain signals | "Import costs for coffee beans dropped 15%" |
| **Funding** | New funding programs, grant announcements, interest rate changes | "SDB launched new startup loan program at 2%" |

## Signal Processing

### Collection
- Background process (Monitoring Agent feeds Opportunity Radar)
- Frequency: configurable (daily/weekly per signal type)
- Sources: web search, government APIs, market databases, news feeds

### Candidate Identification
AI detects patterns that represent business opportunities:
- Market gap signals (unserved demand + location + timing)
- Cost advantage signals (input cost changes)
- Policy alignment signals (government support for a sector)
- Competitive opening signals (competitor exit/weakness)
- Demand surge signals (trend acceleration)

### Evidence Gathering
For each candidate, Research Agent gathers:
- Supporting data points (minimum 2 independent sources)
- Contradicting signals (if any)
- Temporal relevance (is this still current?)
- Geographic specificity (relevant to user's markets?)

## Opportunity Scoring

### Composite Score (0-100)

> **NOTE**: All scoring weights below are **DRAFT**, **CONFIGURABLE** (system parameters, not hardcoded), and **REQUIRE CALIBRATION** against real usage data before being treated as reliable.

| Dimension | Weight | Assessment |
|-----------|--------|-----------|
| **Potential** | 30% | Market size, growth rate, margin indicators |
| **Timing** | 20% | Why now? Window of opportunity? |
| **Fit** | 20% | Alignment with user's skills, location, budget, existing businesses |
| **Evidence Strength** | 15% | Number and quality of supporting signals |
| **Risk** | 15% | Competitive intensity, regulatory barriers, execution complexity |

### Score Display
- 80-100: "Strong Opportunity" — prominent card, recommended action
- 60-79: "Worth Exploring" — standard card
- 40-59: "Watch" — compact card, save for later
- <40: Not surfaced unless user requests

## Opportunity Card Specification

```
┌─────────────────────────────────────────┐
│ [Signal Badge: Market]     Score: 82    │
│                                         │
│ Specialty Coffee in Eastern Province    │
│                                         │
│ Why Now: Growing professional population│
│ in Dammam with limited premium options. │
│ 3 competitors vs 12 in Riyadh.         │
│                                         │
│ Evidence: 4 verified facts, 2 estimates │
│ Potential: High    Risk: Medium         │
│ Relevance: 85% match to your profile   │
│                                         │
│ [Create Study] [Simulate] [Save] [✕]   │
└─────────────────────────────────────────┘
```

## User Actions Per Opportunity

| Action | What Happens |
|--------|-------------|
| **Create Study** | Pre-populates a new feasibility study with the opportunity's sector, location, and available evidence |
| **Simulate** | Opens Decision Simulator with the opportunity as a scenario against an existing business |
| **Save** | Adds to saved opportunities with optional notes |
| **Dismiss** | Removes from feed with optional reason (not interested / not relevant / already explored) |

## Integration Points

| Integration | Direction | Detail |
|-------------|-----------|--------|
| **Feasibility** | Radar → Feasibility | "Create Study" seeds a new study with pre-gathered evidence |
| **Simulator** | Radar → Simulator | "Simulate" opens what-if against existing business baseline |
| **Monitoring** | Monitoring → Radar | Monitoring signals feed opportunity detection |
| **Funding** | Radar → Funding | Opportunity may include funding program matches |
| **Command Center** | Radar → Home | Top opportunities surfaced on Command Center |

## Personalization

Opportunity relevance considers:
- User's existing businesses (sectors, locations)
- User's stated interests and goals
- Previous study sectors
- Saved/dismissed opportunity patterns
- Budget range
- Geographic preferences

## Feed Management

- **Default sort**: By relevance score (highest first)
- **Filters**: Signal type, sector, location, score range, date
- **Refresh**: Manual + automatic (background)
- **History**: Past opportunities with outcome tracking (did user act? what happened?)
- **Notification**: High-score opportunities trigger Action Center notification

## Empty State

"Opportunity Radar is scanning the Saudi market for opportunities matching your profile. You'll see opportunities here as signals are detected. This may take a few hours for initial setup."

## Error/Degraded State

"Some signal sources are temporarily unavailable. Showing opportunities from available sources. [Details]"
