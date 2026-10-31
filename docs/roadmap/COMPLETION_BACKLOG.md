# Completion backlog

Ordered. Do not start a later stage by faking a blocked dependency. Do not merge, migrate production, or deploy without an explicit owner approval.

## Done on this branch, not released

1. Recovery worktree from `56ca05b`, dirty checkout preserved, colliding revisions quarantined.
2. Financial trust: estimated operating costs and ambiguous discount rates cannot authorize `GO` or `GO_WITH_CONDITIONS`.
3. Targeted regression: 130 passed on the Stage 1 set. See `docs/roadmap/FEATURE_STATUS.md`.

## Stage 2 — real Saudi research

Partial. Do not stub the blocked connectors.

- Citation critic and research-lineage critic are on this branch. They do not invent citations.
- Verified competitor records require identity, an http(s) URL, and a real retrieval timestamp.
- Allowlisted search is `BLOCKED` until a provider credential exists. No results are fabricated.
- GASTAT live retrieval was not verified from this machine. MISA homepage returned HTTP 200. Monsha'at stays `BLOCKED_EXTERNAL_REACHABILITY`.
- Live research browser acceptance for the coffee and SaaS studies is NOT TESTED. Search and Groq remain blocked.

## Stage 3 — archetype financials

Partial for two archetypes only.

- Specialty coffee (`fnb`) projects revenue, rent, payroll, and operating cost from explicit assumptions.
- Saudi SaaS (`saas_digital`) projects subscription revenue, acquisition cost, and hosting.
- Monthly totals sum to the annual pre-tax projection. Tax lines are not included.
- A missing or ambiguous line stays missing and blocks an investment-ready GO.
- An estimated material line stays `UNVERIFIED_ESTIMATE` and forces DEFER.
- Driver scenarios replace a named input. A bare multiplier is rejected.
- Other archetypes still use the existing pre-tax proxy.

## Stage 4 — one workspace journey

Partial.

- The study workspace shows specialty-coffee and Saudi SaaS line items, monthly and annual totals, assumption lineage, and the recommendation ceiling.
- The projection is labeled pre-tax, not investment-ready.
- Editing an assumption marks the previous figures stale and withdraws a favorable verdict until analysis is run again.
- The isolated Postgres coffee study shows the owner decision panel. Reject was recorded in the browser and survived refresh. Accepting that same analysis was refused.
- Request Modification on the coffee study persisted on 2026-10-31. Refresh kept the assumption-review banner and the note. The recommendation stayed `INSUFFICIENT_EVIDENCE`.
- Live search and live model classification remain blocked. See `docs/roadmap/OWNER_ACTION_REQUIRED.md`.

## Stage 5 — integration and security

Partial.

- `tests/test_router_authz.py`, `tests/test_projects_auth.py`, and `tests/test_auth_privilege.py`: 46 passed.
- On 2026-10-31 the live English PDF and Arabic DOCX for the coffee study matched the stored operating figures. `npm run build` in `apps/web` completed.

- Non-production Postgres only. Do not apply `0027_v2_scenario_link` or `0028_v2_output_links` from the dirty checkout.
- Browser end-to-end on the recovery branch.
- Security pass on session cookie, owner isolation, and the new rate boundary.

## Stage 6 — release

Not started.

- Requires owner approval before merge, production migration, or deploy.
- Production SHA remains `56ca05b` until that approval.
