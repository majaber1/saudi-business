# 18 — Architecture Gaps Before Phase 9

## Pre-Phase 9 Gate — Redefined

The pre-Phase 9 gate is limited to gatekeeping conditions, NOT implementation work. Items previously listed as "gaps" that are actually Phase 9 implementation scope have been reclassified.

### Pre-Phase 9 Gate Requirements

| # | Requirement | Description | Effort |
|---|------------|-------------|--------|
| P1 | **Owner approval** | This product review package approved by owner | Owner action |
| P2 | **Coffee closure decision** | Owner decides: continue Coffee validation independently, archive it, or merge applicable work | Owner decision |
| P3 | **Domain generalization audit** | Verify no Coffee-specific hardcoding in core architecture. Audit: information needs templates, research queries, financial model formulas, evidence classification logic, UI labels. **Bounded gate**: must pass two structural smoke scenarios (Scrap/Recycling + SaaS) — confirm that information needs, financial model structure, and research prompts produce valid (not Coffee-shaped) output for these non-F&B domains. This is a structural test, not a quality bar. | Bounded (see Smoke Test details below) |
| P4 | **Business Workspace model confirmation** | Confirm first-class Business Workspace data model (User/Org → Business → Studies/Evidence/Models/Decisions) before implementation begins | Small (design confirmation) |
| P5 | **API baseline confirmation** | Verify backend can serve workspace data through existing or minimally modified endpoints | Small (verification) |
| P6 | **Clean starting point** | Branch strategy documented, dependencies current, environment variables documented (in .env.example, not .env) | Small |

### Unverified Operational Checks

These were previously listed as gaps (G1, G9). They are operational issues that may or may not still exist. They do NOT gate Phase 9:

| # | Item | Previous ID | Description | Action |
|---|------|-------------|-------------|--------|
| U1 | Frontend-backend 503 | G1 | Frontend cannot reach backend. This is a deployment/configuration issue. May already be resolved. | Verify during Phase 9 setup; fix if still present |
| U2 | Seed data UniqueViolation | G9 | `ensure_seed_programs` function may fail on duplicate slugs. | Verify during Phase 9 setup; add upsert logic if needed |

---

## Phase 9 Implementation Scope (Previously Listed as "Gaps")

The following items were previously listed as pre-Phase 9 gaps (G3-G8, G10). They are reclassified as Phase 9 implementation work — they are the product features to be built, not prerequisites:

| # | Previous ID | Item | Description | Phase 9 Scope |
|---|-------------|------|-------------|---------------|
| I1 | G3 | **Command Center home page** | Portfolio-level command center with pending decisions, risks, insights | MVP screen (S04) |
| I2 | G4 | **Decision tab implementation** | AI recommendation with structured decision rationale, conditions, and owner approval | MVP screen (S15) |
| I3 | G5 | **Evidence UI completeness** | Coverage heatmap, gap identification, evidence detail panel with full provenance | MVP screens (S13, S16) |
| I4 | G6 | **Workspace tab data binding** | Each workspace tab renders real research data with evidence badges | MVP screens (S08-S12) |
| I5 | G7 | **Financial model display** | Financials tab displays actual financial model output with evidence traceability | MVP screen (S12) |
| I6 | G8 | **Arabic/English RTL support** | Full RTL-first layout, language toggle, bilingual content handling | MVP feature (built from day one) |
| I7 | G10 | **Phase-based progress indicators** | Phase indicators (Research → Evidence → Financials → Decision), not percentages | MVP feature |

### Additional Phase 9 Implementation Items (New)

| # | Item | Description |
|---|------|-------------|
| I8 | **Business Workspace data model** | Implement first-class Business Workspace entity (User/Org → Business → Studies/Evidence/etc.) |
| I9 | **Evidence override governance** | Versioned, auditable overrides with no silent reclassification |
| I10 | **Basic PDF report export** | Feasibility report export |
| I11 | **Onboarding wizard** | Adaptive wizard: Profile → Goals → Add Business (Existing Business OR New Venture) |
| I12 | **Action Center** | Simple notification list linking to workspace decision tabs |

---

## Domain Generalization Audit Details (P3) — Bounded Gate

### Structural Smoke Scenarios

The domain audit is bounded by two structural smoke tests. These are NOT full feasibility studies — they are structural checks that the generic architecture produces valid output for non-F&B domains:

**Scenario A: Scrap Metal / Recycling Business in Dammam**
- Verify: information needs template generates relevant categories (not F&B categories)
- Verify: financial model structure accepts non-F&B inputs (no "seating", "menu", "covers")
- Verify: research prompts do not assume restaurant/cafe context

**Scenario B: SaaS / Software Product**
- Verify: information needs template generates relevant categories (not physical-location-dependent)
- Verify: financial model structure handles subscription revenue (not transaction × ticket)
- Verify: research prompts do not assume physical storefront

**Pass criteria**: Both scenarios produce structurally valid (non-Coffee-shaped) information needs, financial model parameters, and research prompts. Quality and depth of output are NOT evaluated — only structural validity.

**Fail action**: Any Coffee-specific logic found in generic code must be refactored into the domain pack pattern before Phase 9 implementation proceeds.

### Code Audit Targets

**CODE_FACT_REQUIRED**: Audit these files for Coffee/F&B-specific logic in generic code:
- `ai_engine/config.py` — research prompts
- `ai_engine/models/` — information needs models
- `backend/app/api/v2/study_engine.py` — study creation and processing
- `financial-engine/` — financial model formulas
- `apps/web/` — UI labels and field names

Audit criteria:
1. Information needs templates hardcoded to F&B concepts (seating, menu, COGS % for food)
2. Research queries that assume restaurant/cafe contexts
3. Financial model formulas with F&B-specific structure (food cost ratio, covers x ticket)
4. Evidence classification rules tuned to F&B sources
5. UI labels that reference Coffee/F&B concepts in supposedly generic screens

Any Coffee-specific logic found must be refactored into the domain pack pattern before Phase 9 implementation.

---

## Pre-Phase 9 Checklist

- [ ] P1: Owner approval of product review
- [ ] P2: Coffee validation closure decision
- [ ] P3: Domain generalization audit complete
- [ ] P4: Business Workspace model confirmed
- [ ] P5: API baseline verified
- [ ] P6: Clean starting point established
- [ ] U1: Frontend-backend connectivity verified (non-blocking)
- [ ] U2: Seed data upsert verified (non-blocking)

**Estimated effort for gate requirements (P1-P6)**: Bounded by P3 audit (two structural smoke scenarios, not open-ended).
**Phase 9 implementation (I1-I12)**: 4-6 weeks.

---

## What Can Safely Wait Until After Phase 9?

| Item | Phase | Reason It Can Wait |
|------|-------|-------------------|
| Decision Simulator | 9A | Requires stable financial model API from Phase 9 |
| Funding Readiness module | 9B | Requires mature study completion flow |
| Opportunity Radar | 9C | Requires background signal infrastructure |
| Monitoring | 10 | Post-launch feature |
| Advanced reporting (10 types) | 9A+ | Basic PDF export sufficient for MVP |
| Multi-user / Teams | 11 | Single-user MVP is valid |
| POS / accounting integrations | 11 | Manual data entry first |
| Mobile app | 11+ | Responsive web sufficient |
| Domain packs beyond F&B | 12 | F&B validates the generic architecture |
