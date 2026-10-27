# Current status

Updated: 2026-10-28. This file is the resume point for another machine. The remote tip is authoritative only after `git ls-remote` matches local `HEAD`. Do not treat a local-only commit as synchronized.

## Identity

| Item | Value |
| --- | --- |
| Repository | https://github.com/majaber1/saudi-business |
| Feature branch | `saudi-business-completion` |
| Worktree | `saudi-business-completion-20261028` |
| `origin/main` | `56ca05b43dee3cc097e4c04e7b096d13df4b98f3` |
| Financial-trust commit | `8f9eac644f87a9ee0eaa93e45ae9b7e46deaf0c0` |
| Parent of that commit | `56ca05b43dee3cc097e4c04e7b096d13df4b98f3` |
| Resume-point commit | `987d7ed5f967b1acd0b247e4e40f108a7b176d61` |
| Remote branch | https://github.com/majaber1/saudi-business/tree/saudi-business-completion |
| Production deploy | Still `56ca05b`. Not deployed from this branch. |

`origin/main` was fetched on 2026-10-28 and matched `git ls-remote` for `refs/heads/main`. It had not moved past `56ca05b`.

Remote verification before research connectivity: local `HEAD` and `git ls-remote origin refs/heads/saudi-business-completion` both returned `987d7ed5f967b1acd0b247e4e40f108a7b176d61`. Confirm the tip again after the next push.

## Preserved checkouts

The original dirty checkout was not reset, cleaned, or checked out onto this branch.

| Checkout | Branch | HEAD | State |
| --- | --- | --- | --- |
| `Saudi-Business` | `product-readiness/service-architecture` | `ec33176ba17860454817c8a67c7f3566f15e19c4` | Dirty. Tracked edits and untracked files remain, including colliding migrations `0027_v2_scenario_link` and `0028_v2_output_links`. |
| Preservation copy | n/a | n/a | `saudi-business-preservation-20261028-0003` — 81 files verified by SHA256. |
| Recovery worktree | `recovery/financial-trust-20261028` | `8f9eac644f87a9ee0eaa93e45ae9b7e46deaf0c0` | Clean. Same trust commit as this branch. Do not develop there. |

## Completed stages

| Stage | Status | Notes |
| --- | --- | --- |
| 0 Baseline and architecture docs | Complete on this branch | `docs/architecture/CURRENT_ARCHITECTURE.md`, `TARGET_ARCHITECTURE.md`, `FLOWCHARTS.md`, `docs/roadmap/FEATURE_STATUS.md`, `COMPLETION_BACKLOG.md`. |
| 1 Financial trust | Complete on this branch, not released | Estimated 55% and 45% costs cannot authorize GO. Ambiguous discount rates are not divided by 100. Missing `opex_annual` is not zero. |
| 2 Real Saudi research | Partial | GASTAT pages were retrieved with verification on. Competitor and price search stayed NOT_FOUND. No allowlisted search credential exists. Monsha'at has no live connector. |
| 3 Archetype financials | Partial | Specialty coffee and Saudi SaaS line items are calculated and shown in the study workspace. Tax lines and other archetypes are not included. |
| 4 One workspace journey | Partial | A local Riyadh coffee study showed line items, a stale banner after a rent edit, and a recalculated pre-tax net. The recommendation ceiling stayed INSUFFICIENT_EVIDENCE. Approve, Reject, and Request Modification are not one completed journey. |
| 5 Integration, security, browser, non-prod Postgres | Partial | One isolated Postgres 16 browser study was run. The security suite and a full acceptance pass were not run. |
| 6 Release | Not started | Merge, production migration, and deploy need explicit owner approval. |

## Tests

Stage 1 command, run in the recovery worktree before this branch was published:

`python -m pytest tests/test_financial_trust_sprint.py tests/test_financial_trust_hardening.py tests/test_financial_analyst_prompt.py tests/test_financial_projection.py tests/test_financial_engine.py tests/test_decision.py tests/test_scenarios.py tests/test_v2_study_engine.py tests/test_phase8a_research_intelligence.py tests/test_wave65_lifecycle.py -q --tb=line`

Result: **130 passed**, 6 `datetime.utcnow` deprecation warnings. Exit code 0. Python 3.13.14 locally; CI is 3.11.

Citation-critic command, run in `saudi-business-completion-20261028`:

`python -m pytest tests/test_citation_critic.py tests/test_phase8a_research_intelligence.py tests/test_phase8a_final_trust_gate.py tests/test_phase8b_controlled_market_research.py -q --tb=line`

Result: **54 passed**. Exit code 0.

Stage 2 commands, same worktree:

`python -m pytest tests/test_stage2_market_intelligence.py tests/test_phase8b_controlled_market_research.py tests/test_citation_critic.py tests/test_phase8a_research_intelligence.py tests/test_phase8a_final_trust_gate.py tests/test_financial_trust_sprint.py -q --tb=line`

Result: **73 passed**.

`python -m pytest tests/test_phase8c1_research_persistence.py tests/test_phase8c2_research_quality.py tests/test_phase8c3_research_observability.py tests/test_financial_trust_hardening.py tests/test_decision.py tests/test_scenarios.py -q --tb=line`

Result: **123 passed**.

Stage 3 command, same worktree:

`python -m pytest tests/test_stage3_archetype_financials.py tests/test_financial_trust_sprint.py tests/test_product_hardening_sprint.py tests/test_stage2_market_intelligence.py tests/test_financial_analyst_prompt.py tests/test_archetype_e2e_scenarios.py -q --tb=line`

Result: **42 passed**.

Workspace integration command, same worktree:

`python -m pytest tests/test_stage3_archetype_financials.py tests/test_financial_trust_sprint.py tests/test_v2_study_engine.py -q --tb=line`

Result: **72 passed**.

Research connectivity command, same worktree:

`python -m pytest tests/test_stage3_archetype_financials.py -q --tb=line`

Result: **11 passed**. That file now covers the percent-field label and the owner rent edit updating the base case.

Local isolated Postgres browser study: the coffee workspace showed GASTAT source URLs, a pre-tax monthly net, a stale banner after editing rent, and a recalculated net of -1,600 SAR after the base case was updated. This is not a production acceptance pass.

Known local-environment failure, not re-run and not a trust regression: `tests/test_phase7b_gastat_live_source.py::test_l_mcp_source_tool_boundary` failed earlier because the `mcp` package is not installed.

## Blockers

Stage 2 is not complete. These items stay open:

- General Saudi search stays BLOCKED. `TAVILY_API_KEY` and `BRAVE_SEARCH_API_KEY` are absent locally and are not set on the Vercel projects. No results were invented.
- Monsha'at has no live connector. The planner reason remains `BLOCKED_EXTERNAL_REACHABILITY`. The homepage returned HTTP 200 with certificate verification on when Python used the certifi bundle. The default Windows OpenSSL CA file failed the same hosts with `CERTIFICATE_VERIFY_FAILED`. Verification was not disabled.
- GASTAT live retrieval succeeded through the existing connector, which uses httpx and certifi with verification on. The default OpenSSL CA file on this machine does not trust that chain.
- MISA activity pages were fetched with verification on. The homepage connection was reset once and returned HTTP 200 on an earlier request.
- `GROQ_API_KEY` is not in the local environment. Classification used the deterministic fallback and told the owner the model was unavailable.
- Competitor and price evidence for the coffee study were NOT_FOUND.
- Production and `main` stay at `56ca05b` until the owner approves a release.

## Safety

No force-push. No merge to `main`. No production deploy. No destructive migration. Secrets, `.env`, dumps, and machine-specific credentials are not part of this branch.
