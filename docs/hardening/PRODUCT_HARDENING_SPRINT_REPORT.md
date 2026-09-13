# Product Hardening Sprint Report

**Status:** READY FOR OWNER REVIEW  
**Branch:** `cursor/product-hardening-sprint-1831`  
**Baseline:** Phase 8C.3 tip `93d6ed378b345565e7eee06a583ef836998e44a5`  
**Phase 9A:** DELAY (not started — no benchmarks / competitor scoring / market ranges)

## Mission

Improve trust and decision quality **between** existing layers:

Research → Evidence → Quality → Financial → Risk → Decision

Without replacing those layers, without migrations, and without Phase 9A.

## What shipped

### 1. Business Archetype Intelligence
- New deterministic package: `ai_engine/hardening/`
- `fnb` archetype added to classifier, schemas, StudyState, and web options
- Coffee / café / restaurant classifies as **fnb** (not retail/services/consulting)
- Recycling / manufacturing stays **industrial**
- SaaS stays **saas_digital**

### 2. Assumption Intelligence
- Required assumptions are schema-driven per business type
- Progressive questioning attaches **why required** banners on discovery questions
- Assumption agent maps business archetype → schema via `schema_archetype_for`

### 3. Financial Trust Gates
- `evaluate_financial_trust_gates` detects:
  - currency mismatch
  - positive NPV with missing IRR
  - positive NPV with missing payback
  - capacity / utilization / CAC / churn extremes
- **No silent corrections** (`silent_correction_applied: false`)
- Attached onto `financial_results.trust_gates` and decision audit

### 4. Evidence → Verdict Gates
- Missing critical evidence themes caps max verdict
- `apply_decision_safety` downgrades unsafe GO / GO_WITH_CONDITIONS
- Gate audit stored on `state.decision_safety` (JSON only — **no migration**)

### 5. Sector packs (questions only)
- `fnb`, `manufacturing`, `saas`
- Research areas / critical assumptions / evidence themes / decision gates
- Explicitly **no** benchmarks, percentiles, or competitor scores

## Owner Cases

| Case | Result |
|------|--------|
| 1 Coffee shop → F&B assumptions | PASS |
| 2 Recycling plant → industrial assumptions | PASS |
| 3 Accounting SaaS → SaaS assumptions | PASS |
| 4 Invalid finance → inconsistency detected, not auto-fixed | PASS |
| 5 Missing evidence → strong GO blocked | PASS |

## Tests

- `tests/test_product_hardening_sprint.py` — 9/9 PASS
- Slice with archetype + financial trust suites — 48/48 PASS
- Migration: **NONE**
- Architecture deviation: **NONE** (additive hardening layer only)

## Persistence / Tenant Isolation

- No schema migrations
- Gate audit uses existing JSON / state dict fields (`decision_safety`, `financial_results.trust_gates`, `assumption_requirements`)
- No tenant boundary changes

## Known limitations

- Browser E2E of full coffee/recycling/SaaS journeys not re-run in this sprint tip (unit gates cover Cases 1–5)
- Product Validation Sprint can be re-run by owner after merge to confirm end-to-end UX
- LLM discovery can still drift; deterministic heuristic + resolve guards prefer F&B/industrial/SaaS when keywords match

## Owner scorecard (proposed)

| Area | Result |
|------|--------|
| Archetype Engine | PASS |
| Assumption Intelligence | PASS |
| Financial Trust Gates | PASS |
| Evidence Decision Gates | PASS |
| Sector Packs (F&B / Manufacturing / SaaS) | PASS |
| Persistence | PASS (no migration) |
| Tenant Isolation | PASS (unchanged) |
| Browser E2E | PARTIAL (not re-executed this tip) |
| Frontend (`fnb` option + labels) | PASS |
| Migration | NONE |
| Phase 9A | DELAY |

## STOP

Awaiting owner review. Do **not** start Phase 9A.

## Follow-up (API choke points)

Wired explorer recommendations into `backend/app/api/v2/study_engine.py` without migrations:

- Archetype confirm attaches why-required banners on discovery questions
- `approve_stage("assumptions")` blocks when critical archetype keys are empty
- Study payloads expose `assumption_requirements`, `sector_pack`, and `decision_safety`
