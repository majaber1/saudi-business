# 0001 — Evolution from Study Workspace to Business Workspace

Status: PROPOSED
Date: 2026-09-15

## Problem

Saudi Business is an AI Business Operating System, not a Feasibility Report
Generator. The current architecture centers on the Study Workspace as the
primary user container. All modules (Funding Readiness, Opportunity Radar,
Decision Simulator, Growth/Monitoring, Reports) are accessed through a study
context. A user without an active study has no entry point to these
capabilities.

The product must evolve so that the **Business Workspace** is the primary
container, with the Feasibility Study as one peer module among several.

## Current Architecture

The master architecture defines:

```
Project (persistence entity)
  |
  +-- FeasibilityStudy (1:N)
        |
        +-- BusinessProfile snapshot
        +-- Assumptions
        +-- Evidence / Claims
        +-- Financial Results
        +-- Decision
        +-- Report
```

`StudyState` (Pydantic model in `ai_engine/models/study_state.py`) is the
universal data carrier for the AI engine. It holds:

- `ProjectProfile` (archetype, sector, stage, language)
- `assumptions: List[Assumption]`
- `evidence: List[Evidence]`
- `financial_result: Dict`
- `risk_assessment: Dict`
- `decision: Dict`
- `messages` (LangGraph conversation)
- Phase routing state

The LangGraph orchestrator (`ai_engine/orchestrator.py`) routes through
6 agents (discovery, research, evidence, assumptions, financial, risk,
decision) based on `StudyState.phase`.

Other backend services already exist as independent modules:

- `backend/app/api/funding_readiness.py` — reads from study data
- `backend/app/api/scenarios.py` — reads from study assumptions
- `backend/app/api/growth.py` — Growth OS with own workspace model
- `backend/app/api/opportunities.py` — independent catalog
- `backend/app/api/reports.py` — reads from study/financial results
- `backend/app/services/reporting_v2.py` — 19-section report generator

The frontend Command Center (`apps/web/app/page.tsx`) presents 8 module
cards, but all active modules route through `/businesses` → study context.

## Reason Change Is Needed

1. **Product identity**: The Business Workspace is the product. Users manage
   a business, not a study. The study is one tool within that workspace.

2. **Module independence**: Funding Readiness, Monitoring, and Opportunity
   Radar should function even when no study is in progress. A business that
   has completed its feasibility study still needs monitoring and funding.

3. **State boundary**: `StudyState` is accumulating responsibilities. If
   future modules (Funding, Monitoring, Simulator) attach their state to
   `StudyState`, it becomes an unmaintainable monolith. Each module needs
   its own state container at the Business Workspace level.

4. **Navigation**: Users should navigate Business Workspace → Module tabs,
   not Command Center → Business → Study → (hope the module is accessible).

## Proposed Change

### 1. Business Workspace as Primary Container

```
Business Workspace (/businesses/{id})
  |
  +-- Overview / Business Command Center (tab)
  |
  +-- Study Module (tab)
  |     +-- Research
  |     +-- Evidence
  |     +-- Assumptions
  |     +-- Financial Model
  |     +-- Decision
  |     +-- Report
  |
  +-- Funding Readiness Module (tab)
  |
  +-- Opportunity Radar Module (tab)
  |
  +-- Business Decision Simulator Module (tab)
  |
  +-- Monitoring / Growth OS Module (tab)
  |
  +-- Reports Workspace Module (tab)
  |
  +-- Evidence Intelligence Module (tab)
```

### 2. State Boundary Rule

**StudyState remains the foundation for the Study module ONLY.**

StudyState owns:
- Evidence and research results
- Assumptions
- Financial calculations
- Decision output
- Phase routing for the AI engine pipeline

StudyState MUST NOT contain:
- `FundingState` — lives at Business Workspace level
- `MonitoringState` — lives at Business Workspace level
- `OpportunityState` — lives at Business Workspace level
- `SimulatorState` — lives at Business Workspace level

Each future module defines its own state model, attached to the Business
Workspace (backed by `Project`) rather than to `FeasibilityStudy`.

### 3. Persistence Mapping

```
Project (Business Workspace)
  |
  +-- FeasibilityStudy (Study Module)
  |     +-- StudyAssumption
  |     +-- EvidenceClaim
  |     +-- FinancialResult
  |     +-- Decision
  |
  +-- FundingReadinessEvaluation (Funding Module)
  |     +-- references study data, does not own it
  |
  +-- ScenarioSet (Simulator Module)
  |     +-- Scenario snapshots
  |
  +-- GrowthWorkspace (Monitoring Module)
  |     +-- HealthSnapshot
  |     +-- TrendRecord
  |     +-- GrowthDecision
  |
  +-- OpportunityMatch (Radar Module)
  |     +-- matched opportunities for this business
  |
  +-- Report (Reports Module)
        +-- generated report history
```

### 4. Frontend Navigation

`/businesses/{id}` becomes the Business Workspace with a tab/sidebar
navigation system. Each module is a tab or sub-route:

```
/businesses/{id}                    -> Overview
/businesses/{id}/study/{studyId}    -> Study Module (existing)
/businesses/{id}/funding            -> Funding Readiness
/businesses/{id}/opportunities      -> Opportunity Radar
/businesses/{id}/simulator          -> Decision Simulator
/businesses/{id}/monitoring         -> Growth / Monitoring
/businesses/{id}/reports            -> Reports Workspace
/businesses/{id}/evidence           -> Evidence Intelligence
```

### 5. AI Engine Scope

The LangGraph orchestrator and its 6 agents remain scoped to the Study
Module. They operate on `StudyState` and produce study-phase outputs.

Future modules that need AI capabilities define their own agents and
orchestrators. They MAY read from study outputs (financial results,
evidence) but MUST NOT write to `StudyState`.

### 6. Cross-Module Data Flow

Modules may read from other modules' outputs:

- Funding Readiness reads financial results from the latest study
- Opportunity Radar reads business profile from the workspace
- Monitoring reads assumptions and actuals
- Reports reads from all modules

This is achieved through service-layer read functions, not by sharing
state objects. Each module's service defines what it exports and what it
imports.

## Alternatives

### A. Expand StudyState to hold everything

Rejected. This creates a monolithic state object that grows with every
module. Testing, serialization, and agent scope become unmanageable.
Every agent receives the entire platform state even when it only needs
assumptions.

### B. Create a new top-level entity replacing Project

Rejected for Phase 9. The `Project` entity already maps correctly to
Business Workspace. Renaming adds migration risk with no user-facing
benefit. The frontend can display "Business Workspace" while the
persistence layer uses `Project`.

### C. Keep Study as the primary container, add modules as study sub-tabs

Rejected. This forces every module to require an active study. A business
in the monitoring phase (post-launch) should not need to create a new
feasibility study to access Growth OS.

## Data Impact

- No schema changes required for Phase 9 merge.
- Future waves add new tables at the Project level (not Study level).
- Existing `Project → FeasibilityStudy` relationship is preserved.
- Growth OS already has its own workspace model (`GrowthWorkspace`).
- Scenario engine already stores snapshots independently.

## API Impact

- No breaking changes to existing endpoints.
- Future waves add new route prefixes under `/businesses/{id}/`.
- Existing `/studies/{study_id}/funding-readiness` may be aliased to
  `/businesses/{id}/funding` for the new navigation model.
- V2 study engine endpoints remain unchanged.

## Security Impact

- Ownership model unchanged: Business Workspace inherits Project ownership.
- Each module's endpoints continue to verify ownership through
  `owned_study_or_error` or equivalent project-level checks.
- No new auth scopes required.

## Migration Impact

- Additive only for Phase 9 merge. No backfill required.
- Future frontend navigation changes are backward-compatible (old URLs
  can redirect to new tab structure).
- No data migration needed until modules define their own persistence.

## Backward Compatibility

- All existing URLs (`/projects/{id}`, `/projects/{id}/studies/{id}`)
  continue to work.
- The Command Center continues to function as-is.
- API contracts are unchanged.
- The evolution is purely additive in future waves.

## Risks

| Risk | Mitigation |
|------|------------|
| Module proliferation without depth | Each module must have a minimum viable feature set before getting a tab. COMING NEXT modules show as disabled. |
| Cross-module data staleness | Modules read latest data on access, not cached snapshots. Service-layer reads ensure freshness. |
| StudyState scope creep | This ADR establishes the boundary. Code review must enforce: no new fields on StudyState for non-study concerns. |
| Navigation complexity | Tab count is fixed at 8 maximum. Low-activity modules can be collapsed or hidden based on business stage. |
| Frontend rebuild scope | Tab navigation is an incremental addition to `/businesses/{id}`, not a rewrite. Each tab is an independent page component. |

## Technical Debt Watch Items

| Item | Current State | Action Trigger |
|------|---------------|----------------|
| `StudyState` size | 15+ fields, manageable | If any PR adds a field unrelated to the study pipeline, reject it |
| `reporting.py` vs `reporting_v2.py` | Two parallel generators | Deprecate V1 when V2 is wired to all report endpoints |
| `/dashboard` redirect to `/` | Cosmetic URL confusion | Resolve when Business Workspace navigation ships |
| `monitoring.py` name collision | HTTP metrics vs business monitoring | Rename HTTP metrics to `request_metrics.py` when Monitoring module ships |
| Demo mode (`DB_ENABLED=False`) branches | Present in most services | Accept as-is; demo mode is dev-only |

## Future Module Integration Rules

Before adding any capability to the platform:

1. **Classify**: Does this belong to (A) the Study Module or (B) a
   Business Workspace Module?

2. **If Study Module**: The capability uses `StudyState`, is orchestrated
   by the LangGraph pipeline, and produces study-phase outputs.

3. **If Business Workspace Module**: The capability defines its own state
   model, its own API routes under `/businesses/{id}/`, and its own
   service layer. It MAY read from study outputs but MUST NOT write to
   `StudyState`.

4. **If unclear**: Default to Business Workspace Module. It is easier to
   later integrate a standalone module into the study pipeline than to
   extract a tightly coupled feature from `StudyState`.

## Implementation Phases

| Wave | Scope |
|------|-------|
| Phase 9 (current) | Foundation: Study engine, financial model, decision framework, 19-section report. Merge as-is. |
| Wave 2 | Business Workspace tab navigation. Report history. Command Center analytics. Deprecate reporting V1. |
| Wave 3 | Evidence Intelligence as standalone module. Decision Simulator interactive UI. Growth OS frontend. |
| Wave 4 | Funding Readiness workflow. Opportunity Radar personalization. Market feed integration. |
| Wave 5 | Agent observability. Cross-module intelligence. Notification/alert system. |
