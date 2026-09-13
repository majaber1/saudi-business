# Saudi Business V4 — Product Validation Sprint Report

**Status:** COMPLETED  
**Owner gate:** Product Validation Sprint only (no Phase 9A, no product code changes)  
**Date:** 2026-09-13  
**Evaluator lens:** Saudi entrepreneur / SME owner / investor (not developer)

---

## Executive Summary

The platform **can run a full study end-to-end** for SME, industrial, and digital ideas, and it **surfaces Research Quality observability** (preferred official sources, freshness flags, evidence drawer). That is real product progress.

It is **not yet trustworthy enough to commercialise** as an investment decision tool.

Across three live cases, a business user gets a polished journey and a GO / NO_GO style verdict, but the **economics often do not match the business**, research claims are **too generic** (repeated macro inflation / GDP), and financial outputs sometimes **contradict themselves** (positive NPV with uncalculable IRR/payback). A careful founder would not bet money on these numbers without heavy manual rework.

**Can a real business user use this platform to evaluate a business idea and trust the result?**  
**Today: only partially — usable workflow, insufficient trust for capital decisions.**

**Phase 9A recommendation: DELAY.**

**Product-ready claim:** **NOT MADE.** This sprint does **not** declare the product ready. Findings are based on **REAL_USER_FLOW** runs (persisted Study / Research / Financial / Risk), not mocked UI.

---

## Validation Integrity Rule

This sprint is a **product validation** exercise, not a test-data exercise.

| Classification | Meaning | Acceptable for product validation? |
|----------------|---------|-------------------------------------|
| **REAL_USER_FLOW** | Created through the actual product workflow; uses real persisted Study / Research / Financial / Risk flow | Yes — primary evidence |
| **SEEDED_VALIDATION** | Uses an approved isolated validation fixture; clearly marked; not a production customer workflow | Yes — only when labeled; cannot alone prove readiness |
| **MOCK_ONLY** | UI-only simulation without real backend persistence | **No** — not acceptable as product validation |

### Integrity outcome for this sprint

| Case | Classification | Seeded? | Mock-only? |
|------|----------------|---------|------------|
| Case 1 SME (Riyadh coffee) | **REAL_USER_FLOW** | No | No |
| Case 2 Industrial (Jeddah recycling) | **REAL_USER_FLOW** | No | No |
| Case 3 Digital (SME accounting SaaS) | **REAL_USER_FLOW** | No | No |

| Bucket | What was used |
|--------|----------------|
| Real workflow validation | All three cases below |
| Seeded validation | **None** — no approved seed fixture was used for scorecard claims |
| Mock-only | **None** — no UI-only simulation counted |

**How REAL_USER_FLOW was proven (each case):**
1. Account registration → project create → open AI study workspace in the live UI  
2. Briefing submitted through the product composer (not a fixture inject)  
3. Stage progression via product controls (archetype, discovery, evidence, assumptions, continue-to-risks/decision)  
4. `GET` study API returned **persisted** study state (`created_at` / `updated_at`, `persisted_run_id`, research attempts, financials, verdict)  
5. Research path included **live connector attempts** (e.g. GASTAT `mcp_live`) plus knowledge hits — product research pipeline  
6. Harness did **not** call `seed-research-quality` or other seed endpoints (confirmed in driver source + study payload)

**Honest caveats (still REAL_USER_FLOW, not MOCK_ONLY):**
- A Playwright driver automated clicks; humans did not manually type — still the **same product APIs and persistence** as a user.  
- Backend env had `ALLOW_TEST_SEED=1` available, but **no seed endpoint was invoked** for these cases.  
- Assumptions often carry origin `knowledge_reference` (product knowledge packs). That is **product behaviour**, not an isolated validation fixture, and is documented under gaps where the pack misfits the business.

Machine-readable proof: `docs/validation/evidence/integrity-classification.json` and `/opt/cursor/artifacts/product-validation/integrity-classification.json`.

---

## Baseline

| Item | Value |
|------|--------|
| Validation product baseline | Phase **8C.3** tip `93d6ed378b345565e7eee06a583ef836998e44a5` |
| Includes | Phase 8C.2 Research Quality Governance + 8C.3 Observability UX |
| `main` at validation start | Phase **8C.2** `9f2eeb511e89b2f71ff3b060d650141c99695884` (PR #51 open) |
| Validation branch | `cursor/product-validation-sprint-1831` |
| Runtime | Local web `:3000` + API `:8000`, PostgreSQL connected, `GROQ_API_KEY` present |
| Method | **REAL_USER_FLOW** via Playwright against live servers; no MOCK_ONLY verdicts; no SEEDED_VALIDATION scorecard claims |
| Evidence | `/opt/cursor/artifacts/product-validation/` + `docs/validation/evidence/` |

**Caveat:** Product behaviour validated on the **8C.3 tip**, not merged `main`. Commercial readiness claims for `main` require 8C.3 merge first.

---

## Product readiness assessment

| Dimension | Automated harness | Business-user judgment | Verdict |
|-----------|-------------------|------------------------|---------|
| User Experience | PASS | Flow is understandable; next steps visible | **PASS** |
| Research Quality | PASS | Observability present; claim relevance weak | **FAIL** |
| Evidence Trust | PASS | Sources visible; wrong/weak link to decision | **FAIL** |
| Business Value | PASS | Verdict exists; not investable | **FAIL** |

Harness “PASS” means panels/APIs appeared. Owner scorecard below uses **business trust**, not technical presence.  
**Do not read harness PASS as “product ready.”** Readiness is **not** claimed from mocked or seeded-only data.

---

## Case 1 — SME service (Riyadh specialty coffee)

### Scenario source classification
**REAL_USER_FLOW** — register → create project → AI study workspace → briefing → persisted research/financial/risk/report.  
**Not** SEEDED_VALIDATION. **Not** MOCK_ONLY.  
Persisted study evidence: `docs/validation/evidence/case1-sme-result.json` (+ study API dump under `/opt/cursor/artifacts/product-validation/case1-sme-study-api.json`).

### Business scenario
Specialty coffee shop in Riyadh, sit-in + takeaway, young professionals, startup budget **~450,000 SAR**.

### Input
- Project industry: food / F&B  
- Investment: 450,000 SAR  
- Archetype selected: services  
- Briefing: Saudi/Riyadh F&B market, competitors, cup pricing, rent/labor, feasibility  

### Workflow result
Reached **Report Ready** with verdict **GO_WITH_CONDITIONS**.  
Journey: Classification → Discovery → Assumptions → Financial → Risks → Decision → Report.  
Research Quality health + evidence drawer opened (GASTAT preferred; freshness often unknown).
### Strengths
- End-to-end path completes without crashing.
- Clear journey chrome and bilingual surface (EN/AR exercised).
- Final report states conditions and named risks (competition, licensing, bean supply).
- Official-source preference is visible to a non-technical user.

### Weaknesses
- **Wrong operating model:** assumptions used consulting-style drivers (billable utilisation, billing rate ~10,000, MRC, ~20 consultants) instead of cups/day, rent, labour mix, food cost %.
- **Budget ignored:** initial investment assumption ~1.5M vs founder 450k.
- **Unrealistic finance:** IRR ~110%, payback ~9.7 months for a café — not credible to an investor.
- Research claims dominated by **macro inflation/GDP**, not Riyadh café competitive set or rent comps.
- Pricing evidence reported as not found / partial — yet GO still issued.

### Missing information
- Rent SAR/m², seating capacity, average ticket, daily covers  
- Competitor price ladder for specialty coffee in Riyadh  
- Municipal / balady / SFDA licensing path specifics  
- Working capital and fit-out CAPEX aligned to 450k  

### UX observations
PASS — founder can see where they are and that a report exists.  
Arabic toggle works. Evidence modal is discoverable.

### Trust observations
FAIL — “Why should I believe this?” fails once assumptions look like a consulting firm, not a coffee shop. RQ UI explains *source preference*, not *model fit*.

### Recommended improvements (document only)
1. Bind assumption schemas tightly to archetype + industry (F&B ≠ professional services).  
2. Enforce investment budget as a hard constraint on CAPEX assumptions.  
3. Block GO when critical pricing/rent evidence is NOT_FOUND.  
4. Prefer local competitive/pricing claims over repeated CPI headlines.

---

## Case 2 — Industrial (Jeddah plastic recycling)

### Scenario source classification
**REAL_USER_FLOW** — same live product path and persisted Study/Research/Financial/Risk state.  
**Not** SEEDED_VALIDATION. **Not** MOCK_ONLY.

### Business scenario
Small PET/HDPE recycling + pelletizing plant in Jeddah industrial area, budget **~3.5M SAR**. Need supply chain, CAPEX, regulation, demand, ops risk.
### Input
- Industry: industrial  
- Investment: 3,500,000 SAR  
- Archetype: industrial  
- Briefing: supply, CAPEX, Saudi regs, demand, risks  

### Workflow result
Reached **Report Ready** with verdict **NO_GO**.  
RQ observability present; market research status stronger than Case 1 (verified/partial mix).

### Strengths
- System **can say no** — important for investor trust culture.
- Risks mention licensing (SASO-like), feedstock volatility, pellet demand uncertainty — directionally industrial.
- Claims include plant/supply/regulation language beyond pure macro (alongside GASTAT noise).

### Weaknesses
- **Broken unit economics:** e.g. machinery CAPEX ~10,000 with selling price ~1,200,000 / unit and very low utilisation — not a serious plant model.
- Report mixes **USD** language with a SAR-budget Saudi study.
- NPV ~-10,000 with undefined IRR — looks like a placeholder failure, not a grounded industrial model.
- Same inflation claim spam in RQ list as Case 1 — weak differentiation for complex ops.

### Missing information
- Realistic equipment package & civil works CAPEX in SAR  
- Feedstock collection contracts / tipping fees  
- Gate fees vs virgin resin price parity  
- Environmental permit pathway (NCEC / industrial city rules)  
- Offtake MOUs or price assumptions for recycled pellets  

### UX observations
PASS for navigation; FAIL for financial readability (USD, unusable IRR messaging in an industrial CAPEX story).

### Trust observations
FAIL — NO_GO may be directionally safe, but for the **wrong quantitative reasons**. An industrial founder cannot audit the model.

### Recommended improvements (document only)
1. Industrial schema: tonnes/year, yield %, electricity, labour, virgin vs recycled price spread.  
2. Currency consistency (SAR) across report + finance.  
3. Capex floors / sanity checks before verdict.  
4. Separate regulatory evidence pack (SASO, environmental) from CPI news.

---

## Case 3 — Digital (SME accounting SaaS / ZATCA)

### Scenario source classification
**REAL_USER_FLOW** — same live product path and persisted Study/Research/Financial/Risk state.  
**Not** SEEDED_VALIDATION. **Not** MOCK_ONLY.

### Business scenario
B2B SaaS accounting/invoicing for Saudi micro/SMEs with ZATCA e-invoicing readiness; budget **~800,000 SAR**.

### Input
- Industry: technology  
- Investment: 800,000 SAR  
- Archetype: saas_digital  
- Briefing: market size, competitors, pricing/CAC, scalability, go/no-go  

### Workflow result
Reached **Report Ready** with verdict **GO_WITH_CONDITIONS**.  
Assumptions include SaaS-native fields (customers, pricing, ARR, CAC, churn, channels).  
Risks mention CAC inflation, churn, data-residency — relevant.

### Strengths
- Best archetype fit of the three.
- Decision language matches digital business vocabulary.
- RQ observability still available; journey complete.

### Weaknesses
- **Internal finance contradiction:** positive NPV (~2.18M) while IRR and payback **cannot be calculated** because cash flows never recover investment — a founder/investor will stop trusting the engine immediately.
- Claims still overweight generic GASTAT inflation vs ZATCA/competitor/pricing evidence.
- ARR 1.2M with 200 customers @ 500 and CAC/churn defaults feel template-ish; competitor landscape thin in claim list.

### Missing information
- Named competitors (Qoyod, Daftra, Wafeq, Zoho, etc.) with price bands  
- ZATCA phase requirements / integration cost  
- Sales cycle & paid CAC channels in KSA  
- Gross margin / hosting / support cost stack  
- Path from 800k runway to ARR targets  

### UX observations
PASS — SaaS classification and report are readable.  
FAIL on metric coherence (NPV vs payback/IRR messages).

### Trust observations
FAIL for investment use — contradictory finance destroys “why believe this?” even when risks sound smart.

### Recommended improvements (document only)
1. Consistency gate: do not show GO if payback never recovers while NPV is celebrated.  
2. Force digital research prompts toward competitors, ZATCA, pricing pages.  
3. Show unit economics (LTV/CAC) explicitly in report, not only NPV.

---

## Separated findings (integrity buckets)

### A. Real workflow validation (REAL_USER_FLOW)

All scorecard judgments in this report come from **real persisted product runs**:

| Case | Study persistence | Research | Financial / Risk / Verdict |
|------|-------------------|----------|----------------------------|
| 1 SME | Persisted study id + timestamps | Live connector attempts + knowledge hits; RQ observability from research context | GO_WITH_CONDITIONS + NPV/IRR present |
| 2 Industrial | Persisted study id + timestamps | Live connector attempts + knowledge hits; RQ observability present | NO_GO + financials present |
| 3 Digital | Persisted study id + timestamps | Live connector attempts + blocked Monsha’at + knowledge hits; RQ present | GO_WITH_CONDITIONS + NPV present (IRR/payback inconsistent) |

These runs validate **product behaviour**, including failures of trust/model-fit. Failures are product gaps, not test-harness gaps.

### B. Seeded validation (SEEDED_VALIDATION)

**None used for this sprint’s scorecard.**

No approved isolated fixture was injected. No `seed-research-quality` (or similar) call was part of the case evidence.  
Therefore readiness is **not** argued from seeded demos.

### C. Mock-only (MOCK_ONLY)

**None used.** No UI-only simulation without backend persistence was accepted.

### D. Missing capabilities (documented only — not fixed)

Documented product gaps discovered on REAL_USER_FLOW (do not treat as seeded/mock):

1. Archetype/industry assumption schema misfit (F&B coffee → consulting drivers).  
2. Investment budget not enforced as CAPEX constraint.  
3. Research claim relevance too macro-generic for sector decisions.  
4. Evidence gaps (e.g. pricing NOT_FOUND) do not hard-block optimistic GO.  
5. Financial coherence failures (NPV vs IRR/payback; USD vs SAR).  
6. Industrial unit economics not credible at plant scale.  
7. Sector packs thin for F&B comps, industrial offtake, ZATCA/SaaS competitors.

---

## Final sections

### 1. Current Product Strengths
- Full study journey is **shippable as a guided UX** (classification → report).
- Research Quality **observability** (preferred official source, freshness unknown, evidence drawer) is visible to non-engineers.
- Bilingual path works.
- System can produce **conditional GO** and **NO_GO**.
- Digital archetype assumptions are closer to real SaaS language than other cases.

### 2. Current Product Gaps
- Archetype/industry **assumption templates misfire** (coffee → consulting economics).
- Research corpus often **macro-generic**, not decision-critical for the idea.
- Financial engine can emit **non-investable / contradictory** metrics.
- Currency and unit conventions inconsistent.
- Pricing evidence gaps do not hard-stop optimistic verdicts.
- Risks panel sometimes skipped in UI presence even when report lists risks.

### 3. Critical gaps before commercialization
1. **Model-fit integrity:** wrong-schema assumptions must be impossible for a given archetype.  
2. **Evidence-to-verdict coupling:** missing pricing/rent/offtake evidence must downgrade or block GO.  
3. **Financial coherence:** NPV/IRR/payback/currency must be mutually consistent and SAR-native.  
4. **Sector research depth** for F&B, industrial, and regulated SaaS (ZATCA).  
5. Merge/stabilize 8C.3 on `main` before any commercial claims on default branch.

### 4. Recommended roadmap priority
1. **Assumption schema correctness + budget constraints** (highest ROI for trust).  
2. **Financial trust gates** (contradiction blockers, SAR, sanity ranges).  
3. **Sector research packs** (competitors, pricing, regulation) before more agents/RAG.  
4. Then UX polish / Phase 9A feature expansion.

### 5. Phase 9A recommendation

**DELAY**

**Reasons:**
- Product validation shows workflow maturity but **decision trust failure** on realistic Saudi cases.
- Shipping Phase 9A features before fixing model-fit and financial coherence would amplify wrong confidence.
- Owner asked for validation-only; commercialization blockers are documented, not fixed here.

---

## Scorecard (owner format)

| Gate | Result |
|------|--------|
| PRODUCT VALIDATION STATUS | **COMPLETED** |
| Baseline SHA | `93d6ed378b345565e7eee06a583ef836998e44a5` (Phase 8C.3 tip) |
| Cases Tested | 3 |
| Case 1 SME | **FAIL** |
| Case 2 Industrial | **FAIL** |
| Case 3 Digital | **FAIL** |
| Research Quality | **FAIL** (observability PASS; relevance/decision-coupling FAIL) |
| Evidence Trust | **FAIL** |
| User Experience | **PASS** |
| Business Value | **FAIL** |
| Scenario source classes | **REAL_USER_FLOW ×3** (0 seeded, 0 mock-only) |
| Phase 9A | **DELAY** |

### Top Strengths
1. Complete guided study journey to a written verdict.  
2. Research Quality observability UX (official preference + freshness + drawer).  
3. Ability to return NO_GO / conditional GO.

### Top Gaps
1. Wrong-business assumptions (especially SME services).  
2. Generic research claims vs idea-specific evidence.  
3. Contradictory / non-credible financial outputs.

### Critical Issues
1. Coffee shop evaluated with consulting P&L → false GO confidence.  
2. Industrial CAPEX/price units not credible.  
3. SaaS positive NPV with impossible payback/IRR.

### Artifacts
- Report: `docs/validation/PRODUCT_VALIDATION_SPRINT_REPORT.md`  
- Evidence JSON: `docs/validation/evidence/`  
- Screenshots/run logs: `/opt/cursor/artifacts/product-validation/`  
- Walkthrough copies: `/opt/cursor/artifacts/product-validation-walkthrough/`

---

## STOP

Do **not** start Phase 9A.  
Do **not** claim product ready from MOCK_ONLY or seeded-only evidence.  
Await owner review.
