# 17 — MVP vs Future Roadmap

## Phasing Strategy

The product vision is an AI Business Operating System with 9 modules. Shipping everything at once would take too long and risk quality. The roadmap prioritizes by:

1. **Core value loop**: Can the user complete a meaningful action end-to-end?
2. **Revenue potential**: Which modules drive paid conversion?
3. **Technical dependency**: What must exist before other modules can work?
4. **Competitive differentiation**: What makes Saudi Business unique?

## Pre-Phase 9 Gate (Prerequisites Only)

These items must be completed before Phase 9 implementation begins. They are NOT implementation work — they are gatekeeping conditions:

| # | Prerequisite | Description | Effort |
|---|-------------|-------------|--------|
| P1 | Owner approval of product review | This review package approved | Owner action |
| P2 | Coffee validation closure decision | Continue, archive, or merge Coffee work | Owner decision |
| P3 | Domain generalization audit | Audit information needs, research prompts, financial formulas, UI labels for Coffee-specific leakage. **Bounded gate**: must pass two structural smoke scenarios (Scrap/Recycling + SaaS) — confirm that information needs, financial model structure, and research prompts produce valid (not Coffee-shaped) output for these non-F&B domains. This is a structural test, not a quality bar. | Bounded (see P3 details) |
| P4 | Business-vs-Study object model confirmation | Confirm first-class Business Workspace data model in architecture | Small (design confirmation) |
| P5 | API baseline confirmation | Backend can serve workspace data through existing endpoints | Small (verification) |
| P6 | Clean starting point | Branch, dependencies, environment documented and ready | Small |

### Unverified Operational Checks

The following items were previously listed as architecture gaps. They are operational issues that may or may not still exist. They do NOT gate Phase 9:

| # | Item | Description | Action |
|---|------|-------------|--------|
| U1 | Frontend-backend 503 | Frontend cannot reach backend. May be resolved already. | Verify during Phase 9 setup |
| U2 | Seed data UniqueViolation | `ensure_seed_programs` may fail on duplicate slugs. | Verify and fix if needed during Phase 9 |

---

## MVP (Phase 9 — Current Target)

### Goal
A complete, professional AI Business Operating System shell with the feasibility loop as the first end-to-end experience: Business Workspace → Study → Research → Evidence → Financial Model → Decision, plus basic PDF export.

### Phase 9 Scope Includes

The following are Phase 9 implementation work (not prerequisites):

- Business Workspace as first-class entity (data model + routes)
- Command Center home page (portfolio-level view)
- Action Center (simplified notification list: "N pending decisions" linking to workspace tabs)
- Workspace tab data binding (real research data with evidence badges)
- Evidence UI completeness (coverage heatmap, gap identification, detail panel)
- Decision tab with AI recommendation, structured rationale, conditions, and owner approval
- Financial model display with evidence traceability
- Arabic/English RTL-first bilingual support
- Phase-based progress indicators (not percentages)
- Onboarding wizard (adaptive: Profile → Goals → Add Business: Existing Business OR New Venture)
- Basic PDF feasibility report export

### MVP Screens (20 screens)

| Screen | Priority | Justification |
|--------|----------|---------------|
| Login / Register | P0 | Access control |
| Onboarding Wizard | P0 | First-use experience (adaptive: Existing Business OR New Venture) |
| Business Command Center (Home) | P0 | Portfolio entry point |
| My Businesses | P0 | Business portfolio list |
| Business Home | P0 | Persistent, study-independent business workspace |
| Action Center | P1 | Pending actions (simplified notification list) |
| Business/Study Creation Wizard | P0 | Business Workspace + study initiation |
| Workspace Overview | P0 | Executive summary |
| Workspace Market | P0 | Market analysis |
| Workspace Competitors | P0 | Competitive analysis |
| Workspace Location | P0 | Location intelligence |
| Workspace Operations | P0 | Operating model |
| Workspace Financials | P0 | Financial model |
| Workspace Evidence | P0 | Evidence register with provenance |
| Workspace Risks | P1 | Risk assessment |
| Workspace Decision | P0 | AI recommendation + owner approval |
| Evidence Detail Panel | P1 | Provenance drill-down |
| Profile Settings | P1 | User profile |
| Language Settings | P1 | AR/EN toggle |

### MVP Features

| Feature | Status | MVP Scope |
|---------|--------|-----------|
| Business Workspace model | New | First-class Business → Studies → Evidence hierarchy |
| Multi-sector support | Refine | Generic information needs + F&B domain pack |
| Evidence-first research | Keep | Full research → evidence → validation pipeline |
| Provenance & classification | Keep | VERIFIED_FACT / SYSTEM_ESTIMATE / USER_ASSUMPTION / UNKNOWN |
| Financial modeling | Keep | CAPEX, OPEX, Revenue (L/B/H), Break-even, Sufficiency |
| Decision engine | Keep | 4-outcome recommendation with structured rationale |
| Gap recovery | Keep | Iterative research for UNKNOWN items |
| Owner approval gates | Keep | Decision approval with override tracking |
| Evidence override governance | New | Versioned, auditable, no silent reclassification |
| Report generation | New | PDF feasibility report (basic export) |
| Arabic/English UI | New | Full RTL-first support + language toggle |

### MVP NOT Included (Deferred)

**Feature-flag navigation policy**: During Phase 9, unimplemented modules (Simulator, Funding, Opportunity Radar, Monitoring) must be feature-flag hidden until enabled. No broken or dead routes. Sidebar items for unimplemented modules are not rendered until the module is available.

| Feature | Reason for Deferral | Phase |
|---------|-------------------|-------|
| Decision Simulator | Post-MVP; requires stable financial model API | 9A |
| Funding Readiness module | Post-MVP; requires mature study data | 9B |
| Opportunity Radar | Post-MVP; requires continuous signal collection infrastructure | 9C |
| Monitoring | Post-launch data needed | 10 |
| Advanced reporting (10 types) | Basic PDF first | 9A+ |
| POS/accounting integrations | Future | 11 |
| Team/multi-user | Future | 11 |
| Mobile app | Future (responsive web for now) | 11+ |

---

## Phase 9+ (Post-MVP)

### Phase 9A: Decision Simulator (2-3 weeks)

| Deliverable | Description |
|-------------|-------------|
| Scenario Builder | Parameter adjustment UI |
| Impact Comparison | Current vs scenario display |
| Evidence Sensitivity | Beyond-evidence warnings |
| Scenario Library | Save, compare, apply scenarios |
| Pre-built Templates | Common scenario templates |

### Phase 9B: Funding Readiness (3-4 weeks)

| Deliverable | Description |
|-------------|-------------|
| Funding Dashboard | Readiness score + gap + requirements |
| Document Checklist | Required/missing documents |
| Program Matching | Government and bank program matching |
| Package Generation | Investor and bank packages |
| Missing-Info Workflow | Guided gap resolution |

### Phase 9C: Opportunity Radar (3-4 weeks)

| Deliverable | Description |
|-------------|-------------|
| Signal Collection | Background signal gathering |
| Opportunity Scoring | Composite scoring algorithm (DRAFT weights, configurable) |
| Radar Feed | Opportunity cards with actions |
| Create Study from Opportunity | Pre-populated study creation |
| Saved Opportunities | Watchlist management |

---

## Future (Post Phase 9)

### Phase 10: Continuous Monitoring (4-6 weeks)

| Deliverable | Description |
|-------------|-------------|
| Monitoring Dashboard | Actual vs plan |
| Manual Data Entry | Monthly actuals |
| Alert System | Threshold-based alerts |
| Assumption Freshness | Evidence staleness tracking |
| AI Recommendations | Action suggestions |

### Phase 11: Enterprise Features (6-8 weeks)

| Deliverable | Description |
|-------------|-------------|
| Multi-user / Teams | Organization accounts, roles |
| Advanced Permissions | Read/write/approve per module |
| API Access | External integration API |
| POS Integration | Automated revenue tracking |
| Accounting Integration | Automated cost tracking |
| White-label | Enterprise/accelerator branding |

### Phase 12: Domain Expansion

| Deliverable | Description |
|-------------|-------------|
| Manufacturing Domain Pack | Sector-specific research + model |
| Retail Domain Pack | Sector-specific research + model |
| SaaS Domain Pack | Sector-specific research + model |
| Services Domain Pack | Sector-specific research + model |
| Domain Pack Framework | Standardized pack creation system |

---

## Technical Prerequisites by Phase

| Phase | Prerequisite |
|-------|-------------|
| MVP (Phase 9) | Pre-Phase 9 gate complete (P1-P6), Business Workspace data model, stable research pipeline, financial engine, auth system |
| 9A (Simulator) | Financial model API (parameterized), scenario comparison engine |
| 9B (Funding) | Funding program database, document management |
| 9C (Radar) | Background signal collection, scoring algorithm |
| 10 (Monitoring) | Time-series data storage, alert engine |
| 11 (Enterprise) | Multi-tenancy, RBAC, API gateway |
| 12 (Domains) | Domain pack abstraction, template system |
