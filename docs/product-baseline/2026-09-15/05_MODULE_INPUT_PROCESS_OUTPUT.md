# 05 — Module Input → Process → Output Matrix

## Module 1: Business Command Center

**INPUT**: All Business Workspaces (first-class entities), their studies, decisions, evidence, monitoring data, opportunities, and alerts for the authenticated user/organization

**AI / SYSTEM PROCESSING**:
- Aggregate portfolio health scores
- Surface pending decisions (Action Center)
- Rank risks by severity across businesses
- Identify top opportunities from Radar
- Compute funding readiness per business
- Generate AI insight summaries

**OUTPUT**:
- Portfolio summary cards (per Business Workspace: status, health, last activity)
- Decision count badge (pending owner actions)
- Top 3 risks across portfolio
- Top 3 opportunities
- Funding readiness status per business
- AI insight feed (recent findings, alerts, recommendations)
- Quick actions: New Study, Continue Study, Review Decision

**USER DECISION**: Prioritize which business/action to focus on; act on pending decisions

**NEXT ACTION**: Navigate to specific workspace, decision inbox, or opportunity

---

## Module 2: AI Feasibility Workspace

**INPUT**: Business idea, sector, geography, budget, timeline, owner constraints, user assumptions

**AI / SYSTEM PROCESSING**:
- Business Understanding: parse intent, classify sector, generate information needs
- Research: multi-source retrieval (web, government, maps, industry data)
- Evidence Validation: classify, score, deduplicate, trace provenance
- Gap Recovery: identify missing evidence, run targeted research
- Financial Modeling: evidence → CAPEX, OPEX, revenue (Low/Base/High), break-even, sufficiency
- Risk Assessment: sensitivity analysis, risk register
- Decision: apply decision tree → recommendation

**OUTPUT**:
- Investment requirement (range)
- Revenue scenarios (Low/Base/High)
- Break-even / payback period
- Budget sufficiency assessment
- Evidence coverage score
- Confidence level
- Risk register with mitigations
- AI recommendation: GO / GO_WITH_CONDITIONS / DEFER / NO_GO
- Conditions (if applicable)

**USER DECISION**: Approve / Override / Request More Research

**NEXT ACTION**: Funding Readiness / Simulation / Reports / Archive

---

## Module 3: Evidence Intelligence Center

**INPUT**: All evidence items from research, user inputs, external sources

**AI / SYSTEM PROCESSING**:
- Classification (VERIFIED_FACT / SYSTEM_ESTIMATE / USER_ASSUMPTION / UNKNOWN)
- Confidence scoring (0-100)
- Source quality assessment
- Deduplication and normalization
- Provenance chain construction
- Coverage analysis against information needs
- Staleness detection (age-based)

**OUTPUT**:
- Evidence register (filterable, searchable)
- Per-item detail: value/range, class, source(s), date, geography, derivation, confidence, decision impact
- Coverage heatmap (which information needs are satisfied)
- Gap list (UNKNOWN items)
- Source quality distribution
- Conflict detection (contradictory evidence)

**USER DECISION**: Accept/reject/edit evidence items; provide USER_ASSUMPTION; request re-research on specific items

**Evidence Override Governance**:
- No silent reclassification: USER_ASSUMPTION → SYSTEM_ESTIMATE is prohibited; SYSTEM_ESTIMATE → VERIFIED_FACT requires new source evidence
- All class transitions must be logged with justification
- Overrides are explicitly versioned (old value, new value, timestamp, reason)
- Override history is preserved and auditable
- Overrides flow forward to financial model and decision with the override's evidence class

**NEXT ACTION**: Return to workspace; trigger gap recovery; update financial model

---

## Module 4: Funding Readiness

**INPUT**: Approved feasibility decision (GO/GO_WITH_CONDITIONS), financial model, business profile, evidence register

**AI / SYSTEM PROCESSING**:
- Compute funding requirement (CAPEX + Working Capital)
- Assess funding gap (requirement vs available budget)
- Score readiness across dimensions (financial docs, legal, market evidence, management)
- Match against funding programs (government: Monsha'at, SDB; banks; investors)
- Assess eligibility per program
- Identify missing documents/information
- Generate package drafts (investment memo, financial export, pitch data)

**OUTPUT**:
- Readiness score (composite, with per-dimension breakdown)
- Funding requirement and gap
- Matched funding programs with eligibility status
- Document checklist (ready / missing / draft)
- Generated packages: investor package, bank package
- Timeline recommendation

**USER DECISION**: Approve packages; upload missing documents; select programs to apply to; override readiness assessment

**NEXT ACTION**: Submit applications; generate final packages; set follow-up reminders

---

## Module 5: Opportunity Radar

**INPUT**: User profile, active businesses, market signals, sector data, policy/regulatory changes, competitor activity, demand indicators

**AI / SYSTEM PROCESSING**:
- Signal collection from multiple sources (news, government, market data, competitor monitoring)
- Opportunity candidate identification
- Evidence gathering per opportunity
- Market relevance scoring
- Business/user fit assessment
- Opportunity scoring (composite: potential, risk, relevance, timing)
- Action recommendation

**OUTPUT**:
- Signal feed (categorized: market, policy, competitor, demand, sector)
- Opportunity cards with: what changed, why now, evidence, potential, risk, relevance, recommended action
- Opportunity score
- Actions: Create Study / Simulate / Save / Dismiss

**USER DECISION**: Act on opportunity (create study, simulate), save for later, dismiss

**NEXT ACTION**: Create new feasibility study; run simulation against existing business; save to watchlist

---

## Module 6: Business Decision Simulator

**INPUT**: Approved financial baseline (from feasibility), scenario parameters (user-defined changes)

**AI / SYSTEM PROCESSING**:
- Lock baseline from approved study (cannot modify without owner approval)
- Apply parameter changes to financial model
- Compute impact across Low/Base/High scenarios
- Assess risk impact of changes
- Evaluate evidence sensitivity (which evidence assumptions are stressed)
- Generate recommendation per scenario

**OUTPUT**:
- Side-by-side comparison: Current vs Scenario
- Impact metrics: revenue, profit, cash flow, break-even, funding requirement
- Delta display (absolute and percentage)
- Risk impact assessment
- Confidence change
- Evidence sensitivity (which assumptions are stretched beyond evidence)
- AI recommendation per scenario

**USER DECISION**: Save scenario; apply scenario to baseline (requires approval); compare multiple scenarios; dismiss

**NEXT ACTION**: Apply approved scenario; create new study; update funding readiness

---

## Module 7: Continuous Business Intelligence / Monitoring

**INPUT**: Approved baseline, actual performance data (user-entered or integrated), market feeds, competitor monitoring, funding program updates

**AI / SYSTEM PROCESSING**:
- Track actual vs plan (revenue, costs, KPIs)
- Compute variance and trend analysis
- Monitor competitor changes
- Detect assumption staleness (evidence age, market shifts)
- Monitor funding/regulatory signals
- Generate alerts based on threshold rules
- Produce AI recommendations

**OUTPUT**:
- Performance dashboard: actual vs plan with variance
- Trend charts
- Competitor activity feed
- Assumption freshness tracker
- Active alerts (risk, opportunity, staleness)
- AI recommendations: suggested actions, new simulations, updated decisions
- Alert history with resolution status

**USER DECISION**: Acknowledge alerts; trigger simulations; update assumptions; request new research; adjust plans

**NEXT ACTION**: Simulate scenario; update business profile; create new study; generate report

---

## Module 8: Reports & Knowledge Workspace

**INPUT**: All workspace data, evidence, financial models, decisions, monitoring data

**AI / SYSTEM PROCESSING**:
- Compile report from live workspace data
- Inherit evidence provenance and version history
- Format per report type
- Generate executive summaries
- Maintain version control

**OUTPUT**:
- Report types: Full Feasibility Study, Executive Decision Memo, Financial Model Export, Market Intelligence, Competitor Analysis, Location Analysis, Risk Report, Evidence Register, Funding Package, Investor Package
- Version history per report
- Export formats: PDF, spreadsheet, presentation data
- Shareable links (with permission control)

**USER DECISION**: Select report type; customize sections; approve for distribution; share

**NEXT ACTION**: Share with stakeholders; include in funding package; archive

---

## Module 9: Action Center

**INPUT**: All pending actions across modules: study approvals, evidence reviews, gap resolutions, simulation results, monitoring alerts, funding actions

**AI / SYSTEM PROCESSING**:
- Aggregate pending decisions from all modules
- Prioritize by urgency and impact
- Provide context summary per action item
- Track resolution status

**OUTPUT**:
- Prioritized action list
- Per item: context, urgency, impact, recommended action, link to workspace
- Action counts by category
- Resolution history

**USER DECISION**: Act on each item (approve, reject, defer, request more info)

**NEXT ACTION**: Navigate to relevant workspace; complete action; mark resolved
