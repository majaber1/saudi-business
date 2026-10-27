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
| Resume-point commit | `a49357216dd7e6dd40f6a2edb59f74c5c97cc7e8` |
| Remote branch | https://github.com/majaber1/saudi-business/tree/saudi-business-completion |
| Production deploy | Still `56ca05b`. Not deployed from this branch. |

`origin/main` was fetched on 2026-10-28 and matched `git ls-remote` for `refs/heads/main`. It had not moved past `56ca05b`.

Remote verification before Stage 3: local `HEAD` and `git ls-remote origin refs/heads/saudi-business-completion` both returned `a49357216dd7e6dd40f6a2edb59f74c5c97cc7e8`. Confirm the tip again after the Stage 3 push.

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
| 2 Real Saudi research | Partial | Competitor verification, citation critic, and research-lineage critic are on this branch. Search is BLOCKED. Monsha'at is BLOCKED. GASTAT live retrieval was not verified. MISA homepage returned HTTP 200. Browser journey NOT TESTED. |
| 3 Archetype financials | Partial | Specialty coffee and Saudi SaaS have explicit line items, monthly and annual pre-tax totals, assumption lineage, and driver scenarios. Other archetypes still use the legacy proxy. Tax lines are not included. |
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

Stage 2 commands, same worktree:

`python -m pytest tests/test_stage2_market_intelligence.py tests/test_phase8b_controlled_market_research.py tests/test_citation_critic.py tests/test_phase8a_research_intelligence.py tests/test_phase8a_final_trust_gate.py tests/test_financial_trust_sprint.py -q --tb=line`

Result: **73 passed**.

`python -m pytest tests/test_phase8c1_research_persistence.py tests/test_phase8c2_research_quality.py tests/test_phase8c3_research_observability.py tests/test_financial_trust_hardening.py tests/test_decision.py tests/test_scenarios.py -q --tb=line`

Result: **123 passed**.

Stage 3 command, same worktree:

`python -m pytest tests/test_stage3_archetype_financials.py tests/test_financial_trust_sprint.py tests/test_product_hardening_sprint.py tests/test_stage2_market_intelligence.py tests/test_financial_analyst_prompt.py tests/test_archetype_e2e_scenarios.py -q --tb=line`

Result: **42 passed**.

Browser: **NOT TESTED**. No database migration was run.

Known local-environment failure, not re-run and not a trust regression: `tests/test_phase7b_gastat_live_source.py::test_l_mcp_source_tool_boundary` failed earlier because the `mcp` package is not installed.

## Blockers

Stage 2 is not complete. These items stay open:

- General Saudi search provider is not configured. Status BLOCKED, reason `NO_ALLOWLISTED_PROVIDER_CONFIGURED`.
- Monsha'at TLS/reachability is BLOCKED. Planner reason remains `BLOCKED_EXTERNAL_REACHABILITY`. A verified request failed with `CERTIFICATE_VERIFY_FAILED` (`self-signed certificate in certificate chain`). Certificate verification was not disabled.
- GASTAT TLS verification failed the same way on `www.stats.gov.sa`. The connector code remains. Live retrieval is NOT VERIFIED.
- Live research integration is unverified. MISA's homepage returned HTTP 200 on this machine, and a full study retrieval was not re-run. No proxy variables were set. Python's default CA file was unset, and the same interpreter trusted MISA, so the GASTAT and Monsha'at failures are the chains those hosts presented rather than a global trust-store outage. `openssl` is not installed here, so the issuer name was not printed.
- Browser end-to-end and non-production Postgres are NOT TESTED.
- Production and `main` stay at `56ca05b` until the owner approves a release.

## Safety

No force-push. No merge to `main`. No production deploy. No destructive migration. Secrets, `.env`, dumps, and machine-specific credentials are not part of this branch.
