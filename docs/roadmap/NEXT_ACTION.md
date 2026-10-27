# Next action

Resume on branch `saudi-business-completion` in worktree `saudi-business-completion-20261028`. Do not use the dirty `Saudi-Business` checkout and do not apply its `0027` / `0028` migration files.

Last verified remote SHA before the citation-critic commit: `748ce3cde238ac9d24c3e66f9dd98e3fee899d03`. After the next push, confirm `git rev-parse HEAD` equals `git ls-remote origin refs/heads/saudi-business-completion`.

## Immediate task

Require competitor evidence to carry an identity, an http(s) URL, and a retrieval timestamp before it can count as a competitor record.

Name-only extraction may remain visible as an unverified mention. It must not be stored as sourced competitor evidence. Do not invent a competitor URL or timestamp.

Leave these behaviors in place:

- The citation critic still rejects official and document claims that have no http(s) URL.
- GASTAT and MISA connectors stay as they are.
- Monsha'at stays `BLOCKED_EXTERNAL_REACHABILITY`.
- `ai_engine/tools/search.py` stays `not_implemented` until a real allowlisted provider exists.
- The Stage 1 financial trust ceiling stays authoritative.

## Done when

- A unit test shows a name-only competitor mention is not sourced competitor evidence.
- A unit test shows a competitor with identity, http(s) URL, and timestamp is kept.
- A unit test shows a missing URL is not filled in.
- Targeted tests pass.
- The change is committed and pushed to `saudi-business-completion` with a normal push, then the remote SHA matches local `HEAD`.

## Do not do

- Do not merge to `main`.
- Do not deploy.
- Do not force-push.
- Do not run a database migration.
- Do not edit the dirty original checkout.
