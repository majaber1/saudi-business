# 04 — End-to-End User Journey

## Primary Journey: Idea to Monitored Business

```
IDEA → PROFILE → PLAN → RESEARCH → EVIDENCE → GAPS → MODEL → DECISION → FUND → LAUNCH → MONITOR → GROW
```

### Stage 1: Business Idea Entry
**Where**: Command Center → "New Evaluation" or Onboarding
**User does**: Describes business idea in natural language or selects sector
**System does**: AI extracts intent, sector classification, geography, preliminary scope; creates a Business Workspace as the first-class entity
**Output**: Draft Business Workspace with business profile
**Decision**: User confirms/edits profile → Proceed
**Failure**: Ambiguous input → AI asks clarifying questions

### Stage 2: Business Profile & Goals
**Where**: Business Workspace creation wizard
**User does**: Confirms business type, location, budget, timeline, constraints, goals
**System does**: Normalizes inputs, identifies domain pack, sets study parameters
**Output**: Complete business profile with constraints
**Decision**: User approves profile → triggers research planning
**Failure**: Missing critical info → wizard highlights required fields

### Stage 3: Information Needs Plan
**Where**: Workspace → auto-generated after profile approval
**User does**: Reviews AI-generated research plan (what needs to be discovered)
**System does**: Business Understanding agent produces categorized information needs based on domain + geography + constraints
**Output**: Research plan: market size, competitors, location data, operating costs, regulations, etc.
**Decision**: User can add/remove research priorities
**Failure**: Unknown domain → generic template + user guidance

### Stage 4: Research & Discovery
**Where**: Workspace → progress indicator, background processing
**User does**: Monitors progress; may be prompted for user-specific knowledge
**System does**: Research agent executes multi-source retrieval: web, government, maps, POI, industry databases, documents
**Output**: Raw observations with source metadata
**Decision**: None (automated); user can pause/redirect
**Failure**: Source unavailable → retry with alternatives; if all fail → mark as gap

### Stage 5: Evidence Classification & Validation
**Where**: Workspace → Evidence tab
**User does**: Reviews evidence items; can override classification; provides USER_ASSUMPTION where prompted
**System does**: Evidence Validation agent classifies each observation (VERIFIED_FACT / SYSTEM_ESTIMATE / USER_ASSUMPTION / UNKNOWN), deduplicates, normalizes, scores confidence, preserves provenance
**Output**: Classified evidence register with confidence scores
**Decision**: User approves/edits evidence items
**Failure**: Low confidence → flagged; conflicting sources → user arbitration

### Stage 6: Coverage Check & Gap Recovery
**Where**: Workspace → Evidence tab → Coverage heatmap
**User does**: Reviews gaps; decides whether to accept UNKNOWN or request more research
**System does**: Identifies information needs not yet covered; runs targeted gap-recovery research
**Output**: Updated evidence with fewer gaps (or explicit UNKNOWN acceptances)
**Decision**: User accepts remaining unknowns or requests another research cycle
**Failure**: Persistent gaps → UNKNOWN remains; affects decision confidence

### Stage 7: Operating Model & Financial Model
**Where**: Workspace → Operations + Financials tabs
**User does**: Reviews AI-built financial model; may override assumptions
**System does**: Financial Modeling agent converts evidence into: CAPEX, OPEX, revenue scenarios (Low/Base/High), working capital, cash flow, break-even, budget sufficiency
**Output**: Complete financial model with evidence traceability
**Decision**: User validates/edits model parameters
**Failure**: Critical UNKNOWN inputs → financial model shows ranges with low confidence; break-even may be "not calculable"

### Stage 8: Risk & Sensitivity Analysis
**Where**: Workspace → Risks tab
**User does**: Reviews risk register and sensitivity analysis
**System does**: Identifies key risks, runs sensitivity on critical assumptions, assesses mitigation options
**Output**: Risk register with severity, likelihood, mitigation; sensitivity charts
**Decision**: User acknowledges risks; may request simulation
**Failure**: Unquantifiable risks → qualitative assessment with explanation

### Stage 9: Decision Recommendation
**Where**: Workspace → Decision tab
**User does**: Reviews AI recommendation and supporting evidence
**System does**: Decision Advisor agent applies decision tree: sufficient evidence? → financially viable? → risks acceptable? → GO / GO_WITH_CONDITIONS / DEFER / NO_GO
**Output**: Recommendation with structured decision rationale, conditions, confidence
**Decision**: **OWNER APPROVAL GATE** — user selects: Accept / Override / Request More Research
**Failure**: Conflicting signals → GO_WITH_CONDITIONS or DEFER with explicit conditions

### Stage 10: Next Actions (Post-Decision)
**Where**: Workspace → Decision tab → Next Steps panel
**User does**: Chooses next action based on decision
**System does**: Generates action options based on decision outcome

| Decision | Available Actions |
|----------|------------------|
| GO | → Funding Readiness / Generate Reports / Start Monitoring |
| GO_WITH_CONDITIONS | → Address conditions / Simulate scenarios / Funding Readiness |
| DEFER | → Set reminder / Save workspace / Continue research later |
| NO_GO | → Archive / Explore alternatives (Opportunity Radar) |

### Stage 11: Funding Readiness (if GO/GO_WITH_CONDITIONS)
**Where**: Funding Readiness module
**User does**: Reviews readiness score, prepares documents, selects funding programs
**System does**: Assesses readiness, identifies gaps, matches programs, generates packages
**Output**: Funding readiness score, complete package, program matches
**Decision**: User approves packages; submits applications
**Failure**: Missing documents → checklist with generation/upload options

### Stage 12: Launch & Monitor (Post-Funding)
**Where**: Monitoring module
**User does**: Enters actual performance data; reviews AI alerts
**System does**: Tracks actual vs plan, monitors market, detects assumption staleness, surfaces risks and opportunities
**Output**: Performance dashboard, alerts, recommendations
**Decision**: User acts on alerts; may trigger new simulations
**Failure**: No data input → prompts user; stale data → staleness warnings

### Stage 13: Simulate & Grow (Ongoing)
**Where**: Decision Simulator + Opportunity Radar
**User does**: Tests scenarios; reviews new opportunities
**System does**: Runs what-if analysis; surfaces market opportunities with evidence
**Output**: Scenario comparisons; opportunity cards with evidence
**Decision**: User applies scenarios; creates new studies from opportunities
**Failure**: Insufficient baseline data → requests monitoring data first

## Secondary Journeys

### Existing Business Owner (no feasibility needed)
Entry → Create Business Workspace → Skip Feasibility → Monitoring → Simulator → Opportunity Radar

This is a first-class entry point, not a workaround. The Business Workspace creation wizard offers "Existing Business" as an explicit option alongside "New Idea." Existing businesses skip feasibility and go directly to Monitoring, Simulator, or Funding modules within their workspace.

### Investor Evaluating Opportunity
Entry → Shared Study → Evidence Review → Financial Review → Decision Review → Funding Package

### Advisor Managing Multiple Clients
Entry → Command Center (multi-business) → Per-business workspace → Cross-portfolio Reports

## Cross-Journey Persistence

Every journey maintains:
- Workspace state (resumable)
- Evidence chain (never lost)
- Decision history (auditable)
- User overrides (tracked)
- Version history (rollback capable)
