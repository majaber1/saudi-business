# V4 Phase 8C.1 — Research Persistence Validation

**Status:** PASS  
**Baseline main:** `563255f43b05c772da2abc15e093751c06ebdae9`  
**Branch:** `cursor/v4-phase8c1-research-persistence-1831`  
**Scope:** Persistence + provenance only (no ranking / freshness / conflict / Langfuse / connectors / pgvector)

---

## 1. Schema

### `research_runs`
| Column | Notes |
|--------|--------|
| `id` | UUID PK (`run_id`) |
| `study_id`, `project_id` | Study linkage |
| `owner_id`, `user_id` | Tenant ownership (`owner_id` int FK users; `user_id` string matches study_states_v2) |
| `research_type`, `question`, `status` | PLANNED / RUNNING / COMPLETE / PARTIAL / NOT_FOUND / SOURCE_UNAVAILABLE / FAILED |
| `plan_json`, `result_json`, `source_keys_json` | Structured plan/result projection |
| `knowledge_reused`, `live_fetch_count` | Reuse / live counters |
| `started_at`, `completed_at`, `created_at`, `updated_at` | Timestamps |
| `sanitized_error_code`, `sanitized_error_message` | Safe error fields |

### `research_evidence_refs`
| Column | Notes |
|--------|--------|
| `id` | UUID PK |
| `research_run_id` | FK → `research_runs` CASCADE |
| `study_id`, `owner_id`, `user_id` | Tenant scope |
| `source_key`, `source_name` | Source identity |
| `source_document_id`, `chunk_id` | Soft FKs → Knowledge Layer (SET NULL; never invented) |
| `official_url`, `authority_type` | Provenance |
| `published_at`, `retrieved_at` | Dates when known |
| `evidence_type`, `confidence`, `provenance_json` | Metadata |
| `idempotency_key` | Unique per `(research_run_id, idempotency_key)` |

Canonical content remains in `knowledge_documents` / `knowledge_chunks` / `knowledge_evidence`.

---

## 2. Migration

- **ID:** `0031_research_runs`
- **Revises:** `0030_knowledge_sources`
- **Type:** Additive only (create tables + indexes + uniqueness)
- **Downgrade:** Drops `research_evidence_refs` then `research_runs`
- **Result:** PASS (upgrade + downgrade + re-upgrade exercised in tests)

---

## 3. Relationships

```
ResearchRun
  └── ResearchEvidenceRef
        ├── knowledge_documents (optional FK)
        ├── knowledge_chunks (optional FK)
        └── official source URL / registry metadata
```

No `research_documents`, no second vector store, no duplicate Evidence Pack.

---

## 4. Persistence flow

1. Phase 8A/8B `execute_research` completes → `persist_research_result` dual-writes a `ResearchRun` + evidence refs.
2. StudyVersion snapshot continues to store `research_*` / `market_research_context` (compatibility).
3. `_load_study` restores snapshot first, then **prefers** dedicated ResearchRun projection when rows exist.
4. Legacy studies (snapshot only) keep working unchanged.

---

## 5. Fresh-session reload

Test: `TestAcceptanceFreshReload::test_18_fresh_session_reload_and_reopen`

- Persist run + evidence → close session → new session reload
- Verified: status, question, `source_document_id`, `chunk_id`, `official_url`, hydrate projection

---

## 6. Legacy snapshot fallback

Test: `test_k_legacy_snapshot_fallback`

- No ResearchRun rows → hydrate leaves snapshot fields intact
- No migration-time fabrication

---

## 7. Tenant isolation

Test: `test_o_p_tenant_isolation`

- Owner B cannot `get_run` / `load_latest_run` / `load_run_evidence` / hydrate Owner A’s study research
- PASS

---

## 8. Transaction failure

Test: `test_n_transaction_rollback_on_evidence_failure`

- Forced failure in `attach_evidence_refs` → `persist_research_result` returns `None`, rolls back
- No COMPLETE orphan runs
- PASS

---

## 9. Dual-write / idempotency / API

| Gate | Result |
|------|--------|
| New persistence preferred over snapshot | PASS |
| Dual-write consistency | PASS |
| Idempotent re-persist same `run_id` | PASS |
| API fields `research_status/context/attempts/market_research_context` | PASS |
| Study load prefers persistence | PASS |

---

## 10. Regression

Suite (134 passed):

- Phase 8C.1 persistence gate
- Phase 8B controlled market research
- Phase 8A trust + research intelligence
- Phase 7A / 7B / 7C.1 (MISA)
- Knowledge Intelligence + Learning
- Financial Trust Hardening

Financial / Risk / Decision / Report engines unchanged.

---

## Architecture deviations

None material. ResearchRun is persistence/audit state only (not a workflow engine).

## Known limitations

- No UI research-history screen yet (multi-run history is queryable in DB/API projection).
- Live MCP document IDs that are not Knowledge rows are stored only as unresolved provenance (FK left null) — never invented Knowledge IDs.
- Phase 8C.2 (ranking / freshness / conflict) not started.

**STOP — do not start Phase 8C.2 automatically.**
