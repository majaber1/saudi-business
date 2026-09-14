# P1 Hardening Closure Report

**Mode:** Owner-approved P1-only implementation  
**Date:** 2026-09-14  
**PR:** #53 (`cursor/product-hardening-sprint-1831`)  
**Do not merge. Do not start Phase 9A. Do not fix P2.**

---

## Baseline

| Item | Value |
|------|--------|
| **Current Main SHA** | `3ac591229c47d6408c26311a2bbf8232803a8223` |
| **PR #53 Head Before Fix** | `ad3562601f51d4d7e344154a12a53cef90db2fd8` |
| **PR #53 Head After Fix** | *(see tip after this docs commit; implementation at `dd2b22debfc3e1153cf149273c113dc4b1bc5a85`)* |
| **Frozen base** | `main` @ `3ac591229c47d6408c26311a2bbf8232803a8223` |

---

## P1-A — Evidence ↔ Assumption Numeric Contradiction

**Status:** FIXED

### What changed

- Extended `ai_engine/hardening/evidence_gates.py` with allowlisted deterministic numeric consistency (`evaluate_numeric_evidence_assumption_consistency`).
- Comparable family: `transaction_volume` (day↔month via ×30 only when both sides are counts).
- Emits `EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION` findings with audit fields (values, units, periods, normalized compare, reason).
- Caps `max_allowed_verdict` and downgrades strong `GO` via existing `apply_decision_safety` → `GO_WITH_CONDITIONS`.
- `ai_engine/agents/decision.py` now passes `assumptions` into evidence gates and persists `numeric_contradictions` on `decision_safety`.
- Workspace decision panel surfaces `decision_safety` codes / messages / contradictions (`data-testid="decision-safety-panel"`).

### Explicit non-goals honored

- No Research Quality authority / freshness / conflict-ranking changes.
- No SAR↔USD silent FX compare.
- No market-size vs project-revenue compare.
- No percent vs absolute compare.

### Tests

| Suite | Result |
|-------|--------|
| `tests/test_p1a_evidence_assumption_numeric.py` | PASS (6) |
| Hardening targeted | PASS |
| Phase 8C.2 research quality | PASS (67+) |
| Phase 8C.3 observability | PASS |

### Runtime evidence

`/opt/cursor/artifacts/p1a_real_user_flow_contradiction.log`

- Input class: evidence **5,000 transactions/day** vs assumption **1,000 transactions/month** (+ daily_covers mismatch).
- Verdict `GO` → `GO_WITH_CONDITIONS`.
- Gate code persisted on StudyState / API projection.
- Contradiction remains after model_dump → reopen (logout/login persistence simulation).
- UI-visible via `decision_conditions` + decision-safety panel fields.

**REAL_USER_FLOW:** PASS (deterministic study-state path; no mock pretending to be production)

---

## P1-B — Funding Seed UniqueViolation / TOCTOU

**Status:** FIXED

### What changed

- `backend/app/services/funding_programs.py` `ensure_seed_programs`:
  - Per-slug existence check
  - Insert inside `begin_nested()` SAVEPOINT
  - Catch **only** `IntegrityError` (expected duplicate-slug race)
  - Unique constraint retained; unrelated DB errors still raise

### Tests

| Suite | Result |
|-------|--------|
| `tests/test_p1b_funding_seed_concurrency.py` | PASS (first / repeat / parallel / IntegrityError race / unrelated OperationalError not swallowed) |
| `tests/test_funding_programs.py` | PASS (7) on fresh DB; combined with P1-B PASS |

### Concurrency evidence

Parallel 8-thread seed → stable catalog count (=12), unique slugs including `sdb-excellence-track`, no unhandled UniqueViolation.

---

## Counts (post-fix)

| Severity | Count |
|----------|-------|
| **P0** | **0** |
| **P1** | **0** (both approved findings closed) |
| **P2** | unchanged (not in scope) |

---

## Governance checks

| Gate | Result |
|------|--------|
| **Architecture** | PASS |
| **Migration** | NONE |
| **Research Quality Semantics** | UNCHANGED |
| **Phase 9A** | NOT STARTED |
| **GitHub Actions Run** | `34822336483` on `dd2b22d` |
| **CI** | SUCCESS |
| **Frontend production build** | PASS |
| **Browser E2E** (8C.3 observability) | PASS |
| **Backend suite** | 907 passed (deselected live/browser) |
| **Vercel Web** | evaluate on PR checks (historically SUCCESS) |
| **Vercel Backend Preview (`feasibilityos-ai`)** | known platform FAILURE — recorded separately; not classified as app pass/fail without new evidence |
| **REAL_USER_FLOW** | PASS |
| **Production Trust** | BLOCKED (tip not on production; commercial not claimed) |
| **Commercial Trust** | NOT_YET_PROVEN |
| **Hardening Merge Recommendation** | READY_FOR_OWNER_REVIEW |

---

## STOP

- Did **not** merge PR #53  
- Did **not** start Phase 9A  
- Did **not** implement P2 fixes  
- Waiting for owner review  
