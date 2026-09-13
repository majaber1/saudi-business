# V4 Phase 8C.2 — Research Quality Validation

**Status:** PASS (implementation + deterministic tests)  
**Branch:** `cursor/v4-phase8c2-research-quality-1831`  
**Baseline main:** `151d8b6b8d09ed59764f74a5c04689983bfbe906`  
**Policy version:** `8c2-v1`  
**Migration required:** **NO** (reuses `ResearchRun.result_json` + `ResearchEvidenceRef.provenance_json`)

---

## 1. Architecture

Phase 8C.2 adds a deterministic Research Quality layer on top of the frozen 8C.1 path:

```
Research Need
→ Evidence Candidates
→ Eligibility Gate
→ Claim-Type Authority Policy
→ Relevance / Freshness / Geography / Provenance
→ Evidence Quality score/state
→ Conflict Analysis
→ Preferred Evidence / UNRESOLVED
→ existing ResearchRun / ResearchEvidenceRef persistence
→ Study/API projection (additive)
```

Package: `ai_engine/research/quality/`

| Module | Role |
|--------|------|
| `engine.py` | Deterministic claim/authority/freshness/ranking/conflict/quality |
| `schemas.py` | Re-exports |
| `service.py` | Public service re-exports |
| `__init__.py` | Stable imports |

Integration:

- `ai_engine/research/service.py` evaluates quality after evidence collection, before persist
- `backend/app/services/research_persistence_service.py` stores quality metadata in existing JSON fields
- `ai_engine/research/market/market_signal.py` conflict detection now requires matching geography/unit when present

No Financial / Risk / Decision / Report engine changes.

---

## 2. Policy version

`RESEARCH_QUALITY_POLICY_VERSION = "8c2-v1"`

All evaluations include `policy_version`. Ranking is deterministic and repeatable for fixed `as_of`.

---

## 3. Claim-type authority

Claim types include: `INFLATION`, `GDP`, `INVESTMENT_FDI`, labor/economic stats, regulation families, market/pricing/competitor signals, `OTHER`, `UNKNOWN`.

Authority policy (real evidence only):

| Claim | Primary | Secondary |
|-------|---------|-----------|
| INFLATION / GDP / LABOR | `gastat` | — |
| INVESTMENT_FDI | `misa` | `gastat` |
| SME | `monshaat` (only if sourced) | `gastat` |
| Banking / Tax / Cyber | `sama` / `zatca` / `nca` (only if sourced) | — |

Registry-only placeholders never become evidence. Client-supplied trust/authority cannot elevate unsupported sources. AI assumptions are ineligible and never outrank sourced evidence.

---

## 4. Freshness

States: `CURRENT`, `ACCEPTABLE`, `STALE`, `UNKNOWN`, `NOT_APPLICABLE`

Rules:

- Prefer `published_at` as fact-date
- `retrieved_at` alone never implies CURRENT
- Missing / future `published_at` → UNKNOWN
- Claim-specific windows (e.g. pricing faster than market size)
- Regulation age is not automatically decisive → `NOT_APPLICABLE` when policy says so

---

## 5. Conflict model

Comparable conflict only when metric + period + geography + unit align and values differ.

Non-conflicts:

- different period → `TEMPORAL_CHANGE`
- different geography/unit → `SCOPE_MISMATCH`

Statuses:

- `RESOLVED_PREFERRED_SOURCE` when deterministic primary/relevant authority wins
- `UNRESOLVED` when candidates remain equally credible
- Never average values; keep all candidates auditable

---

## 6. Quality model

Ordered ranking factors:

1. claim-specific authority fit  
2. relevance  
3. freshness  
4. geography fit  
5. provenance completeness  
6. existing trust/quality metadata  
7. stable evidence-id tie-breaker  

Quality state: `HIGH` / `MEDIUM` / `LOW` / `UNKNOWN`  
Optional explanatory `quality_score` 0–100 with component breakdown (not truth probability).

---

## 7. Persistence approach

No migration 0032.

Persisted via:

- `ResearchRun.result_json.research_quality`
- `ResearchEvidenceRef.provenance_json` (`research_quality`, flattened evaluation keys, conflict refs)

Tenant isolation via existing `owner_id` scoping on get/persist.

---

## 8. API compatibility

Additive only. Existing research claim/result fields remain. Optional `research_quality` on claims and results.

---

## 9. Test results

Deterministic suite: `tests/test_phase8c2_research_quality.py`

Coverage:

- Source ranking A–H  
- Freshness A–G  
- Conflict A–I + market scope awareness  
- Quality completeness / stale / relevance / provenance / determinism / no-LLM  
- Persistence reload + tenant isolation  
- Controlled scenarios A–D  

See `docs/evidence/V4_PHASE8C2_TEST_RESULTS.json` for machine-readable counts after full suite run.

---

## 10. Live / controlled scenarios

| Scenario | Mode | Expected |
|----------|------|----------|
| A Saudi inflation | Controlled GASTAT-like fixture | INFLATION, PRIMARY gastat, honest freshness, provenance intact |
| B Saudi FDI | Controlled MISA-like fixture | INVESTMENT_FDI, PRIMARY misa |
| C Conflict | Controlled fixtures | Conflict surfaced; resolved only when policy clear |
| D Unknown publication | Controlled | Freshness UNKNOWN |

External live GASTAT/MISA connectors may be BLOCKED_EXTERNAL depending on environment egress; controlled fixtures still prove policy behavior.

---

## 11. Security checks

- No arbitrary URL elevation / client self-certification of authority  
- AI assumptions ineligible  
- Registry-only sources not selected  
- Tenant isolation on ResearchRun load  
- No secrets in ranking path  
- No extra network/LLM calls for ranking  

---

## 12. Known limitations

- Placeholder authorities (SAMA/ZATCA/NCA/Monsha'at) remain policy-ranked only when real sourced evidence exists  
- Freshness cannot invent publication dates  
- Equal-quality conflicts stay UNRESOLVED (by design)  
- Phase 8C.3 Research Activity UI / Langfuse expansion not in scope  
- No new connectors / vector DB / second RAG  

---

## 13. STOP gates

- Do not merge automatically  
- Do not start Phase 8C.3

## Correctness Fix Gate (follow-up)

Status: **PASS**

Blockers closed:
1. Claim-type / ranking isolation per claim group (no CPI↔FDI cross-ranking)
2. UNRESOLVED conflicts clear preferred (`CONFLICT_UNRESOLVED`, empty `preferred_evidence_ids`)
3. Official source identity validated via Source Registry domains (`SOURCE_IDENTITY_MISMATCH`)
4. Candidate `trust_score` / `authority_type` cannot self-elevate
5. Regulation with missing `published_at` → freshness `UNKNOWN` (not `NOT_APPLICABLE`)
6. Claim-level deterministic evidence IDs (same URL/doc, different claims → distinct IDs)

Retest: full backend **901 / 901 PASS** (was 889/889 baseline).

---

## Final Correctness Gate (fact-scope + knowledge provenance)

Status: **PASS**

SHAs (do not self-reference a docs-only tip as `tested_code_sha`):

| Field | Value |
|-------|-------|
| `baseline_sha` | `1a594a4a21ade09a2d8f6055cfe797ff603ee615` |
| `tested_code_sha` | `d7df0edd5e910a194f1b3b9225310d04b61e61a6` |
| `final_head_sha` | tip after this docs sync |
| GitHub Actions run | `34771225935` (mandatory jobs PASS) |

Mandatory GitHub CI: Backend tests, Frontend build, Alembic/Postgres, Docker Compose, Secret scan — all **PASS**.

Platform noise (not chased): Vercel `feasibilityos-ai` preview provisioning/quota failure.

Blockers closed:
1. **P0 Fact-scope preferred grouping** — preferred/conflict groups use `claim_type + metric + period + geography + unit + methodology/scope`; explicit claim_type no longer collapses periods/geographies
2. **P1 Knowledge provenance without URL** — official identity from governed URL domain **or** server connector trust **or** tenant-owned persisted KnowledgeDocument/Chunk; client ids/keys alone never elevate

Mandatory regressions added in `tests/test_phase8c2_research_quality.py`:
- Independent period / geography / unit preferred evidence
- Explicit claim_type multi-period safety
- Multiple independent conflict groups
- GASTAT/MISA persisted no-URL identity
- Fake document / cross-tenant / claimed-key mismatch / URL-vs-document mismatch

Counts:
- Phase 8C.2: **67 / 67** (was 54)
- Full backend: **914 / 914** (was 901)

Architecture: no migration, no second Source Registry, no Financial/Risk/Decision/Report drift.

STOP: Do not merge PR #50. Do not start Phase 8C.3.

