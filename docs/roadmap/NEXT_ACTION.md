# Next action

Resume on branch `saudi-business-completion` in worktree `saudi-business-completion-20261028`. Do not use the dirty `Saudi-Business` checkout and do not apply its `0027` / `0028` migration files.

## Immediate task

Add a research citation critic on this branch.

The critic rejects an official or document claim that has no http(s) source URL and no retrieval timestamp. It does not invent a URL, a date, or a citation. User-entered assumptions stay labeled `user_input` or `ai_assumption` and cannot become official evidence by passing through the critic.

Leave these behaviors in place:

- GASTAT and MISA connectors stay as they are.
- Monsha'at stays `BLOCKED_EXTERNAL_REACHABILITY`.
- `ai_engine/tools/search.py` stays `not_implemented` until a real allowlisted provider exists.
- The Stage 1 financial trust ceiling stays authoritative.

## Done when

- A unit test shows a claim with no source URL is not stored as official evidence.
- A unit test shows a GASTAT or MISA claim that already has a URL and timestamp is kept.
- A unit test shows the critic does not fill in a missing URL.
- Targeted research tests pass.
- The change is committed and pushed to `saudi-business-completion` with a normal push. Then `git ls-remote origin refs/heads/saudi-business-completion` equals local `HEAD`.

## Do not do

- Do not merge to `main`.
- Do not deploy.
- Do not force-push.
- Do not run a database migration.
- Do not edit the dirty original checkout.
