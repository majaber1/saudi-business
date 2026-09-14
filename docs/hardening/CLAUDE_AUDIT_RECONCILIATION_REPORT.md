# Saudi Business V4 — Claude Audit Reconciliation Report

**Mode:** READ-ONLY reproduction + audit reconciliation + production trust gate  
**Date:** 2026-09-13 (updated 2026-09-14 after owner-approved P1 closure)  
**Authoritative tip under test (audit):** `7b3fc3e36ce85d7fd3fd1d3e2db37f47b8b60790`  
**P1 closure implementation:** `dd2b22debfc3e1153cf149273c113dc4b1bc5a85` (see `P1_HARDENING_CLOSURE_REPORT.md`)  
**Frozen main:** `3ac591229c47d6408c26311a2bbf8232803a8223`  
**Phase 9A:** DELAY (not started)  
**Post-closure P1 status:** both confirmed P1s FIXED under owner approval  
**Current P0 Count:** 0  
**Current P1 Count:** 0 (closed)  
**Current P2 Count:** 2+ (unchanged; not in scope)

---

## Baseline (Gate 14)

| Item | Result |
|------|--------|
| `origin/main` | `3ac591229c47d6408c26311a2bbf8232803a8223` (unchanged) |
| PR #53 base | `main` |
| PR #53 head | `7b3fc3e36ce85d7fd3fd1d3e2db37f47b8b60790` |
| GitHub Actions | [34789781467](https://github.com/majaber1/saudi-business/actions/runs/34789781467) = **SUCCESS** |
| Diff vs main | Hardening-only (~21 files); **no migrations**; **no Phase 9A**; **no Research Quality semantic engine files** |
| Architecture path | Research → Source Registry/MCP → Knowledge → ResearchRun → ResearchEvidenceRef → deterministic RQ → Study/API → Observability UX |

**ARCHITECTURE:** PASS  
**MIGRATION:** NONE  
**PHASE 9A:** NOT STARTED

---

## Findings (classification enum)

Allowed: `CONFIRMED_CURRENT` | `FIXED_CURRENT` | `STALE_OLD_BUILD` | `NOT_REPRODUCIBLE` | `BLOCKED_FROM_VERIFICATION`

### 1. Real Estate NPV (−147M class)

**Classification:** `FIXED_CURRENT` (Claude −147M) / tip engine **PASS**  
**Severity:** P0 on tip — **not confirmed**. Modeling gap (infra/soft CAPEX) = P2 note only.

**Scenario mapping (Claude → live fields):**

| Claude input | Engine field(s) |
|--------------|-----------------|
| land_cost 80,000,000 | `land_cost` / `land_cost` |
| construction_boq 120,000,000 | `construction_boq` |
| infrastructure 25,000,000 | **not summed into CAPEX** |
| soft_costs 15,000,000 | **not summed into CAPEX** |
| units 500 | `units` |
| selling_price 900,000 | `selling_price` |
| (implicit absorption) | default ~35% Y1 if missing |

**Tip HEAD deterministic result:**

| Year | Cash flow (SAR) |
|------|-----------------|
| 0 | −200,000,000 |
| 1 | +86,625,000 |
| 2 | +103,950,000 |
| 3 | +116,943,750 |

- Discount rate: **12%**
- Engine NPV: **+43,450,304.93 SAR**
- Independent NPV (same CFs): **+43,450,304.93 SAR** (diff = **0**)
- IRR ≈ 23.6%; payback ≈ 25 months
- OPEX note: defaulted to 45% of revenue when cost inputs missing (disclosed in extract notes)

**Evidence:** `/opt/cursor/artifacts/audit_gate1_re_npv.log`  
**Conclusion:** Claude’s profitable-looking → −147M NPV is **not reproducible** on tip. Engine matches independent math. Residual: infra + soft (40M) excluded from CAPEX sum on tip deterministic extract — field-mapping limitation, not the −147M bug.

**Production note (Gate 11):** Live production (still on **main**, PR #53 not merged) study `study_24e6667b6314` / project `70` used CAPEX **240M** (land+BOQ+infra+soft), CFs `[-240M, +86.625M, +86.625M, +74.25M]`, NPV **−40,749,646.96** (independent recompute matches). Verdict `DEFER`. This is **coherent** for 240M CAPEX and is **not** Claude’s −147M failure mode. Tip vs prod CAPEX inclusion differs (200M vs 240M) — document as modeling variance, not tip P0.

---

### 2. IRR / Payback raw null UX

**Classification:** `FIXED_CURRENT`  
**Severity:** — (was P1)

- API may still carry `irr: null` / `payback_months: null`.
- User-facing: `irr_display` / `payback_display` / `*_state` via `ai_engine/tools/financial_trust.py`; web `apps/web/lib/financialDisplay.ts` (`neverNullText`).
- EN/AR copy explains unavailability; no raw `"null"` / `"UNKNOWN"` in display path.
- Production E2E payback unavailable showed human reason string, not raw null.

**Evidence:** local metric-state probes; production FIN payload `payback_display` / `payback_state`.

---

### 3. Services revenue model

**Classification:** `FIXED_CURRENT`  
**Severity:** — (was P1)

Formula in `services_capacity_revenue`:

`billing_rate × utilization_rate × headcount × billable_period`  
(default period = 160 hours/month × 12)

| Input | Value |
|-------|-------|
| billing_rate | 800 |
| utilization_rate | 0.7 |
| headcount | 10 |
| Expected Y1 | **10,752,000** |
| Engine Y1 | **10,752,000** |

Tiny MRC does not override larger capacity (max + divergence note).

---

### 4. Persistence (REAL_USER_FLOW)

**Classification:** `FIXED_CURRENT` (API production flow)  
**Severity:** — (was P1)

Production flow (no mock LLM / no test seed):

`register → login → project → v2 study → message (LLM classify) → archetype → structured answers → profile/evidence/assumptions → continue → decision → re-login → reopen`

| Field | After reopen |
|-------|----------------|
| study_id | `study_24e6667b6314` |
| project_id | `70` |
| phase | `REPORT_READY` |
| verdict | `DEFER` |
| assumptions | 6 |
| claims | 11 |
| financial NPV | same as pre-logout (**−40,749,646.96** on **production/main**) |

Evidence: `/opt/cursor/artifacts/prod_ai_e2e_final.json`. Tip-local Coffee/F&B REAL_USER_FLOW was previously proven in hardening sprint. Full browser UI logout/login on tip deploy: not separately re-shot (API persistence proven on production).

---

### 5. Evidence ↔ Assumption consistency

**Classification:** `FIXED_CURRENT` (closed 2026-09-14 under owner approval)  
**Severity:** was **P1** → FIXED

Hardening now includes allowlisted numeric consistency in `evidence_gates.py`.
Material contradictions emit `EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION` and prevent unsupported strong GO via existing decision-safety.

See `docs/hardening/P1_HARDENING_CLOSURE_REPORT.md`.

#### Historical STOP note (pre-fix)

| Item | Detail |
|------|--------|
| **ROOT CAUSE** | Theme keyword gates only; no numeric extract/compare vs assumptions |
| **Fix applied** | Allowlisted deterministic compare + decision-safety downgrade; no RQ semantic change |

---

### 6. JSON extraction fallback

**Classification:** `FIXED_CURRENT` with residual disclosure duty → overall **SAFE_FALLBACK** (not silent fabricate-for-GO)  
**Severity:** was P1; tip behavior = **SAFE_FALLBACK**

- Invalid LLM JSON → `_extract_json` returns `None`.
- Merge uses `_deterministic_extract` / deterministic numbers; extract_notes record defaults (e.g. opex 45%).
- Explanation LLM JSON failure does not replace computed NPV/IRR.
- Strong verdict still constrained by financial/evidence decision_safety gates (theme-level), not by inventing CAPEX.

Residual: opex/revenue defaults can still shape economics if user costs missing — disclosed in notes, not silent “market invent.”

---

### 7. Input plausibility

**Classification:** `CONFIRMED_CURRENT` (soft-only)  
**Severity:** **P2**

`validate_financial_inputs` is **soft validation — never blocks**.

| Case | Behavior |
|------|----------|
| A. Data center 20 MW + CAPEX 1M | **WARN** (per-MW ballpark) |
| B. Coffee/F&B implausible rent/seats/tx/ticket | **ACCEPT** (no warn in current rules) |
| C. SaaS extreme CAC/churn/growth | **ACCEPT** |

No fabricated universal market truths added. Future evidence/benchmark ranges = Phase 9A / later — **DELAY**.

---

### 8. Knowledge layer real document

**Classification:** `PARTIAL` → scored as `FIXED_CURRENT` for upload/extract path; full study citation chain **not fully proven** end-to-end on tip deploy  
**Severity:** was P2

Production upload of supported text document: **HTTP 200**, document id returned, extraction_status ready, tenant `visibility: private`.  
Object storage health may report `not_configured` while DB/knowledge path still accepts upload.

Not marked PASS solely because an upload button exists — upload+extract+storage metadata verified via API. Full “claim derived from document → user-visible citation in study decision” on tip: incomplete in this run.

---

### 9. Tenant isolation

**Classification:** `FIXED_CURRENT`  
**Severity:** release trust — **PASS**

- Local: `tests/test_router_authz.py` → **11 passed**
- Production: Tenant B → project **403**, study **404** for Tenant A ids

---

### 10. Frontend ↔ Backend stability

**Classification:** `CONFIRMED_CURRENT` (intermittent)  
**Severity:** **P2**

Samples: `/api/deployment-health` sometimes **503** (`backend: unreachable`, ~6s) then **200**; backend `/health` warm after cold-ish first hit.

**Root cause class:** `BACKEND_COLD_START` / `PROXY_TIMEOUT` / `SERVERLESS_LATENCY` (not proven `ENV_CONFIGURATION`).

Later sample batch: 8/8 ready ~0.16–0.3s — noise + cold start.

---

### 11. Production AI E2E

**Classification:** `FIXED_CURRENT` for flow/LLM/persistence; **financial coherence vs tip scenario = NOT proven on production** (prod ≠ tip)  
**Severity:** commercial trust still **NOT_YET_PROVEN**

| Item | Value |
|------|-------|
| Frontend | `saudi-business-web.vercel.app` |
| Backend | `feasibilityos-ai.vercel.app` |
| Study | `study_24e6667b6314` |
| Project | `70` |
| Archetype | `real_estate` (LLM classification observed) |
| Verdict | `DEFER` |
| NPV (prod) | −40,749,646.96 SAR (240M CAPEX path; independent CF match) |
| RQ observability | present |
| Mock LLM | **No** |
| Reopen | same phase/verdict/financial |

Production does **not** run PR #53 tip until merge. Flow/LLM/persistence/tenant isolation proven. Commercial trust still **NOT_YET_PROVEN** because tip hardening is not deployed and evidence↔assumption numeric P1 remains open.

---

### 12. Funding seed UniqueViolation (`sdb-excellence-track`)

**Classification:** `FIXED_CURRENT` (closed 2026-09-14 under owner approval)  
**Severity:** was **P1** → FIXED

`ensure_seed_programs` now uses SAVEPOINT + `IntegrityError` recovery for duplicate-slug races.
Unique constraint preserved; unrelated DB errors still propagate.

See `docs/hardening/P1_HARDENING_CLOSURE_REPORT.md`.

#### Historical STOP note (pre-fix)

| Item | Detail |
|------|--------|
| **ROOT CAUSE** | Non-transactional check-then-insert on unique `slug` |
| **Fix applied** | `begin_nested()` + catch IntegrityError only |

---

### 13. AI degraded mode / retry

**Classification:** `FIXED_CURRENT` (message sanitization) / UX retry **PARTIAL**  
**Severity:** was P1 → **PARTIAL PASS**

`ai_engine/utils/safe_messages.py` + workspace scrubbing: friendly EN/AR, strip provider URLs/codes; no secrets.  
Retry/recoverability: present as user messaging / Retry-After on health; not a full automatic multi-retry UX everywhere.

**Gate 13 grade:** **PARTIAL**

---

## Counts

| Severity | Current confirmed on tip / live trust |
|----------|----------------------------------------|
| **P0** | **0** |
| **P1** | **0** (both owner-approved findings FIXED 2026-09-14) |
| **P2** | **2+** (plausibility soft-only; intermittent health; CAPEX field mapping note) |

---

## Trust verdicts

| Gate | Result |
|------|--------|
| **PRODUCTION TRUST** | **BLOCKED** (tip not production-deployed; commercial not claimed from CI) |
| **COMMERCIAL TRUST** | **NOT_YET_PROVEN** |
| **HARDENING MERGE RECOMMENDATION** | **READY_FOR_OWNER_REVIEW** (P1s closed; owner merge decision pending) |
| **PHASE 9A RECOMMENDATION** | **DELAY** |

---

## Open PR cleanup recommendations (Gate 15 — do not mutate)

| PR | Classification | Recommendation |
|----|----------------|----------------|
| **#53** | **ACTIVE** | Keep draft; HOLD merge pending P1 owner decisions |
| **#52** | ACTIVE (validation docs) | Keep; supersede narrative after this report |
| **#45** | HISTORICAL_EVIDENCE_ONLY | Close after owner ack (Phase 8A acceptance already frozen on main) |
| **#42** | STALE / BLOCKED_EXTERNAL | Keep as evidence of Monsha'at block or close as superseded |
| **#37** | HISTORICAL_EVIDENCE_ONLY | Docs audit; safe to close after ack |
| **#32** | **SUPERSEDED** by #53 financial trust | Close as superseded (do not merge) |
| **#29** | HISTORICAL_EVIDENCE_ONLY | Phase 6 knowledge validation; keep or archive |
| **#28** | HISTORICAL_EVIDENCE_ONLY | Platform provisioning note; keep |
| **#22** | STALE | Old acceptance; DO_NOT_TOUCH until owner triage |
| **#21** | SUPERSEDED (schemas landed via later work) | Close as superseded after ack |
| **#14** | STALE / DO_NOT_TOUCH | Non-draft; owner product decision required |

**Do not close automatically.**

---

## Absolute constraints honored

- Did not merge PR #53  
- Did not start Phase 9A  
- Did not add migrations / RAG / pgvector / connectors / agents / benchmark engine  
- Did not change frozen Research Quality semantics  
- Did not implement P1 fixes (awaiting owner approval)  
- Did not claim commercial readiness from CI alone  
