# V4 Phase 8C.2 Release Acceptance — Source Ranking + Freshness + Conflict Intelligence

**Status:** MERGED / CLOSED / FROZEN  
**Date (UTC):** 2026-09-13  
**Phase:** 8C.2 — Source Ranking + Freshness + Conflict Intelligence  
**PR:** [#50](https://github.com/majaber1/saudi-business/pull/50)  
**Baseline before phase (`main`):** `151d8b6b8d09ed59764f74a5c04689983bfbe906`  
**Approved PR Head:** `282a6d690decb378498e51e7ccea60d2e5bf1c76`  
**Tested Code SHA:** `d7df0edd5e910a194f1b3b9225310d04b61e61a6`  
**Merge SHA:** `99235d82273b744bc91944827ba56fb1afeb5cd2`  
**Final Main SHA (at merge):** `99235d82273b744bc91944827ba56fb1afeb5cd2`  
**GitHub Actions Run (tested code):** [34771225935](https://github.com/majaber1/saudi-business/actions/runs/34771225935)  
**STOP:** Do **not** start Phase 8C.3 without explicit owner approval.

---

## Architecture

```
Research
  → governed Source Registry / MCP
  → Knowledge
  → ResearchRun
  → ResearchEvidenceRef
  → deterministic Research Quality
  → Study / API projection
```

Frozen Phase 8C.1 persistence path remains intact. Phase 8C.2 adds deterministic Research Quality on top of existing `ResearchRun.result_json` / `ResearchEvidenceRef.provenance_json` fields. **No migration. No second Source Registry. No new connector / RAG / agent runtime.**

### Merged scope (PR #50)

| Area | Change |
|------|--------|
| `ai_engine/research/quality/` | Deterministic claim/authority/freshness/ranking/conflict/quality |
| `ai_engine/research/service.py` | Evaluate quality after evidence collection; pass `db` + `owner_id` |
| `ai_engine/research/market/*` | Scope-aware market conflict alignment |
| `backend/app/services/research_persistence_service.py` | Persist quality metadata in existing JSON fields |
| `backend/app/services/source_registry.py` | Reuse existing registry for official identity |
| `tests/test_phase8c2_research_quality.py` | Deterministic gate (67 tests) |
| Evidence docs | Validation + machine-readable results |

### Explicitly unchanged

- Financial Engine / Risk Engine / Decision Engine / Report Engine
- Funding / Launch / Growth
- No Alembic migration (`0032` not created)
- No new connectors, RAG, agent frameworks, or UI observability (8C.3)

---

## Documented behaviors (frozen)

| Behavior | Guarantee |
|----------|-----------|
| Claim-aware authority policy | Authority fit is claim-type specific (e.g. CPI→GASTAT PRIMARY, FDI→MISA PRIMARY) |
| Server-validated official identity | Client `source_key` / scores / `authority_type` alone never elevate |
| Knowledge provenance identity | Tenant-owned persisted KnowledgeDocument/Chunk may validate official identity without URL |
| Freshness policy | Prefer `published_at`; missing/future → UNKNOWN; regulation undated → UNKNOWN |
| Fact-scope grouping | Preferred/conflict groups use claim_type + metric + period + geography + unit + methodology/scope |
| Conflict handling | Comparable conflicts only within identical fact scope; temporal/geo/unit differences are non-conflicts |
| Unresolved conflict safety | UNRESOLVED clears preferred (`preferred_evidence_ids` empty for that conflict) |
| Persistence | Quality metadata via existing ResearchRun / ResearchEvidenceRef JSON; reload preserves independent preferred scopes |
| Tenant isolation | Cross-tenant ResearchRun and Knowledge provenance reads blocked; fake docs do not leak existence |
| No fabricated evidence | No invented URLs/docs; registry placeholders never become evidence |
| API compatibility | Additive `research_quality` only; existing claim/result fields preserved |
| No LLM authority selection | Ranking/conflict are deterministic |

---

## Pre-merge verification

| Check | Result |
|-------|--------|
| PR head == approved `282a6d690decb378498e51e7ccea60d2e5bf1c76` | **PASS** |
| Scope audit (no Financial/Risk/Decision/Report/Funding/Launch/Growth/migrations/RAG/agents/8C.3 UI) | **PASS** (13 files) |
| GitHub Actions `34771225935` on tested code `d7df0edd…` | **SUCCESS** |
| Backend / Frontend build / Alembic-Postgres / Docker Compose / Secret scan | **PASS** |
| Vercel `saudi-business-web` preview | **PASS** |
| Vercel `feasibilityos-ai` preview | **BLOCKED_PLATFORM** (known provisioning/quota noise; not chased in app code) |

---

## Post-merge validation (from `main` @ `99235d82273b744bc91944827ba56fb1afeb5cd2`)

| Suite | Result |
|-------|--------|
| Phase 8C.2 (`tests/test_phase8c2_research_quality.py`) | **67 / 67 PASS** |
| Full backend (`pytest tests/`) | **914 / 914 PASS** |
| Phase 8C.1 / 8B / 8A / 7A / 7B / MISA / Knowledge / Financial Trust / Alembic group | **135 PASS** |
| Focused smoke (fact-scope + knowledge provenance + correctness gate classes) | **24 / 24 PASS** |

### Post-merge correctness smoke

| Scenario | Result |
|----------|--------|
| A. CPI / GASTAT primary + validated identity | **PASS** |
| B. FDI / MISA primary | **PASS** |
| C. Multiple periods (GDP 2025 vs 2026) — independent preferred, no false conflict | **PASS** |
| D. Geography separation (Saudi CPI vs Riyadh CPI) | **PASS** |
| E. Comparable conflict — deterministic preferred or UNRESOLVED with zero preferred | **PASS** |
| F. Persisted GASTAT/MISA Knowledge without URL | **PASS** |
| G. Fake document/source spoof — no authority elevation | **PASS** |
| H. Cross-tenant evidence reference — blocked | **PASS** |

---

## Migration

**NONE.** Phase 8C.2 reuses existing persistence JSON fields. Alembic head unchanged by this phase.

---

## Known limitations

1. Equal-quality comparable conflicts remain **UNRESOLVED** by design.
2. Authorities such as SAMA / ZATCA / NCA / Monsha'at only rank when real governed evidence exists.
3. No new connectors were added.
4. Phase 8C.3 observability UI is intentionally **not** included.
5. Vercel `feasibilityos-ai` preview provisioning/quota failure remains platform noise unless separately proven otherwise.

---

## Freeze declaration

**Phase 8C.2 is MERGED / CLOSED / FROZEN.**

Frozen architecture behavior:

- claim-aware deterministic authority
- source identity validation
- Knowledge provenance identity
- freshness classification
- evidence quality scoring
- fact-scope preference
- conflict intelligence
- unresolved conflict safety
- durable ResearchRun / ResearchEvidenceRef integration

Future phases must not silently change these semantics. Any future architecture change requires an explicit architecture decision.

**Do not start Phase 8C.3 without explicit owner approval.**
