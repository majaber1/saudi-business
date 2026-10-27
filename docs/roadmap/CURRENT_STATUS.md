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
| Resume-point commit | `748ce3cde238ac9d24c3e66f9dd98e3fee899d03` |
| Remote branch | https://github.com/majaber1/saudi-business/tree/saudi-business-completion |
| Production deploy | Still `56ca05b`. Not deployed from this branch. |

`origin/main` was fetched on 2026-10-28 and matched `git ls-remote` for `refs/heads/main`. It had not moved past `56ca05b`.

Remote verification on 2026-10-28: local `HEAD` and `git ls-remote origin refs/heads/saudi-business-completion` both returned `748ce3cde238ac9d24c3e66f9dd98e3fee899d03`. The citation-critic commit is a child of that SHA. After pulling, confirm the branch tip again with `git rev-parse HEAD` and `git ls-remote`.

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
| 2 Real Saudi research | Partial | Citation critic rejects official or document claims with no http(s) URL and does not invent one. GASTAT and MISA code remains. Monsha'at is `BLOCKED_EXTERNAL_REACHABILITY`. Web search returns `not_implemented`. Neither was faked. |
| 3 Archetype financials | Not started | |
| 4 One workspace journey | Not started | |
| 5 Integration, security, browser, non-prod Postgres | Not tested | |
| 6 Release | Not started | Merge, production migration, and deploy need explicit owner approval. |

## Tests

Stage 1 command, run in the recovery worktree before this branch was published:

`python -m pytest tests/test_financial_trust_sprint.py tests/test_financial_trust_hardening.py tests/test_financial_analyst_prompt.py tests/test_financial_projection.py tests/test_financial_engine.py tests/test_decision.py tests/test_scenarios.py tests/test_v2_study_engine.py tests/test_phase8a_research_intelligence.py tests/test_wave65_lifecycle.py -q --tb=line`

Result: **130 passed**, 6 `datetime.utcnow` deprecation warnings. Exit code 0. Python 3.13.14 locally; CI is 3.11.

Citation-critic command, run in `saudi-business-completion-20261028`:

`python -m pytest tests/test_citation_critic.py tests/test_phase8a_research_intelligence.py tests/test_phase8a_final_trust_gate.py tests/test_phase8b_controlled_market_research.py -q --tb=line`

Result: **54 passed**. Exit code 0.

Browser: **NOT TESTED**. No database migration was run.

Known local-environment failure, not re-run and not a trust regression: `tests/test_phase7b_gastat_live_source.py::test_l_mcp_source_tool_boundary` failed earlier because the `mcp` package is not installed.

## Blockers

- Monsha'at has no reachable connector. Do not stub a successful response.
- Allowlisted web search is not implemented.
- Competitor rows are still name extraction. A row without identity, URL, and timestamp must not count as evidence. The citation critic does not create those rows.
- Production and `main` stay at `56ca05b` until the owner approves a release.

## Safety

No force-push. No merge to `main`. No production deploy. No destructive migration. Secrets, `.env`, dumps, and machine-specific credentials are not part of this branch.
