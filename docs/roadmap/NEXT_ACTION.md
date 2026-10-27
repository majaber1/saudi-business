# Next action

Resume on branch `saudi-business-completion` in worktree `saudi-business-completion-20261028`. Do not use the dirty `Saudi-Business` checkout and do not apply its `0027` / `0028` migration files.

Last verified remote SHA before the Stage 3 line-item commit: `a49357216dd7e6dd40f6a2edb59f74c5c97cc7e8`. After the next push, confirm `git rev-parse HEAD` equals `git ls-remote origin refs/heads/saudi-business-completion`.

## Immediate task

Show the specialty-coffee and Saudi SaaS line items in the study workspace: revenue, rent, payroll, and operating cost for coffee; subscription revenue, acquisition cost, and hosting for SaaS. Display monthly and annual pre-tax totals, the assumption lineage, and the blocked reason when a line is missing or estimated. Do not label that projection as investment-ready.

## Stage 2 blockers to keep visible

- General search: BLOCKED, no allowlisted provider configured.
- Monsha'at: BLOCKED, TLS verification failed and the connector stays `BLOCKED_EXTERNAL_REACHABILITY`.
- GASTAT: TLS verification failed. Do not disable certificate checks.
- Live research integration: NOT VERIFIED. Stage 2 is not complete.

## Do not do

- Do not merge to `main`.
- Do not deploy.
- Do not force-push.
- Do not run a database migration.
- Do not edit the dirty original checkout.
- Do not turn a missing line into zero.
