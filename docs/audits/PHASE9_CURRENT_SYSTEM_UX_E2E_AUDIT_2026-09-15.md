# Phase 9 Current System UX & E2E Audit

**Date**: 2026-09-15
**Auditor**: Automated (Claude session)
**Branch**: `claude/phase9-baseline-and-current-system-audit-20260915`
**Baseline reference**: `docs/product-baseline/2026-09-15/` (21 documents)
**Purpose**: Pre-Phase-9 read-only audit of the current Saudi Business system against the approved product baseline.

---

## 1. Executive Summary

The current Saudi Business system is a working bilingual (Arabic RTL-first) platform with a FastAPI backend and Next.js 16 frontend. It has **596 passing tests** (1 blocked — external GASTAT connector unavailable). The backend health endpoint returns healthy. The frontend serves 25/26 tested routes (1 returns 404). The system has significant backend API coverage but the frontend route architecture and data model require structural changes to match the approved Phase 9 baseline. **No code changes were made during this audit.**

**Overall verdict**: CURRENT_SYSTEM_AUDITED — foundation is sound, structural gaps are well-defined.

---

## 2. Approved Baseline Placement

| Item | Status |
|------|--------|
| Location | `docs/product-baseline/2026-09-15/` |
| Files | 21 documents (00–20) |
| Commit | `b841c5b` on branch `claude/phase9-baseline-and-current-system-audit-20260915` |
| Owner decisions | All 10 resolved (see `19_OWNER_DECISIONS_REQUIRED.md`) |

---

## 3. System Health

### 3.1 Backend Health

| Check | Result |
|-------|--------|
| `GET /health` | `{"status":"healthy"}` |
| `GET /health/ready` | `{"ready":true}` |
| Database | SQLite (dev mode — PostgreSQL expected in production) |
| Cloudflare R2 | Not configured (expected in dev) |

### 3.2 Frontend Health

| Check | Result |
|-------|--------|
| `GET /` | 200 OK |
| `GET /api/deployment-health` | Proxies to backend successfully |
| RTL default | `dir=rtl`, `lang=ar` on all routes |
| Build | Next.js 16 App Router |

### 3.3 Frontend ↔ Backend Connectivity

| Check | Result |
|-------|--------|
| `/api/deployment-health` proxy | PASS — frontend proxies to backend |
| `/api/backend/[...path]` rewrite | Configured in Next.js |

### 3.4 Production Health

| Check | Result |
|-------|--------|
| `https://saudi-business-web.vercel.app/api/deployment-health` | BLOCKED — network restrictions in remote execution environment |

---

## 4. Test Suite Results

| Metric | Value |
|--------|-------|
| Total tests | 597 |
| Passed | 596 |
| Failed | 1 |
| Duration | 211.06s |

**Failed test**: `test_phase7b_gastat_live_source.py::test_a_gastat_live_connector_contract`
- **Reason**: External GASTAT API unavailable from audit environment (`assert 'unavailable' == 'healthy'`)
- **Classification**: TEST_BLOCKED — external dependency, not a code defect
- **Next action**: Verify GASTAT connector works from production or a network-enabled environment

---

## 5. Browser UX Walkthrough

### 5.1 Route Audit (26 routes tested)

| Route | Status | Notes |
|-------|--------|-------|
| `/` | 200 | Home/landing — green Saudi theme, Arabic RTL, decision dashboard widget |
| `/login` | 200 | Clean Arabic login form with demo mode |
| `/register` | 200 | Registration form |
| `/dashboard` | 200 | "مركز قيادة أعمالك" — 3 demo projects, readiness 72/100 |
| `/businesses` | 200 | "أعمالي" — requires login, shows login CTA |
| `/projects` | 200 | Project list page |
| `/feasibility` | **404** | No index route — only `/feasibility/new` exists |
| `/feasibility/new` | 200 | New feasibility study wizard |
| `/funding` | 200 | Funding page |
| `/opportunities` | 200 | Opportunities listing |
| `/tools/feasibility` | 200 | Feasibility tools |
| `/tools/financial` | 200 | Financial tools |
| `/tools/funding` | 200 | Funding tools |
| `/tools/reports` | 200 | Reports tools |
| `/tools/qualification` | 200 | Qualification tools |
| `/tools/knowledge` | 200 | Knowledge tools |
| `/tools/opportunities` | 200 | Opportunities tools |
| `/tools/proposal` | 200 | Proposal tools |
| `/start` | 200 | Getting started |
| `/help` | 200 | Help page |
| `/account` | 200 | Account settings |
| `/ideas` | 200 | Ideas page |
| `/franchises` | 200 | Redirects to `/opportunities` |
| `/qualification` | 200 | Qualification page |
| `/pricing` | 200 | Pricing page |
| `/admin` | 200 | Admin page |

**RTL/Bilingual**: All 26 routes return `dir=rtl`, `lang=ar`. PASS.

### 5.2 Visual Observations (from screenshots)

- **Home** (`01_home.png`): Green Saudi theme, enterprise dashboard, readiness metrics (78 readiness, 84% feasibility, 72% funding, 91% data), Arabic text dominant
- **Login** (`02_login.png`): Clean centered form, Arabic labels, demo mode link
- **Dashboard** (`04_dashboard.png`): "مركز قيادة أعمالك" heading, 3 demo project cards (Coffee, Medical, Packaging), readiness score 72/100
- **Businesses** (`05_businesses.png`): Auth-gated, shows empty state with login CTA

### 5.3 Evidence

Screenshots: `docs/audits/evidence/phase9-current-system-2026-09-15/` (26 PNG files + `route_audit_results.txt`)

---

## 6. MVP Screen Gap Matrix (Part E)

Comparing approved 20 MVP screens (from `08_SCREEN_INVENTORY.md`) against current system:

| # | Approved Screen | Approved Route | Current Route | Current Status | Gap |
|---|----------------|----------------|---------------|----------------|-----|
| S01 | Login | `/login` | `/login` | EXISTS — 200 | Cosmetic only. Needs baseline visual refinement. |
| S02 | Register | `/register` | `/register` | EXISTS — 200 | Cosmetic only. |
| S03 | Onboarding Wizard | `/onboard` | NONE | **MISSING** | No onboarding wizard exists. `/start` exists but is not the approved guided wizard. |
| S04 | Command Center (Home) | `/` | `/` | PARTIAL | Current home is a landing/marketing page with dashboard widget. Needs elevation to Business Command Center with Action Center strip, study grid, risk alerts, AI insights. |
| S05 | Action Center | `/actions` | NONE | **MISSING** | No `/actions` route. No notification/action center component. |
| S04a | My Businesses | `/businesses` | `/businesses` | PARTIAL | Route exists but currently auth-gated with login CTA. Needs Business Workspace cards with health, evidence coverage, decisions. Current model is Project-based, not Business Workspace-based. |
| S04b | Business Home | `/businesses/:bid` | `/businesses/[id]` | PARTIAL | Route exists in Next.js app router but serves Project detail, not Business Workspace home. Needs: profile header, health summary, latest baseline, studies list, evidence health, recommended actions. |
| S06 | Business/Study Creation Wizard | `/businesses/new` | `/feasibility/new` | PARTIAL | Creation flow exists at wrong route. Current wizard creates a FeasibilityStudy under a Project. Needs to create a Business Workspace as the first-class entity. |
| S07 | Workspace — Overview | `/businesses/:bid/studies/:id` | `/projects/[projectId]/studies` | PARTIAL | Study view exists under projects route. Needs route restructuring under businesses. Content needs executive summary with AI recommendation, evidence coverage, key metrics. |
| S08 | Workspace — Market | `/businesses/:bid/studies/:id/market` | NONE (tab within study) | **MISSING** as standalone route | Market data may exist within study payload but no dedicated Market tab/route. |
| S09 | Workspace — Competitors | `/businesses/:bid/studies/:id/competitors` | NONE | **MISSING** as standalone route | Backend has competitor data in study payload. No dedicated frontend route. |
| S10 | Workspace — Location | `/businesses/:bid/studies/:id/location` | NONE | **MISSING** as standalone route | Backend has location analysis. No dedicated frontend route. |
| S11 | Workspace — Operations | `/businesses/:bid/studies/:id/operations` | NONE | **MISSING** as standalone route | Backend has operations data in study. No dedicated frontend route. |
| S12 | Workspace — Financials | `/businesses/:bid/studies/:id/financials` | `/tools/financial` | PARTIAL | Financial tools page exists at different route. Not integrated into workspace tab structure. |
| S13 | Workspace — Evidence | `/businesses/:bid/evidence` | NONE as workspace tab | **MISSING** as workspace route | Backend evidence API exists (`/api/evidence/`). No dedicated frontend evidence center within workspace. |
| S14 | Workspace — Risks | `/businesses/:bid/studies/:id/risks` | NONE | **MISSING** | No risk tab or risk display. Backend scenarios API exists but no dedicated risk view. |
| S15 | Workspace — Decision | `/businesses/:bid/studies/:id/decision` | NONE as workspace tab | **MISSING** as workspace route | Backend decision API exists (`/api/decision/`). No dedicated decision tab in workspace. |
| S16 | Evidence Detail Panel | `/businesses/:bid/evidence/:eid` | NONE | **MISSING** | No evidence detail panel/modal. Backend has evidence item endpoints. |
| S40 | Profile & Organization | `/settings/profile` | `/account` | PARTIAL | Account page exists at `/account`, not at approved route `/settings/profile`. Content scope TBD. |
| S42 | Language & Regional | `/settings/language` | NONE | **MISSING** | RTL is default but no language/regional settings page. |

### MVP Gap Summary

| Category | Count |
|----------|-------|
| EXISTS (cosmetic refinement only) | 2 (Login, Register) |
| PARTIAL (route exists, content/structure gap) | 7 (Home, My Businesses, Business Home, Creation Wizard, Overview, Financials, Profile) |
| MISSING (no route or component) | 11 (Onboarding, Action Center, Market, Competitors, Location, Operations, Evidence, Risks, Decision, Evidence Detail, Language Settings) |

**11 of 20 MVP screens are MISSING. 7 are PARTIAL. 2 exist with cosmetic gaps only.**

---

## 7. Business Workspace Model Verification (Part F — P4 Gate)

### 7.1 Approved Model (from baseline)

```
User/Org → Business Workspace (first-class entity) → Studies/Evaluations
                                                    → Evidence Register
                                                    → Financial Models
                                                    → Decisions
                                                    → Reports
                                                    → Monitoring
```

Business Workspace is the persistent, study-independent entity representing a business opportunity. Multiple studies can exist under one workspace.

### 7.2 Current Model (from `backend/app/models.py`)

```
User → Organization → Project → FeasibilityStudy → EvidenceItem
                                                  → StudyAssumption
                                                  → BusinessProfile
                                                  → FinancialAssumption
                                                  → FinancialResult
                                                  → SensitivityScenario
```

Key observations:
- **No "Business Workspace" entity exists.** The current first-class entity is `Project`.
- `Project` has: `name`, `industry`, `investment`, `stage`, `workflow_status`, `owner_id`, `organization_id`
- `FeasibilityStudy` belongs to `Project` (FK: `project_id`)
- `BusinessProfile` belongs to `FeasibilityStudy` (not to Project/Workspace) — this means the business profile is study-scoped, not workspace-scoped
- `EvidenceItem` belongs to `FeasibilityStudy` — evidence is study-scoped, not workspace-scoped
- No workspace-level evidence register
- No workspace-level decision history
- No workspace health aggregation

### 7.3 Schema Gap Analysis

| Approved Concept | Current Implementation | Gap | Migration Impact |
|-----------------|----------------------|-----|------------------|
| Business Workspace | `Project` table | RENAME + EXTEND | Add workspace-level fields (health, status, sector_pack) |
| Workspace → Studies (1:many) | `Project → FeasibilityStudy` (1:many) | ALIGNED | Relationship structure matches, just needs rename |
| BusinessProfile on Workspace | `BusinessProfile` on `FeasibilityStudy` | **STRUCTURAL** | Must move profile FK from study to workspace level |
| Evidence Register per Workspace | `EvidenceItem` per study | **STRUCTURAL** | Must add workspace-level evidence or cross-study evidence linking |
| Decision History per Workspace | `StudyDecision` per study | PARTIAL | Decision exists per study; workspace-level history view needed |
| Funding Readiness per Workspace | `FundingProgram` (global) | **STRUCTURAL** | Per-workspace funding readiness scoring needed |
| Monitoring per Workspace | Not implemented | **NEW** | Phase 10 |

### 7.4 P4 Gate Verdict

**SCHEMA_CHANGE_REQUIRES_OWNER_REVIEW**

The current `Project` entity can be evolved into `BusinessWorkspace` via migration + rename. The 1:many Project→Study relationship already matches the approved model. However, `BusinessProfile` and `EvidenceItem` FK restructuring requires a schema migration that must be reviewed before Phase 9 implementation begins.

**Recommended approach** (for owner review):
1. Rename `Project` → `BusinessWorkspace` (Alembic migration)
2. Move `BusinessProfile` FK from `feasibility_studies.id` to `business_workspaces.id`
3. Add workspace-level evidence linking (cross-study or workspace-scoped)
4. Add workspace health/status fields
5. Preserve backward compatibility for existing data

---

## 8. API Baseline Verification (Part G — P5 Gate)

### 8.1 Current Backend API Surface

39 router files across `backend/app/api/` and `backend/app/api/v2/`:

**Auth & User**: `auth.py`
**Core Workspace**: `projects.py`, `feasibility.py`, `business_profile.py`
**Evidence & Research**: `evidence.py`, `assumptions.py`, `extracted_facts.py`, `v2/sources.py`, `v2/knowledge.py`, `v2/study_engine.py`
**Financial**: `financial.py`, `financial_health.py`, `financing_structure.py`, `scenarios.py`, `borrowing_capacity.py`, `collateral.py`, `company_financial_profile.py`
**Decision**: `decision.py`
**Funding**: `funding.py`, `funding_gap.py`, `funding_matching.py`, `funding_programs.py`, `funding_readiness.py`
**Opportunities**: `opportunities.py`, `opportunity_matching.py`, `verified_opportunities.py`
**Other**: `ideas.py`, `leads.py`, `franchises.py`, `proposals.py`, `qualification.py`, `quick_idea_check.py`, `reports.py`, `documents.py`, `entitlements.py`, `growth.py`, `launch.py`, `validation.py`, `admin.py`

### 8.2 API Coverage per MVP Screen

| MVP Screen | Required API | Current API | Status |
|------------|-------------|-------------|--------|
| S01 Login | Auth endpoints | `auth.py` — login, register, token | **READY** |
| S02 Register | Registration | `auth.py` — register | **READY** |
| S03 Onboarding Wizard | Profile creation, goal setting | `business_profile.py` (partial) | **PARTIAL** — wizard flow not exposed as API |
| S04 Command Center | Portfolio aggregation, AI insights, risk alerts | `projects.py` (list), `feasibility.py` | **PARTIAL** — no portfolio health aggregation endpoint, no AI insight endpoint |
| S05 Action Center | Pending decisions, notifications | `decision.py` (per-study) | **PARTIAL** — no cross-workspace action aggregation |
| S04a My Businesses | Workspace list with health | `projects.py` (CRUD) | **PARTIAL** — project list exists but no health/evidence coverage fields |
| S04b Business Home | Workspace detail, studies, evidence health | `projects.py`, `feasibility.py`, `evidence.py` | **PARTIAL** — endpoints exist separately but no unified workspace home endpoint |
| S06 Creation Wizard | Business + study creation | `projects.py`, `feasibility.py` | **PARTIAL** — separate create endpoints, no unified wizard flow |
| S07 Overview | Study executive summary | `feasibility.py`, `financial.py`, `evidence.py`, `decision.py` | **PARTIAL** — data available across endpoints but no overview aggregation |
| S08 Market | Market research data | `v2/study_engine.py`, `v2/sources.py` | **PARTIAL** — study engine has research but no market-specific endpoint |
| S09 Competitors | Competitor analysis | `v2/study_engine.py` | **PARTIAL** — competitor data in study payload, no dedicated endpoint |
| S10 Location | Location analysis | `v2/study_engine.py` | **PARTIAL** — location data in study payload, no dedicated endpoint |
| S11 Operations | Operating model | `v2/study_engine.py`, `assumptions.py` | **PARTIAL** — operations data in study, no dedicated endpoint |
| S12 Financials | Financial model, scenarios | `financial.py`, `scenarios.py`, `assumptions.py` | **READY** — comprehensive financial APIs exist |
| S13 Evidence | Evidence register, coverage | `evidence.py`, `extracted_facts.py` | **READY** — evidence CRUD, classification, provenance exist |
| S14 Risks | Risk register, sensitivity | `scenarios.py` | **PARTIAL** — scenarios exist but no dedicated risk register API |
| S15 Decision | AI recommendation, owner approval | `decision.py` | **READY** — decision tree, recommendation, owner action exist |
| S16 Evidence Detail | Single evidence item detail | `evidence.py` | **READY** — individual evidence item endpoints exist |
| S40 Profile | User profile, org settings | `auth.py`, `admin.py` | **PARTIAL** — basic auth profile, no full settings API |
| S42 Language | Language preference | None | **MISSING** — no language preference API |

### 8.3 API Coverage Summary

| Status | Count | Screens |
|--------|-------|---------|
| READY | 6 | Login, Register, Financials, Evidence, Decision, Evidence Detail |
| PARTIAL | 13 | Onboarding, Command Center, Action Center, My Businesses, Business Home, Creation, Overview, Market, Competitors, Location, Operations, Risks, Profile |
| MISSING | 1 | Language Settings |

**6 of 20 MVP screens have READY backend API. 13 are PARTIAL. 1 is MISSING.**

Most PARTIAL screens have underlying data available but need:
- Route restructuring (workspace-centric instead of project-centric)
- Aggregation endpoints (portfolio health, workspace overview, cross-study queries)
- Dedicated dimension endpoints (market, competitors, location, operations as separate APIs instead of embedded in study payload)

---

## 9. End-to-End Value Loop Verification (Part H)

### 9.1 Approved E2E Flow

```
Idea → Profile → Plan → Research → Evidence → Gaps → Model → Decision → Fund → Launch → Monitor → Grow
```

### 9.2 Current Implementation Coverage

| Stage | Approved Step | Current Implementation | Status |
|-------|--------------|----------------------|--------|
| 1 | Idea Entry | `/feasibility/new` wizard, `/ideas` page, `/quick_idea_check` API | **IMPLEMENTED** — multiple entry points exist |
| 2 | Business Profile & Goals | `BusinessProfile` model, `business_profile.py` API | **IMPLEMENTED** — profile linked to study, not workspace (structural gap) |
| 3 | Information Needs Plan | `v2/study_engine.py` — research planning | **IMPLEMENTED** — study engine generates research plan |
| 4 | Research & Discovery | `v2/sources.py`, `v2/knowledge.py` — multi-source retrieval | **IMPLEMENTED** — source connectors, knowledge documents, research runs |
| 5 | Evidence Classification | `evidence.py` — EvidenceItem with classification (VERIFIED_FACT, SYSTEM_ESTIMATE, USER_ASSUMPTION, UNKNOWN) | **IMPLEMENTED** — full 4-class system with provenance |
| 6 | Gap Recovery | `v2/study_engine.py` — gap detection, iterative research | **PARTIAL** — gap detection exists but automated recovery loop TBD |
| 7 | Financial Model | `financial.py`, `assumptions.py`, `scenarios.py` — CAPEX, OPEX, revenue, break-even, sensitivity | **IMPLEMENTED** — comprehensive financial modeling |
| 8 | Risk Analysis | `scenarios.py` — sensitivity scenarios | **PARTIAL** — scenarios exist but dedicated risk register incomplete |
| 9 | Decision | `decision.py` — GO/GO_WITH_CONDITIONS/DEFER/NO_GO with owner approval gate | **IMPLEMENTED** — full decision tree with structured rationale |
| 10 | Funding | `funding.py`, `funding_readiness.py`, `funding_matching.py`, `funding_programs.py`, `funding_gap.py` | **IMPLEMENTED** — extensive funding APIs (Phase 9B target) |
| 11 | Launch | `launch.py` — launch workspace | **PARTIAL** — launch workspace exists but post-decision flow TBD |
| 12 | Monitor | Not implemented | **NOT IMPLEMENTED** — Phase 10 target |
| 13 | Grow | `growth.py` — growth workspace | **PARTIAL** — growth workspace exists, Phase 10+ |

### 9.3 Value Loop Verdict

The core value loop (stages 1–9: Idea → Decision) is **substantially implemented** in the backend. The primary gaps are:
1. **Structural**: Business Workspace is not the first-class entity (Project is) — affects the persistence and continuity model
2. **Frontend presentation**: The workspace tab structure (Market, Competitors, Location, Operations, Evidence, Risks, Decision) does not exist as navigable routes
3. **Automated gap recovery**: Study engine supports research but the automated gap-recovery iteration loop needs completion
4. **Risk register**: Dedicated risk view separate from sensitivity scenarios

Stages 10–13 (Fund through Grow) have backend API scaffolding but are post-Phase-9 targets.

---

## 10. Current Route Architecture vs Approved

### 10.1 Routes That Need Structural Change

| Current Route | Approved Route | Change Type |
|--------------|----------------|-------------|
| `/projects` | (removed) | Routes move under `/businesses` |
| `/projects/[projectId]` | `/businesses/:bid` | Rename + restructure |
| `/projects/[projectId]/studies` | `/businesses/:bid/studies/:id` | Restructure |
| `/feasibility/new` | `/businesses/new` | Move creation wizard |
| `/tools/financial` | `/businesses/:bid/studies/:id/financials` | Move into workspace tabs |
| `/tools/feasibility` | (merged into workspace) | Absorb into workspace |
| `/account` | `/settings/profile` | Move to settings |
| (none) | `/onboard` | NEW |
| (none) | `/actions` | NEW |
| (none) | `/businesses/:bid/studies/:id/market` | NEW |
| (none) | `/businesses/:bid/studies/:id/competitors` | NEW |
| (none) | `/businesses/:bid/studies/:id/location` | NEW |
| (none) | `/businesses/:bid/studies/:id/operations` | NEW |
| (none) | `/businesses/:bid/studies/:id/risks` | NEW |
| (none) | `/businesses/:bid/studies/:id/decision` | NEW |
| (none) | `/businesses/:bid/evidence` | NEW |
| (none) | `/businesses/:bid/evidence/:eid` | NEW |
| (none) | `/settings/language` | NEW |

### 10.2 Routes to Deprecate/Remove (Phase 9)

Per approved baseline feature-flag nav policy: unimplemented modules are hidden, not rendered with dead links.

Current routes with no direct approved equivalent:
- `/tools/*` (8 routes) — tools become workspace-integrated features
- `/start` — replaced by `/onboard` wizard
- `/pricing` — product decision (keep/remove TBD by owner)
- `/franchises` — already redirects to `/opportunities`
- `/qualification` — may merge into workspace or remain standalone (owner decision)

---

## 11. RTL & Bilingual Assessment

| Check | Result |
|-------|--------|
| `dir=rtl` on `<html>` | PASS — all 26 routes |
| `lang=ar` on `<html>` | PASS — all 26 routes |
| Arabic as default language | PASS |
| Language toggle visible | Not verified (requires authenticated state) |
| Mixed Arabic/English support | Observed in dashboard (Arabic labels, English project names) |
| SAR currency formatting | Observed in financial widgets |

**Verdict**: RTL-first architecture is in place. Bilingual support exists. Language toggle and preference persistence need verification in authenticated flow.

---

## 12. Data Model Summary

### 12.1 Current Entity Count

| Entity | Table | Records (dev) |
|--------|-------|---------------|
| Organization | `organizations` | Present |
| User | `users` | Present |
| Project | `projects` | Demo data (3 projects) |
| FeasibilityStudy | `feasibility_studies` | Linked to projects |
| EvidenceItem | `evidence_items` | Per study |
| BusinessProfile | `business_profiles` | Per study (should be per workspace) |
| FundingProgram | `funding_programs` | Global catalog |
| VerifiedOpportunity | `verified_opportunities` | Global catalog |

### 12.2 Migration Count

18 Alembic migrations (`0001_initial` through `0018_funding_programs`). Schema is stable and well-versioned.

---

## 13. Security Observations

- Auth flow uses JWT tokens (observed in `auth.py`)
- Demo mode available on login page (appropriate for dev, review for production)
- Admin page accessible at `/admin` (auth-gating TBD)
- `.env` with real API keys exists locally — **must never be committed**
- CORS posture: deny-by-default with same-origin proxy (documented in README)

---

## 14. Performance Baseline

| Metric | Value |
|--------|-------|
| Backend startup | < 5s |
| Frontend startup (dev) | < 10s |
| Full test suite | 211s (597 tests) |
| Frontend route response | 200 on all routes < 2s (dev server, no auth) |

---

## 15. Pre-Phase-9 Gate Status

| Gate | ID | Status | Evidence |
|------|----|--------|----------|
| Owner approval | P1 | **PASS** | All 10 decisions resolved in `19_OWNER_DECISIONS_REQUIRED.md` |
| Coffee closure | P2 | **PENDING** | PR #56 managed by Cursor independently. Do not interfere. |
| Domain audit | P3 | **PENDING** | Coffee domain-specific code audit not yet executed. Scrap/Recycling + SaaS smoke tests pending. |
| Business Workspace model confirmation | P4 | **SCHEMA_CHANGE_REQUIRES_OWNER_REVIEW** | Current model uses Project, not Business Workspace. Migration path identified (Section 7). |
| API baseline | P5 | **PARTIAL** | 6/20 MVP screens READY, 13 PARTIAL, 1 MISSING. Backend has extensive coverage but needs restructuring (Section 8). |
| Clean start | P6 | **PENDING** | Depends on P2, P3, P4 resolution. |

---

## 16. Key Findings

### 16.1 Strengths

1. **Backend API surface is extensive** — 39 router files covering auth, evidence, financial, decision, funding, opportunities, and more
2. **Evidence system is implemented** — 4-class classification (VERIFIED_FACT, SYSTEM_ESTIMATE, USER_ASSUMPTION, UNKNOWN) with provenance
3. **Decision flow exists** — GO/GO_WITH_CONDITIONS/DEFER/NO_GO with structured rationale
4. **RTL-first architecture** — Arabic default across all routes
5. **Test coverage is strong** — 596/597 tests passing
6. **Financial modeling is comprehensive** — CAPEX, OPEX, revenue scenarios, sensitivity, break-even
7. **V2 study engine** — research planning, source integration, knowledge management

### 16.2 Structural Gaps

1. **Business Workspace does not exist as first-class entity** — Project is the current anchor. Schema migration required.
2. **Frontend route architecture misaligned** — Current routes use `/projects/`, `/tools/`, flat structure. Approved baseline uses `/businesses/:bid/studies/:id/` nested workspace structure.
3. **11 of 20 MVP screens are MISSING** — No frontend routes for workspace tabs (Market, Competitors, Location, Operations, Evidence, Risks, Decision), Onboarding Wizard, Action Center, Evidence Detail, Language Settings.
4. **No workspace-level aggregation** — Portfolio health, workspace health, cross-study evidence not exposed as endpoints.
5. **BusinessProfile is study-scoped** — Approved model requires workspace-scoped business profile.

### 16.3 Items Requiring Owner Decision

1. **Schema migration approach**: Rename `Project` → `BusinessWorkspace` or create new entity and migrate?
2. **Existing `/tools/*` routes**: Absorb into workspace or keep as standalone utilities?
3. **`/pricing` route**: Keep in Phase 9 or defer?
4. **Demo mode on login**: Keep for Phase 9 MVP or restrict?

---

## 17. Recommendations for Phase 9 Start

1. **Resolve P2 (Coffee closure)** before starting
2. **Execute P3 (domain audit)** — verify no Coffee-specific leakage in generic code
3. **Confirm P4 (schema migration)** with owner — the Project→BusinessWorkspace rename is well-defined but must be approved
4. **Start Phase 9 with route restructuring** — move from flat `/projects/` to nested `/businesses/:bid/studies/:id/` workspace structure
5. **Build workspace tabs incrementally** — Overview first, then Market/Competitors/Location/Operations/Financials/Evidence/Risks/Decision
6. **Implement Onboarding Wizard and Action Center** as Phase 9 P0 screens
7. **Preserve existing backend APIs** — most are reusable with route/model renaming

---

## 18. Evidence Inventory

| Evidence | Location |
|----------|----------|
| Route audit results | `docs/audits/evidence/phase9-current-system-2026-09-15/route_audit_results.txt` |
| Screenshots (26) | `docs/audits/evidence/phase9-current-system-2026-09-15/*.png` |
| Test results | 596 passed, 1 failed (GASTAT connector — external dependency) |
| Backend health | `{"status":"healthy"}` |
| Frontend health | All routes 200 except `/feasibility` (404) |

---

## 19. Audit Constraints

- **No code changes made** during this audit
- **No PR created** — per instructions
- **Coffee PR #56 not touched** — Cursor manages independently
- **No Phase 9 implementation started**
- **No product redesign performed** — baseline is approved and placed
- **Production health check blocked** — network restrictions in remote execution environment (not a system defect)
- **GASTAT test failure** — external API unavailable from audit environment (not a code defect)

---

**END OF AUDIT**
