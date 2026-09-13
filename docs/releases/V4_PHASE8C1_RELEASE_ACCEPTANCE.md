# V4 Phase 8C.1 Release Acceptance — Persistent Research Runs + Durable Provenance

**Status:** MERGED  
**Date (UTC):** 2026-09-13  
**PR:** https://github.com/majaber1/saudi-business/pull/48  
**Verified Head SHA (pre-merge):** `b161cee7d94329a972f3c4a346b7a39b5ab2441a`  
**Merge SHA / Main SHA:** `02bcef5926470f36b6fded012bf61d4ad1aefef0`  
**STOP:** Do **not** start Phase 8C.2.

## Objective

Make Research → governed source → Knowledge → `ResearchRun` → `ResearchEvidenceRef` the durable persistence path for research provenance, while preserving StudyVersion snapshot dual-write and legacy snapshot fallback for pre-8C.1 studies.

## Architecture flow

```
Existing LangGraph Research Node
        |
execute_research (Phase 8A / 8B)
        |
best-effort dual-write
        |
ResearchRun ──< ResearchEvidenceRef ──> Knowledge documents/chunks
        |
Study load hydrate (prefer ResearchRun; fallback StudyVersion snapshot)
```

### Scope merged (PR #48)

| Area | Change |
|------|--------|
| `backend/app/models.py` | `ResearchRun` + `ResearchEvidenceRef` on shared SQLAlchemy `Base` |
| `database/migrations/versions/0031_research_runs.py` | Additive `research_runs` + `research_evidence_refs` |
| `backend/app/services/research_persistence_service.py` | create/start/complete/fail, attach evidence, latest/list, hydrate |
| `ai_engine/research/service.py` | Best-effort dual-write after research |
| `ai_engine/research/nodes/research.py` | Pass project/user scope into research execute |
| `backend/app/api/v2/study_engine.py` | Hydrate ResearchRun into study load (incl. memory fallback path) |
| Alembic test head lists | Include `0031_research_runs` |
| Tests + evidence docs | Phase 8C.1 persistence gate + validation artifacts |

### Explicitly unchanged

- Financial Engine
- Risk Engine
- Decision Engine
- Report Engine
- No new RAG / vector database
- No source ranking / freshness scoring / conflict engine
- No new connectors
- No Phase 8C.2 work

## Final pre-merge review

| Check | Result |
|-------|--------|
| File scope limited to Phase 8C.1 paths | **PASS** (12 files) |
| Financial / Risk / Decision / Report untouched | **PASS** |
| No ranking / freshness / connectors / pgvector | **PASS** |
| GitHub Actions CI (847/847) | **PASS** |
| Alembic migrations on Postgres | **PASS** |
| Frontend build + saudi-business-web Vercel | **PASS** |
| feasibilityos-ai Vercel **preview** | **BLOCKED_PLATFORM** (`BUILD_FAILED` / `Resource provisioning failed`; build never started) |

Preview failure is platform provisioning noise (not code/config). No application code was changed to work around it. Production backend remained healthy.

## Migration

| Item | Result |
|------|--------|
| Alembic head | `0031_research_runs` |
| Tables | `research_runs`, `research_evidence_refs` |
| FK integrity | owner → users; evidence → research_runs CASCADE; soft FK → knowledge_documents / knowledge_chunks SET NULL |
| Idempotency | unique `(research_run_id, idempotency_key)` |
| Knowledge tables | unchanged beyond optional inbound FKs |

Fresh Postgres upgrade `→ head` validated post-merge. Local migcheck DB at `0031_research_runs` with both tables present, indexes, and unique idempotency constraint.

## Post-merge validation (from `main` @ `02bcef5`)

### Automated

| Suite | Result |
|-------|--------|
| Full backend (`pytest tests/`) | **PASS** — **847 / 847** |
| Phase 8C.1 persistence suite | **PASS** (15) |
| Alembic validation / growth / launch | **PASS** |
| Phase 8A research + final trust gate | **PASS** |
| Phase 8B controlled market research | **PASS** |
| Knowledge Intelligence + learning | **PASS** |
| Financial Trust | **PASS** |
| Tenant isolation (8C.1 + GASTAT/MISA/Knowledge regressions) | **PASS** |
| GitHub Actions on main | **PASS** (backend, Alembic, frontend, compose, secret scan) |

### Real persistence acceptance (Postgres)

| Scenario | Result |
|----------|--------|
| Research → Knowledge → ResearchRun → ResearchEvidenceRef | **PASS** |
| Close session / reopen fresh session reload | **PASS** — status, question, official URL, document_id, chunk_id |
| Latest-run determinism (Run1/2/3 → latest = Run3) | **PASS** |
| Multi-run history preserved (no overwrite) | **PASS** |
| Legacy StudyVersion snapshot fallback (no fabricated ResearchRun) | **PASS** |
| Tenant isolation | **PASS** |

Ordering uses application-side chronology (`started_at` DESC NULLS LAST, then `created_at`, then `id`) — UUID alone is not the semantic latest discriminator.

### Production backend health

| Check | Result |
|-------|--------|
| `https://feasibilityos-ai.vercel.app/health` | **PASS** — HTTP 200, `status=running`, `db_connected=true` |
| Production deploy after merge | **Ready** (`feasibilityos-gasy2beuh`, 26s) |
| saudi-business-web production | **Ready** |

## Vercel preview provisioning note

`Vercel – feasibilityos-ai` preview for PR #48 failed with:

- `errorCode=BUILD_FAILED`
- `errorMessage=Resource provisioning failed`
- Build started: **NO** (`buildingAt=null`, duration `0ms` / `?`, empty events)
- Code-related: **NO**

Classification: **PLATFORM_PROVISIONING_FAILURE**.  
This must not block Phase 8C.1 release acceptance when GitHub Actions + production health are green.

## Known limitations

1. Research dual-write is best-effort — persistence failure must not fail the research node / study path.
2. Legacy studies without ResearchRun rows continue to rely on StudyVersion snapshot projection.
3. Vercel **preview** for `feasibilityos-ai` may remain blocked by platform provisioning; production deploys are the health gate.
4. Phase 8C.2 (ranking / freshness / conflict) is **not** started.
5. No second RAG / vector index / new connectors in this phase.

## Scorecard

| Item | Result |
|------|--------|
| PHASE 8C.1 STATUS | **MERGED** |
| Merge SHA | `02bcef5926470f36b6fded012bf61d4ad1aefef0` |
| Main SHA | `02bcef5926470f36b6fded012bf61d4ad1aefef0` |
| Alembic Head | `0031_research_runs` |
| Full Backend | **PASS** 847/847 |
| Postgres Migration | **PASS** |
| ResearchRun Persistence | **PASS** |
| EvidenceRef Persistence | **PASS** |
| Latest Run Determinism | **PASS** |
| Multi-Run History | **PASS** |
| Fresh Session Reload | **PASS** |
| Legacy Compatibility | **PASS** |
| Tenant Isolation | **PASS** |
| Production Backend Health | **PASS** |
| Backend Preview | **BLOCKED_PLATFORM** |
| saudi-business-web | **PASS** |

## STOP

Phase 8C.1 release closure complete. **Do not start Phase 8C.2 automatically.**
