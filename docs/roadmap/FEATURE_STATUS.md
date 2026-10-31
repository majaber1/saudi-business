# Feature status

Measured on `recovery/financial-trust-20261028` against production SHA `56ca05b`. Statuses: VERIFIED, PARTIAL, FAILED, BLOCKED, NOT TESTED, NOT STARTED.

| Feature | Status | Evidence |
| --- | --- | --- |
| Production research node still on the graph | VERIFIED | `ai_engine/orchestrator.py` registers `research`. `test_research_node_remains_on_the_production_graph` passed. |
| Single Alembic head `0031_research_runs` | VERIFIED | Chain ends at `0031_research_runs`. Colliding dirty-tree revisions were not applied. |
| Phase 8 research modules present | VERIFIED | `ai_engine/research/**` remains. `tests/test_phase8a_research_intelligence.py` passed in the Stage 1 run. |
| Phase 9 workspace route present | VERIFIED | `apps/web/app/projects/[projectId]/studies/[studyId]/workspace/page.tsx` exists. Browser pass: NOT TESTED. |
| GASTAT connector | PARTIAL | Live page `https://www.stats.gov.sa/en/w/news/180` returned HTTP 200 on 2026-10-27 with verification on. Coffee-specific competitor search did not match that page. |
| MISA connector | PARTIAL | `https://misa.gov.sa/` and the national investment strategy page returned HTTP 200 on 2026-10-27 with verification on. |
| Monsha'at connector | BLOCKED | Homepage `https://www.monshaat.gov.sa/ar` returned HTTP 200 with verification on. No approved page list and no connector. Planner reason remains `BLOCKED_EXTERNAL_REACHABILITY`. |
| Allowlisted web search | BLOCKED at runtime | Tavily and Brave clients are implemented. Fixture tests cover URL filtering, deduplication, timeout, rate limit, and a 5xx retry. No local or Vercel key exists, so no live call was made. |
| Groq classification | BLOCKED locally | `GROQ_API_KEY` is set on both Vercel projects and is absent from this machine. The value was not decrypted. The workspace labels the keyword result `deterministic_fallback`. |
| Competitor identity, URL, and timestamp | VERIFIED | A verified record requires all three. Name-only, missing URL, invalid timestamp, and geographic mismatch stay unverified. Covered by `tests/test_stage2_market_intelligence.py`. |
| Citation critic for official and document claims | VERIFIED | `ai_engine/research/citation_critic.py` drops those claims when the URL is not http(s) and does not invent a URL. `tests/test_citation_critic.py` plus Phase 8A/8B research tests: 54 passed. |
| 55% and 45% cost fills cannot authorize GO | VERIFIED | Fills stay labeled `UNVERIFIED_ESTIMATE`. `tests/test_financial_trust_sprint.py` passed. |
| Missing `opex_annual` is not treated as zero | VERIFIED | `project_cash_flows` raises. Compute and scenario APIs return 422. Covered by projection, scenario, and decision tests. |
| Ambiguous discount rate is not divided by 100 | VERIFIED | `financial-engine/rate_contract.py`. Bare `12` is rejected. Historical `0.10` stays a ratio. |
| LLM cannot override deterministic cost or discount | VERIFIED | `_merge_extract` keeps deterministic discount and does not hide an estimated cost behind an LLM cost. |
| Deterministic policy is the recommendation ceiling | VERIFIED | `apply_investment_trust` runs after `apply_decision_safety` and after the blocked-financial early return. |
| Negative NPV, contradictory evidence, impossible margins, invalid units, provider failure | PARTIAL | Existing financial and evidence gates cover several of these. A single Stage 1 case for every failure mode is not claimed. |
| Archetype line-item model, monthly cash flow, real what-if | PARTIAL | Specialty coffee and Saudi SaaS only, in `ai_engine/tools/archetype_lines.py`. `tests/test_stage3_archetype_financials.py` passed with the trust and archetype regressions (42 passed). Other archetypes and tax lines are not in this model. |
| One workspace journey with Approve / Reject / Request Modification | PARTIAL | `POST /api/v2/studies/{id}/decision/owner` records approve, reject, or request_modification. Approval does not change the verdict. A rejection of the same analysis cannot be accepted. On 2026-10-31 the coffee study browser click persisted `request_modification`, returned to assumption review, kept `INSUFFICIENT_EVIDENCE`, and survived refresh. The Saudi SaaS journey is still NOT TESTED. |
| Bilingual RTL report as the single artifact | PARTIAL | PDF and DOCX exports include the persisted operating lines, monthly net, pre-tax label, and owner decision. On 2026-10-31 the live English PDF and Arabic DOCX for `study_884fa2d78ce9` contained 52000, 20000, 18000, 15600, -1600, and -19200. |
| Integration, security, and browser end-to-end | PARTIAL | Auth and financial regression tests passed. One isolated Postgres browser study ran. Full model-written acceptance did not run because Groq and search are not available locally. |
| Non-production Postgres migration of this branch | PARTIAL | Isolated Postgres 16 on `127.0.0.1:54329` applied the chain through `0031_research_runs`. This was not a production migration. |
| Release: merge, production migration, deploy | NOT STARTED | Explicit owner approval is still required. |
| `mcp` package in the local interpreter | VERIFIED | `mcp` is a declared runtime dependency (`mcp>=1.28,<2`). The machine had `mcp` 2.0.0, which does not provide the pinned FastMCP import. Installing `mcp` 1.30.0 made `test_i_mcp_boundary_smoke` and `test_l_mcp_source_tool_boundary` pass. |

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

The Riyadh coffee browser journey is PARTIAL: reject, blocked re-approval, and Request Modification were exercised on isolated Postgres. The Saudi SaaS browser journey remains **NOT TESTED**.
