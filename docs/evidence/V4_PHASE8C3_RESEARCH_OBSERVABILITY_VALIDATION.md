# V4 Phase 8C.3 — Research Quality Observability Validation

**Status:** READY FOR OWNER REVIEW  
**Branch:** `cursor/v4-phase8c3-research-observability-1831`  
**Baseline main:** `9f2eeb511e89b2f71ff3b060d650141c99695884`  
**Implementation tip (pre-evidence):** `7ac0c6ae138e7ea2da8d44c5591f100b1c3358a9`  
**PR:** https://github.com/majaber1/saudi-business/pull/51  
**Observability version:** `8c3-v1`  
**Migration required:** **NO**

---

## 1. Architecture baseline

Frozen Phase 8C.2 pipeline (unchanged semantics):

```
Research
→ governed Source Registry / MCP
→ Knowledge
→ ResearchRun
→ ResearchEvidenceRef
→ deterministic Research Quality (8C.2)
→ Study/API projection
→ Phase 8C.3 observability UI
```

Phase 8C.3 is **presentation + observability + safe API projection only**.
It does **not** recompute authority, freshness, conflicts, preference, or fabricate evidence.

---

## 2. Changed files

| Path | Role |
|------|------|
| `ai_engine/research/quality/observability.py` | Additive bilingual observability projection |
| `ai_engine/research/quality/__init__.py` | Export observability APIs |
| `backend/app/api/v2/study_engine.py` | Attach projection to study payload; test-only seed |
| `apps/web/components/study/ResearchQualityObservability.tsx` | Summary, claim badges, evidence drawer |
| `apps/web/app/projects/[projectId]/studies/[studyId]/workspace/page.tsx` | Wire observability into V2 workspace |
| `apps/web/e2e/phase8c3-research-observability.spec.ts` | Browser E2E |
| `apps/web/playwright.config.ts` | `ALLOW_TEST_SEED=1` for backend webServer |
| `tests/test_phase8c3_research_observability.py` | Deterministic projection tests |
| `docs/evidence/V4_PHASE8C3_RESEARCH_OBSERVABILITY_VALIDATION.md` | This record |
| `docs/evidence/V4_PHASE8C3_TEST_RESULTS.json` | Machine-readable results |

---

## 3. API changes (additive only)

Study GET/state payloads now include:

- `research_quality_observability` (top-level)
- `research_context.research_quality_observability` (nested)

Derived from existing `research_quality` + claims. No new tables. No breaking fields.

Test-only:

- `POST /api/v2/studies/{study_id}/test/seed-research-quality`
- Gated by `ALLOW_TEST_SEED=1`; blocked in production

---

## 4. UI components

- `ResearchQualitySummary` — study-level counts (preferred, unresolved, stale, unknown freshness, low quality, official)
- `ResearchQualityClaimsList` + `ClaimQualityBadge` — concise claim status
- `EvidenceDrawer` — preferred + alternate evidence, conflict candidates, selection reason, freshness, provenance, official validation badge

Progressive disclosure: study → badge → drawer → deeper provenance/conflict.

---

## 5. Browser verification

Playwright E2E (`phase8c3-research-observability.spec.ts`): **PASS**

Verified:

- Study loads in V2 workspace
- Quality badges render
- Evidence drawer opens with preferred + alternates + selection reason
- Conflict state visible for CPI GASTAT vs SAMA
- Refresh preserves observability
- Arabic + English labels
- No console-breaking errors

Screenshots (agent artifacts):

- `phase8c3-observability-en.png` — EN summary + claim badges
- `phase8c3-observability-ar.png` — AR evidence drawer with conflict candidates + preferred GASTAT

---

## 6. Tests

| Suite | Result |
|-------|--------|
| Phase 8C.3 observability | 7/7 PASS |
| Phase 8C.2 research quality | 67/67 PASS |
| Phase 8C.1 + 8C.2 + 8C.3 | 89/89 PASS |
| Phase 8A / 8B / Knowledge / MISA (named) | included in full suite |
| Full backend | 921/921 PASS |
| Frontend `next build` | PASS |
| Playwright Phase 8C.3 E2E | 1/1 PASS |

---

## 7. Security verification

- Frontend is not authoritative for quality/security
- Official badge only when server-projected `official_validated` is true
- Spoofed official / cross-tenant identity covered by frozen 8C.2 + observability projection tests
- Seed endpoint unavailable without `ALLOW_TEST_SEED` / in production
- No new persistence surface; no fabricated URLs

---

## 8. Migration status

**NONE** — uses existing `research_context` / `research_quality` JSON.

---

## 9. Architecture deviations

**NONE**

---

## 10. Known limitations

- Observability appears when `research_quality` exists on study `research_context` (real research path or test seed)
- Blog/unverified candidates may be rejected by 8C.2 eligibility and therefore not shown as alternates; seed uses SAMA as a real alternate for CPI conflict UX
- No fabricated numeric “AI confidence %” score — counts/categories only

---

## 11. Owner gate

**DO NOT MERGE** until owner review.
**DO NOT START** any phase after 8C.3.
