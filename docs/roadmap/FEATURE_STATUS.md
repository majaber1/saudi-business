# Feature status

Measured on `recovery/financial-trust-20261028` against production SHA `56ca05b`. Statuses: VERIFIED, PARTIAL, FAILED, BLOCKED, NOT TESTED, NOT STARTED.

| Feature | Status | Evidence |
| --- | --- | --- |
| Production research node still on the graph | VERIFIED | `ai_engine/orchestrator.py` registers `research`. `test_research_node_remains_on_the_production_graph` passed. |
| Single Alembic head `0031_research_runs` | VERIFIED | Chain ends at `0031_research_runs`. Colliding dirty-tree revisions were not applied. |
| Phase 8 research modules present | VERIFIED | `ai_engine/research/**` remains. `tests/test_phase8a_research_intelligence.py` passed in the Stage 1 run. |
| Phase 9 workspace route present | VERIFIED | `apps/web/app/projects/[projectId]/studies/[studyId]/workspace/page.tsx` exists. Browser pass: NOT TESTED. |
| GASTAT connector | PARTIAL | Code remains. Homepage probe on 2026-10-28 failed locally with `CERTIFICATE_VERIFY_FAILED` behind a self-signed chain. Certificate checks were not disabled. Live retrieval: NOT VERIFIED. |
| MISA connector | PARTIAL | Code remains. Homepage returned HTTP 200 on 2026-10-28. A full study retrieval was not re-run. |
| Monsha'at connector | BLOCKED | Planner reason remains `BLOCKED_EXTERNAL_REACHABILITY`. The same local TLS failure occurred. No connector was added and certificate checks were not disabled. |
| Allowlisted web search | BLOCKED | No Tavily, Brave, SerpAPI, Bing, or Google CSE credential is configured. `search_saudi_data` returns `BLOCKED` / `NO_ALLOWLISTED_PROVIDER_CONFIGURED` and an empty result list. |
| Competitor identity, URL, and timestamp | VERIFIED | A verified record requires all three. Name-only, missing URL, invalid timestamp, and geographic mismatch stay unverified. Covered by `tests/test_stage2_market_intelligence.py`. |
| Citation critic for official and document claims | VERIFIED | `ai_engine/research/citation_critic.py` drops those claims when the URL is not http(s) and does not invent a URL. `tests/test_citation_critic.py` plus Phase 8A/8B research tests: 54 passed. |
| 55% and 45% cost fills cannot authorize GO | VERIFIED | Fills stay labeled `UNVERIFIED_ESTIMATE`. `tests/test_financial_trust_sprint.py` passed. |
| Missing `opex_annual` is not treated as zero | VERIFIED | `project_cash_flows` raises. Compute and scenario APIs return 422. Covered by projection, scenario, and decision tests. |
| Ambiguous discount rate is not divided by 100 | VERIFIED | `financial-engine/rate_contract.py`. Bare `12` is rejected. Historical `0.10` stays a ratio. |
| LLM cannot override deterministic cost or discount | VERIFIED | `_merge_extract` keeps deterministic discount and does not hide an estimated cost behind an LLM cost. |
| Deterministic policy is the recommendation ceiling | VERIFIED | `apply_investment_trust` runs after `apply_decision_safety` and after the blocked-financial early return. |
| Negative NPV, contradictory evidence, impossible margins, invalid units, provider failure | PARTIAL | Existing financial and evidence gates cover several of these. A single Stage 1 case for every failure mode is not claimed. |
| Archetype line-item model, monthly cash flow, real what-if | PARTIAL | Specialty coffee and Saudi SaaS only, in `ai_engine/tools/archetype_lines.py`. `tests/test_stage3_archetype_financials.py` passed with the trust and archetype regressions (42 passed). Other archetypes and tax lines are not in this model. |
| One workspace journey with Approve / Reject / Request Modification | PARTIAL | Two surfaces exist. The owner action set is not one completed journey. |
| Bilingual RTL report as the single artifact | PARTIAL | Arabic and English strings exist. A unified report journey was not browser-tested. |
| Integration, security, and browser end-to-end | NOT TESTED | No browser session was run against the trust changes. SSO protects the Vercel domains. |
| Non-production Postgres migration of this branch | NOT TESTED | No migration was added. No database write was run. |
| Release: merge, production migration, deploy | NOT STARTED | Explicit owner approval is still required. |
| `mcp` package in the local interpreter | FAILED | Baseline `test_l_mcp_source_tool_boundary` failed with `RuntimeError: mcp package not installed`. Pre-existing local environment. Not a trust regression. Not re-run after the trust edits. |

## Stage 1 test run

Command, from the recovery worktree, after the trust fixes:

`python -m pytest tests/test_financial_trust_sprint.py tests/test_financial_trust_hardening.py tests/test_financial_analyst_prompt.py tests/test_financial_projection.py tests/test_financial_engine.py tests/test_decision.py tests/test_scenarios.py tests/test_v2_study_engine.py tests/test_phase8a_research_intelligence.py tests/test_wave65_lifecycle.py -q --tb=line`

Result: **130 passed**, 6 deprecation warnings from `ai_engine/knowledge/quality.py` (`datetime.utcnow`). Exit code 0. Duration about 80 seconds. Python on this machine is 3.13. CI is 3.11.

## Stage 2 test run

Commands, from `saudi-business-completion-20261028`:

`python -m pytest tests/test_stage2_market_intelligence.py tests/test_phase8b_controlled_market_research.py tests/test_citation_critic.py tests/test_phase8a_research_intelligence.py tests/test_phase8a_final_trust_gate.py tests/test_financial_trust_sprint.py -q --tb=line`

Result: **73 passed**.

`python -m pytest tests/test_phase8c1_research_persistence.py tests/test_phase8c2_research_quality.py tests/test_phase8c3_research_observability.py tests/test_financial_trust_hardening.py tests/test_decision.py tests/test_scenarios.py -q --tb=line`

Result: **123 passed**.

Browser journey for the Riyadh coffee study and the Saudi SaaS study: **NOT TESTED**. The same two shapes were exercised in unit tests only. No non-production Postgres write was run.
