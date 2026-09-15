# 00 — Owner-Approved Decisions and Corrections

**Date**: 2026-09-15
**Status**: APPROVED — This document takes precedence over any conflicting content in deliverables 01-20.

---

## Owner Decisions (D1-D10)

### D1: MVP Scope
**Approved**: Option A with adjustment — MVP screens include feasibility workspace end-to-end + Command Center + Action Center + My Businesses + Business Home. Screen count is not an architecture constraint; it adjusts honestly to accommodate the Business Workspace model (see C3).

### D2: Domain Generalization Priority
**Approved**: Option A — Before Phase 9. Clean architecture first; Coffee-specific code audit and refactoring completed before Phase 9 implementation begins.

### D3: Arabic/English Priority
**Approved**: Option A — MVP must be bilingual from day one. RTL-first architecture. No English-only interim.

### D4: Report Generation in MVP
**Approved**: Option A — Basic PDF feasibility report export included in MVP.

### D5: Action Center Complexity
**Approved**: Option B — Simple notification list. "You have N pending decisions" linking to workspace Decision tabs. Full Action Center deferred to post-MVP.

### D6: Onboarding Flow
**Approved**: Option A (refined) — Adaptive guided wizard: Profile → Goals → Add Business (existing) or New Idea (venture). Existing businesses may skip feasibility; new ventures may start first evaluation.

### D7: Study Progress Representation
**Approved**: Option A — Phase indicators only. "Research → Evidence → Financial Model → Decision" with current phase highlighted. No percentage.

### D8: Prototype Visual Direction
**Approved**: Option A (refined) — Premium enterprise decision intelligence with Saudi green as a controlled brand/accent color. Prototype references are directional, not literal implementation specs. See C12 for design refinement.

### D9: Module Phasing Order (Post-MVP)
**Modified**: Phase 9A = Decision Simulator, Phase 9B = Funding Readiness, Phase 9C = Opportunity Radar, Phase 10 = Monitoring. Reporting is a basic export in Phase 9 (MVP), not a standalone phase.

### D10: Cursor Integration Strategy
**Approved**: Option A — Cursor continues Coffee validation independently. Phase 9 implementation starts after this review approval.

---

## Owner Corrections (C1-C10)

### C1: Reclassify G1 and G9
G1 (frontend-backend 503) and G9 (seed data UniqueViolation) are moved to UNVERIFIED_OPERATIONAL_CHECKS. These are operational issues that may or may not still exist. They are not architecture gaps and do not gate Phase 9.

### C2: Redefine Pre-Phase-9 Gate
The pre-Phase-9 gate is limited to:
1. Owner approval of this product review
2. Coffee validation closure decision (continue, archive, or merge)
3. Domain generalization audit (information needs, research prompts, financial formulas, UI labels)
4. Business-vs-Study object model confirmation (first-class Business Workspace)
5. API baseline confirmation (backend can serve workspace data)
6. Clean starting point (branch, dependencies, environment documented)

Items previously listed as "gaps" (G3-G8, G10) are Phase 9 implementation work, not prerequisites.

### C3: First-Class Business Workspace Model
The data model is: User/Org → Business Workspace → Studies, Evidence, Financial Models, Decisions, Reports, Monitoring. A "Business" is the first-class entity, not a "Study." Studies are evaluations within a Business Workspace. Routes, navigation, and API contracts reflect this hierarchy.

### C4: Agents Are Logical Responsibilities
The 7 specialist agents and 1 orchestrator represent logical responsibilities, not mandatory separate LLM processes. Preferred execution mode:
- Financial Modeling = DETERMINISTIC engine (no LLM required)
- Simulation = DETERMINISTIC engine
- Evidence Validation = rules-first, LLM-assisted where rules are insufficient
- Research = LLM-directed, tool-augmented
- Business Understanding = LLM-directed
- Decision Advisor = structured decision rationale (not "step-by-step reasoning chain")
- Monitoring = rules + threshold engine, LLM for recommendations only

Token/cost guardrails: each agent invocation should have cost bounds; prefer deterministic computation where possible.

### C5: Evidence Override Governance
User evidence overrides must be:
- Explicitly versioned (old value, new value, timestamp, reason)
- Auditable (override history preserved)
- No silent reclassification: USER_ASSUMPTION → SYSTEM_ESTIMATE is prohibited; SYSTEM_ESTIMATE → VERIFIED_FACT requires new source evidence; any class transition must be logged with justification
- Overrides flow forward to financial model and decision with the override's evidence class, not the original class

### C6: Scoring Weights Are Draft
All composite scoring weights in Funding Readiness and Opportunity Radar are:
- **DRAFT** — not empirically validated
- **CONFIGURABLE** — weights are system parameters, not hardcoded
- **REQUIRES CALIBRATION** — must be tuned against real usage data before being treated as reliable

### C7: Owner Decisions Applied
All 10 owner decisions (D1-D10) are reflected throughout the deliverables. See the D1-D10 section above.

### C8: Navigation Refinement
Approved sidebar navigation order:
1. Home (Command Center)
2. My Businesses
3. New Evaluation (+)
4. Opportunity Radar
5. Simulator
6. Funding
7. Reports
8. Action Center (replaces "Decision Inbox")
9. Settings

### C9: Domain Pack Wording
Domain packs define: information needs, research priorities, financial model dependencies. They do NOT include benchmark databases (yet). Remove any claim of "benchmark databases" from domain pack descriptions.

### C10: Final Status Update
After all corrections are applied consistently, final status changes to READY_FOR_OWNER_APPROVAL.

### C11: Business Workspace Real in UX
My Businesses (`/businesses`) and Business Home (`/businesses/:bid`) are distinct MVP screens, not theoretical placeholders. Business Home is a persistent, study-independent view showing business profile, health, studies, evidence, decisions, simulations, funding, monitoring, reports, and next actions. Screen count adjusts honestly to accommodate this — "18 screens" is not a constraint.

### C12: Visual Direction Refinement
The approved direction is Premium Enterprise Decision Intelligence with Saudi green as a controlled brand/accent color. Use strong neutral surfaces, sophisticated typography, high information clarity, limited strategic green, semantic colors for evidence/decisions, and strong AR/EN readability. Avoid excessive green backgrounds, green-on-green dashboards, generic government portal styling, or decorative cards with no decision value. Prototype references are directional, not literal implementation specs.

### C13: Database Migration Status
"No database migration is needed" is replaced with "Database/schema migration requirement is TO BE DETERMINED during P4/P5 Business Workspace model and API baseline verification." Policy: prefer reuse of existing models; do not invent a migration; if migration is required, document schema impact and alternatives; schema change requires architecture/owner approval.

### C14: Pre-Phase-9 Genericization Gate Bounded
P3 is a bounded validation gate, not a redesign sprint. After Coffee validation closes: (A) Audit generic core paths for Coffee leakage. (B) Run two lightweight STRUCTURAL smoke scenarios — Scrap/Recycling and SaaS — to prove Research → Evidence → Financial → Decision works across radically different archetypes. Refactor only generic-core leakage that blocks this proof. Non-blocking domain enhancements go to backlog.

### C15: Future Module Navigation Policy
During Phase 9, unimplemented modules (Simulator, Funding, Opportunity Radar, Monitoring) must be feature-flag hidden until enabled. No broken or dead routes. No "Coming Soon" placeholder pages unless explicitly approved.

### C16: Token/AI Cost Guardrails (Complete)
Added to Agent Model: reuse persisted outputs, cache normalized evidence, check freshness before re-research, skip already-satisfied information needs, materiality-based research depth, bounded gap-recovery cycles, stop when sufficiency criteria are met, orchestrator must not invoke every capability for every request, deterministic before LLM, avoid duplicate LLM synthesis, reuse previously approved baselines.

### C17: New Business vs New Evaluation
"New Business" creates a Business Workspace. "New Evaluation" creates a Study under an existing Business, or creates a provisional Business first if the idea is new. Existing businesses may skip feasibility entirely.

### C18: Evidence Business/Study Scope
Business evidence (`/businesses/:bid/evidence`) spans all studies. Study-scoped evidence is filtered to the active study. A study workspace must not display unrelated evidence from another study without indicating it is reusable Business-level evidence.

---

## Precedence Rule

If any content in deliverables 01-20 conflicts with this document, this document governs.
