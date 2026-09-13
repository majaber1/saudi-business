# Product Hardening Sprint Report

**Status:** READY FOR OWNER REVIEW (aligned onto frozen Phase 8C.3 main)  
**PR:** #53 (DRAFT, OPEN — do **not** merge)  
**Branch:** `cursor/product-hardening-sprint-1831`  
**Frozen base (main):** `3ac591229c47d6408c26311a2bbf8232803a8223`  
**Previous hardening head (pre-rebase):** `dc0a7e792d2942db41f5d9f70958182fbc839286`  
**Implementation head (pre-docs):** `69896abd324c6916492d2fc7a3eac6eb99eecd0e`  
**New hardening head:** `32a711375fe7777855c1afb0cc08f3e60b170a29`  
**Rebase:** PASS (clean onto frozen main; no conflicts)  
**Retarget:** PASS (PR base = `main`)  
**Phase 9A:** DELAY (not started — no benchmarks / competitor scoring / market ranges)

## Mission

Improve trust and decision quality **between** existing layers:

Research → Evidence → Quality → Financial → Risk → Decision

Without replacing those layers, without migrations, and without Phase 9A.

## Rebase / alignment

| Item | Result |
|------|--------|
| Frozen main SHA verified | `3ac591229c47d6408c26311a2bbf8232803a8223` |
| Main advanced beyond freeze? | NO |
| Rebase onto frozen main | PASS |
| PR #53 base retargeted to `main` | PASS |
| PR remains OPEN + DRAFT | YES |
| Migrations | NONE |
| Phase 8C.2 / 8C.3 frozen semantics changed? | NO |

## Final changed-file list (vs frozen main)

```
ai_engine/agents/assumption.py
ai_engine/agents/decision.py
ai_engine/agents/discovery.py
ai_engine/agents/financial_analyst.py
ai_engine/archetypes/classifier.py
ai_engine/archetypes/schemas.py
ai_engine/discovery/interview.py
ai_engine/hardening/__init__.py
ai_engine/hardening/archetype_intelligence.py
ai_engine/hardening/evidence_gates.py
ai_engine/hardening/financial_gates.py
ai_engine/hardening/sector_packs.py
ai_engine/models/study_state.py
apps/web/components/study/archetypeOptions.ts
apps/web/lib/archetypeLabels.ts
backend/app/api/v2/study_engine.py
docs/hardening/PRODUCT_HARDENING_SPRINT_REPORT.md
tests/test_hardening_approve_stage_gate.py
tests/test_product_hardening_sprint.py
```

**Unexpected scope:** NONE (no Alembic, no research-quality ranking/freshness/authority/conflict engines, no Knowledge/ResearchRun/EvidenceRef persistence changes, no funding/benchmark/Phase 9A).

## What shipped (preserved)

### 1. Business Archetype Intelligence
- Deterministic package: `ai_engine/hardening/`
- `fnb` archetype in classifier, schemas, StudyState, and web options
- Coffee / café / restaurant → **fnb** (not retail/services/consulting)
- Recycling / manufacturing → **industrial**
- SaaS → **saas_digital**

### 2. Assumption Intelligence
- Required / optional / critical assumption structure per business type
- Why-required banners on discovery questions
- Assumption agent maps business archetype → schema

### 3. Assumption approval gate
- `approve_stage("assumptions")` blocks when critical archetype keys are missing

### 4. Financial Trust Gates
- Currency consistency, NPV/IRR consistency, payback validity, capacity extremes
- **No silent corrections** (`silent_correction_applied: false`)

### 5. Evidence → Verdict Gates
- Missing critical evidence themes caps max verdict / blocks strong GO
- `decision_safety` stored on study state and exposed through Study API

### 6. Sector packs (questions only)
- F&B / Manufacturing / SaaS
- Explicitly **no** benchmark values

### 7. API projection
- `assumption_requirements`, `sector_pack`, `decision_safety`

## Architecture compliance

| Gate | Result |
|------|--------|
| Additive hardening only | PASS |
| Frozen 8C.3 observability semantics untouched | PASS |
| Frozen 8C.2 quality ranking / freshness / authority / conflict untouched | PASS |
| Official-source identity rules untouched | PASS |
| No fabricated evidence | PASS |
| No duplicate / temporary compatibility hacks | PASS |
| Migration | NONE |

## Verification (post-rebase)

| Suite | Result |
|------|--------|
| Hardening targeted (`test_product_hardening_sprint` + `test_hardening_approve_stage_gate`) | **12 / 12 PASS** |
| Phase 8C.3 regression (`test_phase8c3_research_observability.py`) | **7 / 7 PASS** |
| Phase 8C.2 regression (`test_phase8c2_research_quality.py`) | **67 / 67 PASS** |
| Combined (hardening + 8C.1/8C.2/8C.3 + financial trust) | **117 / 117 PASS** |
| Full backend (`pytest tests/`) | **919 passed / 14 failed** — same DB-pollution / env class as frozen main (funding catalog counts, auth email collision, health sqlite-vs-postgres). **Not introduced by hardening.** |
| Frontend typecheck | PASS |
| Frontend lint | PASS |
| Frontend build | PASS |
| Browser E2E Phase 8C.3 observability | **1 / 1 PASS** (refresh + AR/EN; no app-route mocks) |
| Coffee HTTP real workflow + critical approve gate | PASS |
| Coffee browser/API persistence check (no route mocks) | PASS |

## Real workflow classification

**REAL_USER_FLOW** (HTTP Study API against live local backend + persisted StudyState JSON roundtrip)

Coffee Shop expected outcomes verified:

- classified as F&B (`fnb`)
- F&B questions / sector pack shown
- required / critical fields enforced
- assumptions persist across GET refresh
- financial validation codes fire without silent correction
- evidence gaps downgrade unsafe GO via decision safety unit/API gates
- `approve/assumptions` returns 400 when critical keys empty

## Owner Cases

| Case | Result |
|------|--------|
| 1 Coffee shop → F&B assumptions | PASS |
| 2 Recycling plant → industrial assumptions | PASS |
| 3 Accounting SaaS → SaaS assumptions | PASS |
| 4 Invalid finance → inconsistency detected, not auto-fixed | PASS |
| 5 Missing evidence → strong GO blocked | PASS |

## Known limitations

- Full-backend suite still has pre-existing 14 environment/DB-pollution failures on this machine (also present on frozen main class of failures); treat CI green on PR as the authoritative app-code signal.
- Decision-safety UI chrome is API-projected; strong GO blocking is enforced in decision/evidence gates + Study payload (`decision_safety`), not a separate marketing banner component.
- LLM discovery can still drift; deterministic heuristic + resolve guards prefer F&B/industrial/SaaS when keywords match.
- Vercel `feasibilityos-ai` preview may FAIL as known platform noise; evaluate separately from GitHub Actions app CI.
- Phase 9A must remain DELAY until owner explicitly starts it after reviewing Hardening.

## Phase 9A recommendation

**DELAY**

## STOP

Awaiting owner review.

**DO NOT MERGE PR #53.**  
**DO NOT START PHASE 9A.**
