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

---

## Baseline

| Item | Value |
|------|--------|
| Validation product baseline | Phase **8C.3** tip `93d6ed378b345565e7eee06a583ef836998e44a5` |
| Includes | Phase 8C.2 Research Quality Governance + 8C.3 Observability UX |
| `main` at validation start | Phase **8C.2** `9f2eeb511e89b2f71ff3b060d650141c99695884` (PR #51 open) |
| Validation branch | `cursor/product-validation-sprint-1831` |
| Runtime | Local web `:3000` + API `:8000`, PostgreSQL connected, `GROQ_API_KEY` present |
| Method | Real UI workflow (Playwright driver against live servers) — no mock-only verdicts |
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

---

## Case 1 — SME service (Riyadh specialty coffee)

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
| Baseline SHA |  (Phase 8C.3 tip) |
| Cases Tested | 3 |
| Case 1 SME | **FAIL** |
| Case 2 Industrial | **FAIL** |
| Case 3 Digital | **FAIL** |
| Research Quality | **FAIL** (observability PASS; relevance/decision-coupling FAIL) |
| Evidence Trust | **FAIL** |
| User Experience | **PASS** |
| Business Value | **FAIL** |
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
Await owner review.
