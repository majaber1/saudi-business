# Current architecture

Status date: 2026-10-28. This describes the recovery line, not the dirty checkout at `Saudi-Business`.

## Baseline

| Item | Value |
| --- | --- |
| Production SHA | `56ca05b43dee3cc097e4c04e7b096d13df4b98f3` (PR #57, 2026-09-15) |
| Recovery branch | `recovery/financial-trust-20261028` |
| Recovery worktree | `saudi-business-recovery-20261028` |
| Alembic head on this line | `0031_research_runs` (single chain from `0001_initial`) |
| Deployed web | Vercel project `saudi-business-web` |
| Deployed API | Vercel project `feasibilityos-ai` |
| Production deploy of the trust changes | Not deployed. Owner approval is required before merge or deploy. |

The original checkout (`product-readiness/service-architecture`, HEAD `ec33176`) stays dirty. Its untracked migrations `0027_v2_scenario_link` and `0028_v2_output_links` collide with production `0027_funding_intelligence` and `0028_knowledge_intelligence`. They are quarantined and must not be applied.

A checksummed copy of that dirty work sits at `saudi-business-preservation-20261028-0003`.

## Runtime

One repository, two applications:

- `apps/web` — Next.js BFF. Session is the HTTP-only cookie `sb_session`. Project isolation is owner / V2 `user_id`.
- `backend` — FastAPI.
- `ai_engine` — LangGraph study runner. `build_graph` in `ai_engine/orchestrator.py` registers `discovery`, `research`, `evidence`, `assumptions`, `financial`, `risk`, `decision`, and `error_handler`. Each user step runs one phase and then ends. The research node is still on the graph.
- `financial-engine` — NPV, IRR, and payback. `rate_contract.py` is the discount-rate boundary used by the recovery branch.
- LLM calls go through `ai_engine/provider.py` (Groq). A missing `GROQ_API_KEY` raises `ProviderUnavailableError`. The model explains. It does not overrule the deterministic trust layer.

## Study surfaces

Two study surfaces exist on this SHA:

- Tabbed study page: `apps/web/app/projects/[projectId]/studies/[studyId]/page.tsx`
- Phase 9 workspace: `apps/web/app/projects/[projectId]/studies/[studyId]/workspace/page.tsx`

They are not one journey yet.

## Research

Live connectors used by `ai_engine/research/service.py`: GASTAT (`stats.gov.sa`) and MISA (`misa.gov.sa`). Both returned HTTP 200 on 2026-10-27 with certificate verification left on. Monsha'at has no connector. Its homepage also returned HTTP 200 with verification on, and the planner reason stays `BLOCKED_EXTERNAL_REACHABILITY`. `ai_engine/tools/search.py` stays `BLOCKED` until `TAVILY_API_KEY` or `BRAVE_SEARCH_API_KEY` is set and a tested client is enabled. A missing `GROQ_API_KEY` is labeled `deterministic_fallback`. It is not shown as an AI suggestion.

## Financial and decision path on this branch

Production `56ca05b` still divides a discount rate greater than 1 by 100 inside the financial analyst, and it can fill operating cost at 55% (services) or 45% (missing or zero cost vector).

This branch changes that contract:

- `financial-engine/rate_contract.py` accepts an explicit `PERCENT` or `RATIO`. A historical API value already inside `[0, 1]` with no representation stays a ratio and is not divided by 100. A value outside that range with no representation is rejected and is not rescaled.
- Illustrative 55% and 45% operating-cost fills remain visible and are tagged `UNVERIFIED_ESTIMATE`. They set `investment_grade=false` and cannot yield `GO` or `GO_WITH_CONDITIONS`.
- A revenue series with an all-zero cost vector is blocked. It is not replaced with a 45% estimate. Legacy `project_cash_flows` raises when `opex_annual` is missing. Explicit zero is still allowed. Stored `FinancialResult` rows are not rewritten.
- `ai_engine/tools/investment_trust.py` is the recommendation ceiling. An ambiguous discount rate forces `INSUFFICIENT_EVIDENCE`. An unverified cost forces `DEFER` when the current verdict would otherwise be favorable. `NO_GO` is left in place.
- Absent discount on the V2 analyst may use `0.12` labeled `SYSTEM_DEFAULT_RATIO`. That default is not a rescaling of a stored user number.
- Cash flows from `run_financial_analysis` are a pre-tax operating proxy (`cash_flow_basis=PRE_TAX_OPERATING_PROXY`). They are not an investment-ready tax model.
- `apply_decision_safety` in `ai_engine/hardening/evidence_gates.py` still runs. The trust layer runs after it.

## What this document does not claim

Browser end-to-end coverage of the trust changes is `NOT TESTED`. No production database migration has been run. A passing unit test is not production readiness.
