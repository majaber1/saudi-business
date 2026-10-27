# Next action

Resume on branch `saudi-business-completion` in worktree `saudi-business-completion-20261028`. Do not use the dirty `Saudi-Business` checkout and do not apply its `0027` / `0028` migration files.

Last verified remote SHA before the Stage 2 commit: `bba2d5e9c794e599319cac81954a597b2ea2d93a`. After the next push, confirm `git rev-parse HEAD` equals `git ls-remote origin refs/heads/saudi-business-completion`.

## Immediate task

Start Stage 3 with the specialty-coffee and Saudi SaaS archetypes.

Add explicit line items for those two archetypes: revenue, rent, payroll, and operating cost for coffee; subscription revenue, acquisition cost, and hosting for SaaS. Keep monthly and annual cash flow labeled as a pre-tax operating projection until the tax lines exist. Keep the Stage 1 trust ceiling and the Stage 2 research ceiling. A missing line stays missing. It does not become zero and it does not become a sourced fact.

## Leave in place

- Verified competitors still require identity, an http(s) URL, and a real retrieval timestamp.
- Search stays `BLOCKED` until an allowlisted provider credential exists.
- Monsha'at stays `BLOCKED_EXTERNAL_REACHABILITY`.
- Do not disable TLS verification to reach GASTAT or Monsha'at.

## Do not do

- Do not merge to `main`.
- Do not deploy.
- Do not force-push.
- Do not run a database migration.
- Do not edit the dirty original checkout.
