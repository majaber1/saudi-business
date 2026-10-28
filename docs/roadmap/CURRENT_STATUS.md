# Current status

Updated: 2026-10-29. This file is the resume point for another machine. The remote tip is authoritative only after `git ls-remote` matches local `HEAD`. Do not treat a local-only commit as synchronized.

## Identity

| Item | Value |
| --- | --- |
| Repository | https://github.com/majaber1/saudi-business |
| Feature branch | `saudi-business-completion` |
| Worktree | `saudi-business-completion-20261028` |
| `origin/main` | `56ca05b43dee3cc097e4c04e7b096d13df4b98f3` |
| Financial-trust commit | `8f9eac644f87a9ee0eaa93e45ae9b7e46deaf0c0` |
| Parent of that commit | `56ca05b43dee3cc097e4c04e7b096d13df4b98f3` |
| Owner-decision commit | `c945ac498f883c357c8efb3a7d1b158a6b955393` |
| Remote branch | https://github.com/majaber1/saudi-business/tree/saudi-business-completion |
| Production deploy | Still `56ca05b`. Not deployed from this branch. |

`origin/main` was fetched on 2026-10-28 and matched `git ls-remote` for `refs/heads/main`. It had not moved past `56ca05b`.

The owner-decision commit `c945ac498f883c357c8efb3a7d1b158a6b955393` matched `git ls-remote` for `refs/heads/saudi-business-completion`. `origin/main` remained `56ca05b43dee3cc097e4c04e7b096d13df4b98f3`. Confirm the tip again after the status-note push.

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
| 4 One workspace journey | Partial | The Riyadh coffee study now records an owner rejection of `INSUFFICIENT_EVIDENCE` without changing that recommendation. Accepting the same analysis is refused. Request Modification is unit-tested and was not clicked on that study. |
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

Research activation command, same worktree:

`python -m pytest tests/test_stage2_market_intelligence.py tests/test_stage3_archetype_financials.py -q --tb=short`

Result: **26 passed**.

Financial, research, and authorization command, same worktree:

`python -m pytest tests/test_financial_trust_sprint.py tests/test_financial_trust_hardening.py tests/test_financial_analyst_prompt.py tests/test_financial_projection.py tests/test_decision.py tests/test_scenarios.py tests/test_citation_critic.py tests/test_phase8a_research_intelligence.py tests/test_phase8b_controlled_market_research.py tests/test_auth.py tests/test_auth_hardening.py tests/test_auth_privilege.py tests/test_router_authz.py tests/test_account_security.py tests/test_projects_auth.py -q --tb=line`

Result: **201 passed**.

Local isolated Postgres browser study: the coffee workspace showed GASTAT source URLs, a pre-tax monthly net, a stale banner after editing rent, and a recalculated net of -1,600 SAR after the base case was updated. A second study, `study_736acb38212a`, labeled the missing model as a deterministic fallback in Arabic and English. This is not a production acceptance pass. Search and Groq were not available to that process.

Published-date command, same worktree:

`python -m pytest tests/test_phase7a_source_foundation.py tests/test_knowledge_intelligence_learning.py tests/test_stage2_market_intelligence.py -q --tb=short`

Result: **28 passed**, 1 failed. That failure was `test_i_mcp_boundary_smoke` while `mcp` 2.0.0 was installed. The declared range is `mcp>=1.28,<2`.

Search-client and MCP command, after installing `mcp` 1.30.0:

`python -m pytest tests/test_stage2_market_intelligence.py tests/test_phase7a_source_foundation.py::test_i_mcp_boundary_smoke tests/test_phase7b_gastat_live_source.py::test_l_mcp_source_tool_boundary -q --tb=short`

Result: **17 passed**. `test_l_mcp_source_tool_boundary` also fetched GASTAT through the existing connector. That is not a web-search result.

Acceptance recheck on 2026-10-29, same worktree:

`python -m pytest tests/test_stage2_market_intelligence.py tests/test_stage3_archetype_financials.py tests/test_financial_trust_sprint.py tests/test_financial_trust_hardening.py tests/test_citation_critic.py tests/test_phase8a_research_intelligence.py tests/test_phase7a_source_foundation.py::test_i_mcp_boundary_smoke tests/test_phase7b_gastat_live_source.py::test_l_mcp_source_tool_boundary -q --tb=line`

Result: **72 passed**. A direct call with an empty environment returned `BLOCKED` / `NO_ALLOWLISTED_PROVIDER_CONFIGURED` and zero results. No browser journey was repeated. The full customer workflow remains not accepted.

Owner-decision command, same worktree:

`python -m pytest tests/test_owner_decision.py tests/test_stage3_archetype_financials.py tests/test_v2_study_engine.py -q --tb=short`

Result: **77 passed**, 6 `datetime.utcnow` deprecation warnings. Exit code 0.

Browser check on isolated study `study_884fa2d78ce9`: the owner panel showed `INSUFFICIENT_EVIDENCE`. Reject recorded `reject` at `2026-10-28T21:41:25.256773+00:00`, analysis version 0. A following accept showed "تم رفض هذه النسخة. لا يمكن قبولها قبل تغيير التحليل." and left the recorded action as reject. Refresh kept that record. This is not a live-search or live-model acceptance pass. No user reference images were available; the only image in the repo is `apps/web/app/icon.svg`.

## Acceptance score

This is not a full acceptance pass. Checked again on 2026-10-28. `GROQ_API_KEY` remains on Vercel only and was not decrypted. `TAVILY_API_KEY` and `BRAVE_SEARCH_API_KEY` are absent locally and on both Vercel projects. The search client is implemented and fixture-tested. Runtime search stays `BLOCKED` until a key is present, and no live search result exists.

| Stage | Status |
| --- | --- |
| Idea captured | Partial — earlier local coffee studies exist |
| Real model classification, risks, and explanation | BLOCKED — no local Groq credential |
| Official research | Partial — GASTAT and MISA pages were retrieved with verification on |
| Competitors and prices | BLOCKED — client is implemented and fixture-tested; no live credential and no live result |
| Evidence | Partial — official claims only; competitor and price are `NOT_FOUND` |
| Owner assumptions | Partial — owner-confirmed on the earlier coffee study, not model-drafted |
| Financial projection | Partial — pre-tax coffee lines only; not investment-grade |
| Scenario modification and stale recommendation | Partial — rent edit on the earlier study |
| Decision | Partial — owner rejection recorded on the coffee study; recommendation stayed `INSUFFICIENT_EVIDENCE` |
| Owner action on the decision | Partial — reject persisted after refresh; same-analysis accept was refused. Request Modification is unit-tested only |
| Report | Partial — downloaded report context carries the financial ceiling, pre-tax label, and owner line. A downloaded file was not opened in the browser |
| Refresh and sign-in persistence | Partial — verified for `study_884fa2d78ce9` only |
| Arabic and English | Partial — chrome and the fallback label switched; some study text stayed in the study language |

## Blockers

Stage 2 is not complete. These items stay open:

- General Saudi search stays BLOCKED at runtime. `TAVILY_API_KEY` and `BRAVE_SEARCH_API_KEY` are absent locally and are not set on the Vercel projects. The client can call either provider when a key is present. No live search was run, and no competitor or price URL was produced.
- `GROQ_API_KEY` is set on the Vercel web and API projects. It is not in the local process, and the production value was not decrypted. Classification on this machine is a deterministic fallback.
- Monsha'at has no live connector. The planner reason remains `BLOCKED_EXTERNAL_REACHABILITY`. The homepage returned HTTP 200 with certificate verification on when Python used the certifi bundle. The default Windows OpenSSL CA file failed the same hosts with `CERTIFICATE_VERIFY_FAILED`. Verification was not disabled.
- GASTAT live retrieval succeeded through the existing connector, which uses httpx and certifi with verification on. The default OpenSSL CA file on this machine does not trust that chain.
- MISA homepage and the national investment strategy page returned HTTP 200 on 2026-10-27 with verification on.
- Competitor and price evidence for the coffee study were NOT_FOUND.
- Production and `main` stay at `56ca05b` until the owner approves a release.

## Safety

No force-push. No merge to `main`. No production deploy. No destructive migration. Secrets, `.env`, dumps, and machine-specific credentials are not part of this branch.
