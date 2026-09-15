# 03 — Product Sitemap

## Global Navigation (Persistent Sidebar)

```
Saudi Business
├── Home (Business Command Center)
├── My Businesses
│   ├── [Business 1] — Workspace
│   │   ├── Studies
│   │   ├── Evidence
│   │   ├── Financial Models
│   │   ├── Decisions
│   │   ├── Reports
│   │   └── Monitoring
│   ├── [Business 2] — Workspace
│   └── ...
├── New Evaluation (+)
├── Opportunity Radar
├── Simulator
├── Funding
├── Reports
├── Action Center
└── Settings
    ├── Profile & Organization
    ├── Notifications
    ├── Language (AR/EN)
    ├── Integrations
    └── Team & Permissions
```

## Screen Hierarchy

### 1. Business Command Center (`/`)
- Portfolio overview
- Active Business Workspace summary cards
- Action Center strip (pending actions count)
- Risk alerts
- Opportunity highlights
- Funding readiness summary
- Recent simulations
- AI insights feed

### 1a. My Businesses (`/businesses`)
- List/grid of all Business Workspaces
- Per-business: name, sector, status, health, latest decision, evidence coverage
- Quick actions: open workspace, new evaluation
- Sort/filter by status, sector, last activity

### 1b. Business Home (`/businesses/:bid`)
```
Business Workspace Home (persistent, study-independent)
├── Business Profile (name, sector, location, status)
├── Health & Status Summary
├── Latest Approved Baseline (key financials)
├── Studies / Evaluations (list of all studies for this business)
├── Latest Decision (outcome, date, conditions)
├── Evidence Health (coverage, freshness, gaps)
├── Simulations (recent scenarios, saved)
├── Funding Status (readiness, gap, programs)
├── Monitoring Status (actual vs plan, alerts)
├── Reports (generated, available)
├── Recent Activity Timeline
└── Recommended Next Action (AI-suggested)
```

### 2. AI Feasibility Workspace (`/businesses/:bid/studies/:sid`)
```
Study Workspace
├── Overview (executive summary)
├── Market
│   ├── Market size & demand
│   ├── Target segments
│   └── Trends & growth
├── Competitors
│   ├── Competitor map
│   ├── Individual competitor profiles
│   └── Competitive positioning
├── Location
│   ├── Location analysis
│   ├── Map view
│   ├── Rent/cost comparison
│   └── Demographics & traffic
├── Operations
│   ├── Operating model
│   ├── Staffing
│   ├── Hours & capacity
│   └── Supply chain / COGS
├── Financials
│   ├── Investment requirement (CAPEX + Working Capital)
│   ├── Revenue scenarios (Low/Base/High)
│   ├── Operating costs (OPEX)
│   ├── Break-even / payback
│   ├── Cash flow projection
│   └── Budget sufficiency
├── Evidence
│   ├── Evidence register (all items)
│   ├── By classification
│   ├── Coverage heatmap
│   ├── Gaps & unknowns
│   └── Source quality
├── Risks
│   ├── Risk register
│   ├── Sensitivity analysis
│   └── Mitigation recommendations
└── Decision
    ├── AI recommendation
    ├── Conditions (if GO_WITH_CONDITIONS)
    ├── Evidence coverage summary
    ├── Owner action: Approve / Override / Request more research
    └── Next steps
```

### 3. Evidence Intelligence Center (`/businesses/:bid/evidence` + `/evidence`)
```
Evidence Center
├── Business-level evidence register (/businesses/:bid/evidence — all evidence across studies)
├── Study-scoped view (filtered to active study, with indication of reusable Business evidence)
├── Global evidence library (/evidence — cross-business, Phase 9+)
├── Evidence detail view
│   ├── Value/range
│   ├── Classification badge
│   ├── Source(s) with links
│   ├── Observation count
│   ├── Date/recency
│   ├── Geography
│   ├── Derivation chain
│   ├── Confidence score
│   └── Decision impact
├── Filters: by class, source, date, confidence, domain
└── Evidence comparison view
```

### 4. Funding Readiness (`/businesses/:bid/funding`)
```
Funding Readiness
├── Readiness Dashboard
│   ├── Readiness score (composite)
│   ├── Funding requirement
│   ├── Funding gap
│   └── Timeline
├── Document Checklist
│   ├── Required documents
│   ├── Status: ready / missing / draft
│   └── Upload / generate actions
├── Funding Programs
│   ├── Matched programs (government, bank, investor)
│   ├── Eligibility assessment
│   └── Application guidance
├── Investor Package
│   ├── Investment memo
│   ├── Financial model export
│   ├── Pitch deck data
│   └── Generate package action
└── Bank Package
    ├── Bank-ready financials
    ├── Collateral assessment
    └── Generate package action
```

### 5. Opportunity Radar (`/opportunities`)
```
Opportunity Radar
├── Signal Feed
│   ├── Market signals
│   ├── Policy / regulatory signals
│   ├── Competitor signals
│   ├── Demand signals
│   └── Sector signals
├── Opportunity Cards
│   ├── What changed / why now
│   ├── Evidence
│   ├── Potential (scored)
│   ├── Risk
│   ├── Relevance to user
│   └── Actions: Create Study / Simulate / Save / Dismiss
├── Saved Opportunities
└── Opportunity Detail View
```

### 6. Business Decision Simulator (`/businesses/:bid/simulator`)
```
Decision Simulator
├── Baseline (locked from approved study)
├── Scenario Builder
│   ├── Parameter adjustment (price, rent, staff, capacity, etc.)
│   ├── Multi-variable scenarios
│   └── Named scenario save
├── Impact View
│   ├── Current vs Scenario comparison
│   ├── Revenue / Profit / Cash impact
│   ├── Break-even impact
│   ├── Risk impact
│   ├── Confidence change
│   └── Low/Base/High ranges
├── Scenario Library
│   ├── Saved scenarios
│   ├── Compare up to 3
│   └── Recommendation per scenario
└── Apply Scenario (owner approval required)
```

### 7. Continuous Business Intelligence (`/businesses/:bid/monitoring`)
```
Monitoring Dashboard
├── Performance Overview
│   ├── Actual vs Plan (revenue, costs, KPIs)
│   ├── Trend lines
│   └── Variance alerts
├── Market Watch
│   ├── Competitor changes
│   ├── Market shifts
│   └── New entrants
├── Risk Monitor
│   ├── Assumption staleness tracker
│   ├── Evidence freshness
│   └── Active risk alerts
├── AI Recommendations
│   ├── Suggested actions
│   ├── New simulations recommended
│   └── Updated decisions
└── Alert History
```

### 8. Reports & Knowledge (`/reports`)
```
Reports & Knowledge
├── Report Center
│   ├── Generate report (by type)
│   ├── Report history
│   └── Scheduled reports
├── Report Types
│   ├── Full Feasibility Study
│   ├── Executive Decision Memo
│   ├── Financial Model Export
│   ├── Market Intelligence Report
│   ├── Competitor Analysis
│   ├── Location Analysis
│   ├── Risk Report
│   ├── Evidence Register
│   ├── Funding Package
│   └── Investor Package
├── Knowledge Hub
│   ├── Domain knowledge base
│   ├── Industry benchmarks
│   ├── Saudi market data
│   └── Regulatory reference
└── Decision History
    ├── All decisions with timestamps
    ├── Evidence at time of decision
    └── Outcome tracking
```

### 9. Action Center (`/actions`)
```
Action Center
├── Pending Approvals
│   ├── Study decisions awaiting review
│   ├── Evidence requiring user input
│   ├── Gap resolution requests
│   └── Simulation results to approve
├── Notifications
│   ├── AI alerts
│   ├── Risk warnings
│   ├── Opportunity matches
│   └── Monitoring triggers
└── Action History
```

### 10. Authentication & Onboarding
```
Auth
├── Login / Register
├── Onboarding (adaptive wizard)
│   ├── Profile setup
│   ├── Goals & constraints
│   ├── Add Business: Existing Business OR New Idea/Venture
│   │   ├── Existing Business → Business Workspace (may skip feasibility)
│   │   └── New Venture → Business Workspace + optional first Evaluation
│   └── Dashboard introduction
└── Organization setup (multi-user, future)
```
