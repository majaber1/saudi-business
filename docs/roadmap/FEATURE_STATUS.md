# Feature status

Measured on `recovery/financial-trust-20261028` against production SHA `56ca05b`. Statuses: VERIFIED, PARTIAL, FAILED, BLOCKED, NOT TESTED, NOT STARTED.

| Feature | Status | Evidence |
| --- | --- | --- |
| Production research node still on the graph | VERIFIED | `ai_engine/orchestrator.py` registers `research`. `test_research_node_remains_on_the_production_graph` passed. |
| Single Alembic head `0031_research_runs` | VERIFIED | Chain ends at `0031_research_runs`. Colliding dirty-tree revisions were not applied. |
| Phase 8 research modules present | VERIFIED | `ai_engine/research/**` remains. `tests/test_phase8a_research_intelligence.py` passed in the Stage 1 run. |
| Phase 9 workspace route present | VERIFIED | `apps/web/app/projects/[projectId]/studies/[studyId]/workspace/page.tsx` exists. Browser pass: NOT TESTED. |
| GASTAT and MISA connectors | PARTIAL | Code paths exist. Live reachability was not re-measured in this session. |
| Monsha'at connector | BLOCKED | `BLOCKED_EXTERNAL_REACHABILITY` in `ai_engine/research/planner.py`. Not faked. |
| Allowlisted web search | NOT STARTED | `ai_engine/tools/search.py` returns `not_implemented`. |
| Competitor identity, URL, and timestamp | NOT STARTED | Current competitor handling extracts names. It is not a sourced competitor record. |
| Critic node | NOT STARTED | No critic step rejects unsourced claims before they enter the decision. |
| 55% and 45% cost fills cannot authorize GO | VERIFIED | Fills stay labeled `UNVERIFIED_ESTIMATE`. `tests/test_financial_trust_sprint.py` passed. |
| Missing `opex_annual` is not treated as zero | VERIFIED | `project_cash_flows` raises. Compute and scenario APIs return 422. Covered by projection, scenario, and decision tests. |
| Ambiguous discount rate is not divided by 100 | VERIFIED | `financial-engine/rate_contract.py`. Bare `12` is rejected. Historical `0.10` stays a ratio. |
| LLM cannot override deterministic cost or discount | VERIFIED | `_merge_extract` keeps deterministic discount and does not hide an estimated cost behind an LLM cost. |
| Deterministic policy is the recommendation ceiling | VERIFIED | `apply_investment_trust` runs after `apply_decision_safety` and after the blocked-financial early return. |
| Negative NPV, contradictory evidence, impossible margins, invalid units, provider failure | PARTIAL | Existing financial and evidence gates cover several of these. A single Stage 1 case for every failure mode is not claimed. |
| Archetype line-item model, monthly cash flow, real what-if | NOT STARTED | Production math is a pre-tax annual proxy with ±20% scenario multipliers. |
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
