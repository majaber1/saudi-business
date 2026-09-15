# 09 — Screen Specifications

## S04: Business Command Center (Home)

### 1. Business purpose
Portfolio-level executive view. The user's single entry point to understand the state of all their businesses, pending decisions, risks, and opportunities.

### 2. User persona
Entrepreneur (primary), Investor, Advisor

### 3. Inputs
All user's studies, decisions, evidence, monitoring data, opportunities, alerts

### 4. AI processing
- Portfolio health aggregation
- Risk prioritization across businesses
- Opportunity matching
- Insight generation (what changed since last visit)
- Decision urgency scoring

### 5. Primary information hierarchy
1. **Hero section**: Welcome + "What's changed since you were last here" AI summary (1-2 sentences)
2. **Action Center strip**: "[N] decisions need your attention" — clickable
3. **Active Studies grid**: Cards showing each study with status, key metric, evidence coverage
4. **Risk Alerts**: Top 3 risks across portfolio with severity
5. **Opportunities**: Top 3 matched opportunities with relevance score
6. **Funding Readiness**: Per-business readiness status (if applicable)
7. **Recent Activity**: Timeline of AI actions, user decisions, study progress

### 6. Components
- AI Insight Banner (dismissible, context-aware)
- Action Center Strip (count + top items)
- Study Cards (grid, sortable)
- Risk Alert Cards
- Opportunity Preview Cards
- Funding Status Indicators
- Activity Timeline
- Quick Actions: "+ New Business", "+ New Evaluation", "View All Opportunities"

### 7. Evidence/provenance visibility
Study cards show evidence coverage bar (% of information needs satisfied). Risk alerts link to underlying evidence.

### 8. AI-generated insight
Top banner: natural language summary of portfolio state. Each study card: one-line AI insight ("Evidence gap in operating costs", "Ready for decision", "Market conditions changed").

### 9. User actions
- Create new study
- Continue existing study
- Act on Action Center item
- Explore opportunity
- Navigate to any module

### 10. Decision action
Navigate to Action Center for pending approvals

### 11. Next step
Enter specific workspace or act on highest-priority item

### 12. Empty state
First-time user: "Welcome to Saudi Business. Create your first Business Workspace to explore an opportunity." + prominent "New Business" CTA + brief visual explanation of the platform flow.

### 13. Loading state
Skeleton cards for studies grid; "Checking your portfolio..." text

### 14. Partial-evidence state
Study cards show partial coverage indicators. Incomplete studies show "In Progress" badge with current phase.

### 15. Error/recovery state
API error: "Unable to load your dashboard. Retrying..." + retry button. Individual card failure: card shows error state while others load normally.

### 16. Mobile behavior
Single column. Decision inbox strip at top. Study cards stack vertically. Opportunities carousel (horizontal scroll).

### 17. Arabic/English
Full RTL support. Welcome message in selected language. Business names may be mixed language. SAR currency with locale-appropriate formatting.

---

## S04a: My Businesses

### 1. Business purpose
Portfolio list view. Browse all Business Workspaces with status, health, and quick actions.

### 2. User persona
Entrepreneur (primary), Advisor (multi-client)

### 5. Primary information hierarchy
1. **Header**: "My Businesses" + "+ New Business" CTA
2. **Business Cards** (list/grid toggle): Per business: name, sector badge, status (Active/Decided/Archived), health indicator, latest decision, evidence coverage bar, last activity
3. **Sort/Filter**: By status, sector, last activity, decision outcome
4. **Empty state**: "Create your first Business Workspace" + prominent CTA

### 9. User actions
- Create new business
- Open any business workspace
- Filter/sort list

### 12. Empty state
"No businesses yet. Create your first Business Workspace to start evaluating an opportunity." + "New Business" CTA

---

## S04b: Business Home

### 1. Business purpose
Persistent, study-independent home for a single business. Shows business identity, health, latest baseline, studies, evidence health, and recommended next actions.

### 2. User persona
Entrepreneur (primary), Investor (shared view)

### 5. Primary information hierarchy
1. **Business Profile Header**: Name, sector, location, status badge
2. **Health & Status Summary**: Overall workspace health
3. **Latest Approved Baseline**: Key financials from most recent approved study
4. **Studies / Evaluations**: List of all studies for this business with status
5. **Latest Decision**: Outcome, date, conditions
6. **Evidence Health**: Coverage, freshness, gap count
7. **Simulations**: Recent/saved scenarios (if Phase 9A+)
8. **Funding Status**: Readiness, gap, matched programs (if Phase 9B+)
9. **Monitoring Status**: Actual vs plan, active alerts (if Phase 10+)
10. **Recent Activity Timeline**: Chronological log of actions
11. **Recommended Next Action**: AI-suggested next step

### 9. User actions
- Start new evaluation
- Open existing study
- View evidence register
- Navigate to simulator / funding / monitoring (when available)

### 12. Empty state
Business just created: "Start your first evaluation for [business name]." + "New Evaluation" CTA

---

## S07: Workspace — Overview

### 1. Business purpose
Executive summary of a single business study: investment requirement, revenue potential, break-even, budget assessment, evidence strength, AI recommendation, next steps. The "one-page answer" for the study.

### 2. User persona
Entrepreneur, Investor

### 3. Inputs
Complete study data: profile, evidence, financial model, risks, decision

### 4. AI processing
- Aggregate key metrics from financial model
- Synthesize evidence coverage
- Generate executive summary
- Produce recommendation with conditions
- Identify top risks and next steps

### 5. Primary information hierarchy
1. **Header**: Business name, sector badge, location, status badge (Draft/In Progress/Decision Ready/Decided), last updated
2. **Key Metrics Row**: Investment Required (range) | Break-even (range) | Budget Assessment (sufficient/insufficient/conditional)
3. **Two-column body**:
   - Left: Revenue Scenarios (Low/Base/High bars), Evidence Summary (counts by class), Competitor Highlights (top 3), Location Insights (map thumbnail + key facts)
   - Right: AI Decision Summary card (recommendation + key reasons + conditions + CTA "View Full Study"), Main Risks (top 3), Next Steps checklist
4. **Bottom**: "Explore Next" module links (Funding Readiness, Opportunity Radar, Decision Simulator)

### 6. Components
- Study Header (name, badges, actions: Share, Export Report)
- Tab Bar (Overview active)
- Metric Tiles (3-column) with evidence class icons
- Revenue Scenario Bars
- Evidence Summary Counter (4 class counts)
- Competitor Preview Cards (3 max)
- Location Map Thumbnail + Facts
- AI Decision Card (prominent, green/yellow/orange/red by recommendation)
- Risk Cards (3 max)
- Next Steps Checklist (actionable items)
- Module Link Cards (Funding, Opportunity, Simulator)

### 7. Evidence/provenance visibility
Every metric tile shows evidence class icon. Revenue bars show confidence band. Evidence Summary is clickable → Evidence tab. Each competitor/location card links to detail.

### 8. AI-generated insight
Decision card: 2-3 sentence recommendation with reasoning. Per-metric: one-line provenance note on hover.

### 9. User actions
Export Report, Share Study, Navigate to any tab, Accept/Override Decision, Create Simulation

### 10. Decision action
"View Decision" → Decision tab where owner can approve

### 11. Next step
Depends on study phase: if research in progress → wait/review evidence; if decision ready → review and decide; if decided → funding/simulation

### 12. Empty state
Study just created: "AI is starting research for [business name]. You'll see results as they come in." + animated progress indicator showing current research phase

### 13. Loading state
Skeleton layout matching final structure. "Loading study workspace..."

### 14. Partial-evidence state
Metric tiles show "Pending" for uncalculated values. Revenue scenarios show available scenarios with UNKNOWN marked. Evidence summary shows actual counts including UNKNOWNs.

### 15. Error/recovery state
Study data error: "Unable to load study. Your work is saved." + retry. Individual section error: show error in that section only.

### 16. Mobile behavior
Single column. Key metrics stack vertically. AI Decision Card stays prominent. Competitor/Location become horizontal scroll.

### 17. Arabic/English
Full RTL. Business name in original language. Financial figures in SAR. Date format per user preference.

---

## S08-S11: Workspace Tabs (Market, Competitors, Location, Operations)

### Shared specification pattern:

**Business purpose**: Deep dive into a specific analysis dimension with full evidence visibility

**Information hierarchy per tab**:

**Market (S08)**:
1. Market Size & Demand (with evidence badges)
2. Target Customer Segments
3. Market Trends & Growth Indicators
4. Demand Drivers
5. Regulatory Environment
6. Evidence coverage for market dimension

**Competitors (S09)**:
1. Competitive Landscape Summary (count, density, positioning map)
2. Competitor Cards (name, type, location, differentiators, evidence source)
3. Competitive Positioning (where this business fits)
4. Competitive Advantage / Differentiation Assessment
5. Evidence coverage for competitor dimension

**Location (S10)**:
1. Location Analysis Summary
2. Map View (selected area, competitors, POIs)
3. Demographics & Traffic Data
4. Rent / Cost Comparison (area benchmarks)
5. Location Score (composite with evidence breakdown)
6. Evidence coverage for location dimension

**Operations (S11)**:
1. Operating Model Summary
2. Staffing Requirements (headcount, costs, regulations)
3. Operating Hours & Capacity
4. Supply Chain / COGS Breakdown
5. Licensing & Regulatory Requirements
6. Evidence coverage for operations dimension

**Common elements across all tabs**:
- Each data point shows evidence class badge inline
- Click any evidence badge → Evidence Detail Panel
- "Research Status" indicator showing if AI is still gathering data
- "Request More Research" button for specific topics
- User can add USER_ASSUMPTION for any gap
- Evidence coverage progress bar for this dimension

**Empty state**: "AI is researching [dimension]. Results will appear as they're validated."
**Partial state**: Show available evidence; UNKNOWN items marked with "Not yet determined" + option to provide user assumption or request research
**Error state**: Per-section error handling; other sections remain functional

---

## S12: Workspace — Financials

### 1. Business purpose
Complete financial picture: investment required, revenue model, operating costs, cash flow, break-even, budget sufficiency — all evidence-traced

### 5. Primary information hierarchy
1. **Investment Requirement**: CAPEX breakdown + Working Capital (range, evidence-linked)
2. **Revenue Model**: Low/Base/High annual revenue with driver breakdown (e.g., transactions × ticket × days)
3. **Operating Costs (OPEX)**: Category breakdown (rent, labor, COGS, utilities, marketing, other) with evidence class per item
4. **Cash Flow Projection**: Monthly chart (first 12-36 months) with scenario bands
5. **Break-even Analysis**: Time to break-even (months) with confidence band; "Not calculable" if critical inputs UNKNOWN
6. **Budget Sufficiency**: User's stated budget vs required investment; GO/CAUTION/INSUFFICIENT with conditions
7. **Sensitivity Analysis**: Tornado chart showing which inputs have highest impact on outcomes

### Key components
- Financial Summary Tiles (Investment, Revenue, OPEX, Break-even — each with evidence class)
- Revenue Driver Table (per assumption with evidence badge)
- OPEX Breakdown Table (per category, Low/Base/High, evidence class)
- Cash Flow Chart (interactive, scenario toggle)
- Break-even Timeline (visual with confidence band)
- Budget Assessment Card
- Sensitivity Tornado Chart
- "All assumptions" expandable table (every model input with evidence link)

### Evidence/provenance visibility
Critical: every financial input shows evidence badge. Financial summary section shows "Based on X verified facts, Y estimates, Z unknowns". Any UNKNOWN input that makes a calculation impossible shows explicit "Requires: [input]" message.

---

## S13: Workspace — Evidence

### 1. Business purpose
Trust layer. Browse, filter, inspect all evidence for this study. Understand what's known, estimated, assumed, and unknown.

### 5. Primary information hierarchy
1. **Coverage Heatmap**: Grid of information needs vs evidence status (green/yellow/orange/red)
2. **Evidence Summary Bar**: Counts by class (Verified/Estimate/Assumption/Unknown)
3. **Evidence Register Table**: Sortable, filterable list of all evidence items
   - Columns: Item, Value/Range, Class, Source, Date, Confidence, Impact
4. **Gap Highlight Section**: UNKNOWN items that affect decisions
5. **Actions**: Add User Assumption, Request Research, Override Classification

### Evidence detail (S16 — panel/modal):
- Full value with range
- Classification with explanation
- Source(s): name, URL, access date
- Observation count (if multiple sources)
- Geography relevance
- Temporal relevance
- Derivation chain (how the system arrived at this value)
- Confidence score with explanation
- Decision impact (which outputs depend on this)
- Edit/Override option (becomes USER_ASSUMPTION if user modifies)
- History (changes to this evidence item over time)

---

## S15: Workspace — Decision

### 1. Business purpose
The owner decision screen. AI presents its recommendation with full reasoning; owner makes the final call.

### 5. Primary information hierarchy
1. **AI Recommendation Banner**: Large, prominent — GO (green) / GO_WITH_CONDITIONS (yellow) / DEFER (orange) / NO_GO (red)
2. **Structured Decision Rationale**: How the AI reached the recommendation (evidence sufficient? → financially viable? → risks acceptable?)
3. **Conditions** (if GO_WITH_CONDITIONS): Numbered list of specific conditions that must be addressed
4. **Evidence Coverage at Decision**: Summary of evidence strength at this point
5. **Key Financial Metrics**: Investment, Revenue (base), Break-even — with confidence
6. **Key Risks Acknowledged**: Top risks the recommendation accounts for
7. **Owner Action Bar** (sticky bottom): "Approve Recommendation" | "Override: [dropdown: GO/CONDITIONS/DEFER/NO_GO]" | "Request More Research"
8. **Post-Decision: Next Steps**: Actions unlocked by the decision (Funding, Simulation, Reports)

### Decision action
Owner clicks Approve or Override. Override requires a reason (free text). Both are logged with timestamp and create an immutable decision record.

### Post-decision state
Decision banner shows "Decided: [outcome] by [owner] on [date]". Next steps become active. "Change Decision" available but flagged as creating a new decision version.

---

## S20: Funding Dashboard

### 1. Business purpose
Post-decision funding preparation: understand how ready you are, what's missing, and which programs match.

### 5. Primary information hierarchy
1. **Readiness Score**: Composite score (0-100) with dimensional breakdown (Financial Docs, Legal, Market Evidence, Management, Track Record)
2. **Funding Requirement**: Total needed, available, gap
3. **Funding Gap Visualization**: Bar showing available vs needed with gap highlighted
4. **Missing Items**: Priority-ordered list of what's needed to improve readiness
5. **Matched Programs**: Government (Monsha'at, SDB), Bank, Investor matches with eligibility %
6. **Package Status**: Investor Package / Bank Package — generation status
7. **Timeline**: Recommended funding timeline with milestones

---

## S25: Opportunity Radar Feed

### 1. Business purpose
AI-powered opportunity discovery. What's happening in the market that the user should know about?

### 5. Primary information hierarchy
1. **Signal Filter Bar**: All | Market | Policy | Competitor | Demand | Sector
2. **Opportunity Cards** (scrollable feed):
   - Signal type badge
   - Title: What changed / what's the opportunity
   - "Why Now" context (1-2 sentences)
   - Evidence count and confidence
   - Potential score (Low/Medium/High)
   - Risk level
   - Relevance to user/existing businesses
   - Actions: Create Study | Simulate | Save | Dismiss
3. **Saved Opportunities sidebar/section**

---

## S28: Simulator Home

### 1. Business purpose
What-if analysis workspace. Test how changes affect financial outcomes without modifying the approved baseline.

### 5. Primary information hierarchy
1. **Baseline Summary**: Locked metrics from approved study (Investment, Revenue, Break-even)
2. **Scenario Builder**: Parameter sliders/inputs (price, rent, staffing, capacity, COGS, etc.)
3. **Impact Preview**: Live comparison as parameters change
   - Current | Scenario | Delta columns
   - Revenue, Profit, Cash Flow, Break-even rows
   - Low/Base/High for each
4. **Risk Impact**: How the scenario changes risk profile
5. **Evidence Sensitivity**: Warning when scenario pushes beyond evidence-supported ranges
6. **Recommendation**: AI assessment of the scenario
7. **Actions**: Save Scenario | Compare | Apply (requires owner approval) | Reset

---

## S32: Monitoring Dashboard

### 1. Business purpose
Post-launch performance tracking. Are we on plan? What's changed in the market?

### 5. Primary information hierarchy
1. **Performance Header**: Key KPIs — Actual vs Plan with variance indicators
2. **Trend Charts**: Revenue, Costs, Profit — actual vs projected over time
3. **Variance Alerts**: Items significantly off-plan (positive or negative)
4. **Assumption Freshness**: Which original assumptions are aging / becoming stale
5. **Market Watch**: Competitor changes, market shifts, new entrants
6. **AI Recommendations**: Suggested actions, new simulations, decision reviews
7. **Alert History**: Past alerts with resolution status
