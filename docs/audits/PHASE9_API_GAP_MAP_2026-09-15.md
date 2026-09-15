# Phase 9 API Gap Map (P5)

**Date**: 2026-09-15
**Gate**: P5 — API Baseline Confirmation
**Status**: PASS — API BASELINE CONFIRMED. Implementation gaps deferred to Phase 9.

---

## Summary

The current backend has 39 API router files with extensive coverage of auth, evidence, financial, decision, funding, and opportunity domains. The API baseline is confirmed as sound — gaps are implementation work for Phase 9, not architectural failures.

---

## Gap Classification

### A) Reuse Existing API Directly (6 screens)

These MVP screens can use current backend APIs with no changes.

| MVP Screen | Current API | Notes |
|------------|-------------|-------|
| S01 Login | `POST /api/auth/login`, `POST /api/auth/token` | Ready |
| S02 Register | `POST /api/auth/register` | Ready |
| S12 Financials | `GET/POST /api/financial/*`, `GET/POST /api/studies/{id}/assumptions/*`, `GET /api/scenarios/*` | Comprehensive financial APIs exist |
| S13 Evidence | `GET/POST /api/evidence/*`, `GET /api/extracted-facts/*` | Evidence CRUD, classification, provenance |
| S15 Decision | `GET/POST /api/decision/*` | Decision tree, recommendation, owner approval gate |
| S16 Evidence Detail | `GET /api/evidence/{id}` | Individual evidence item endpoints |

### B) Add Aggregation/Composition Endpoint (7 screens)

These screens need a new endpoint that composes data from existing services.

| MVP Screen | New Endpoint | Composed From | Effort |
|------------|-------------|---------------|--------|
| S04 Command Center | `GET /api/workspace/dashboard` | `projects.py` (list) + `evidence.py` (counts) + `decision.py` (pending) + AI insight | Medium |
| S05 Action Center | `GET /api/workspace/actions` | `decision.py` (pending decisions across projects) + notification aggregation | Small |
| S04a My Businesses | `GET /api/workspace/businesses` | `projects.py` (list) + evidence coverage per project + latest decision per project | Small |
| S04b Business Home | `GET /api/workspace/businesses/{bid}` | `projects.py` (detail) + `feasibility.py` (studies) + `evidence.py` (health) + `decision.py` (latest) | Medium |
| S07 Overview | `GET /api/workspace/businesses/{bid}/studies/{sid}/overview` | `feasibility.py` + `financial.py` + `evidence.py` + `decision.py` (summary) | Medium |
| S14 Risks | `GET /api/workspace/businesses/{bid}/studies/{sid}/risks` | `scenarios.py` (sensitivity) + risk extraction from study payload | Small |
| S40 Profile | `GET/PUT /api/settings/profile` | `auth.py` (user) + new workspace preference fields | Small |

### C) Extend Existing Contract (4 screens)

These screens need minor extensions to existing API endpoints.

| MVP Screen | Existing API | Extension Needed | Effort |
|------------|-------------|-----------------|--------|
| S03 Onboarding | `POST /api/projects`, `PUT /api/studies/{id}/business-profile` | Add wizard-flow endpoint that chains project creation + profile + archetype selection in one call | Small |
| S06 Creation Wizard | `POST /api/v2/studies`, `POST /api/projects` | Unified creation endpoint: create project (workspace) + study + trigger archetype classification | Small |
| S08 Market | `GET /api/v2/studies/{id}` | Extract market dimension from study `profile_json` / research context into dedicated response shape | Small |
| S09 Competitors | `GET /api/v2/studies/{id}` | Extract competitor data from study payload into dedicated response | Small |

### D) New Endpoint Required (3 screens)

| MVP Screen | New Endpoint | Description | Effort |
|------------|-------------|-------------|--------|
| S10 Location | `GET /api/workspace/businesses/{bid}/studies/{sid}/location` | Location analysis view: map data, demographics, rent benchmarks from evidence | Medium |
| S11 Operations | `GET /api/workspace/businesses/{bid}/studies/{sid}/operations` | Operating model view: staffing, hours, supply chain, licensing from assumptions/evidence | Medium |
| S42 Language | `GET/PUT /api/settings/language` | Language/regional preference storage and retrieval | Small |

---

## Effort Summary

| Category | Screens | Effort |
|----------|---------|--------|
| A — Reuse directly | 6 | None |
| B — Aggregation endpoint | 7 | 4 Medium, 3 Small |
| C — Extend existing | 4 | 4 Small |
| D — New endpoint | 3 | 2 Medium, 1 Small |
| **Total** | **20** | **6 Medium, 8 Small** |

---

## API Route Restructuring Note

The approved baseline uses workspace-centric routes:
```
/api/workspace/businesses/{bid}/studies/{sid}/...
```

Current APIs use:
```
/api/projects/{id}/...
/api/studies/{id}/...
/api/v2/studies/{id}/...
```

**Recommendation**: Add new workspace-prefixed routes that delegate to existing service layer. Do NOT remove existing routes in Phase 9 — deprecate them after workspace routes are stable. This avoids breaking existing frontend code during the transition.

---

## Existing API Assets (Not in MVP but Available)

These backend APIs exist and support post-Phase-9 modules:

| API | Router | Post-MVP Module |
|-----|--------|----------------|
| Funding readiness | `funding_readiness.py` | Phase 9B |
| Funding matching | `funding_matching.py` | Phase 9B |
| Funding programs | `funding_programs.py` | Phase 9B |
| Funding gap | `funding_gap.py` | Phase 9B |
| Opportunity matching | `opportunity_matching.py` | Phase 9C |
| Verified opportunities | `verified_opportunities.py` | Phase 9C |
| Scenarios | `scenarios.py` | Phase 9A |
| Launch workspace | `launch.py` | Post-decision |
| Growth workspace | `growth.py` | Phase 10+ |
| Validation | `validation.py` | Quality gates |

---

## P5 Gate Verdict

**PASS — API BASELINE CONFIRMED**

- 6/20 screens can reuse existing APIs directly
- 14/20 need composition, extension, or new endpoints — all buildable on top of existing service layer
- No architectural blockers
- Implementation gaps are Phase 9 work items, not baseline failures
