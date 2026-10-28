# Next action

Resume on branch `saudi-business-completion` in worktree `saudi-business-completion-20261028`. Do not use the dirty `Saudi-Business` checkout and do not apply its `0027` / `0028` migration files.

Owner-decision commit verified on the remote: `c945ac498f883c357c8efb3a7d1b158a6b955393`. After the next push, confirm `git rev-parse HEAD` equals `git ls-remote origin refs/heads/saudi-business-completion`.

Rechecked 2026-10-29. Local process, user, and machine environments have no `TAVILY_API_KEY`, `BRAVE_SEARCH_API_KEY`, or `GROQ_API_KEY`. No `.env` file exists. The web Vercel project still has `GROQ_API_KEY` and does not have either search key. That production Groq value was not decrypted. Search stayed `BLOCKED`.

## Immediate task

Provide one allowlisted search credential and one local Groq credential, then prove a real competitor or price retrieval and a model-written classification. Do not invent competitors, prices, or timestamps.

## Local configuration

1. Copy `.env.example` to `.env` in the worktree. Do not commit `.env`.
2. Set `GROQ_API_KEY` in that file or in the API process environment. Optional model names: `GROQ_MODEL_PRIMARY` and `GROQ_MODEL_FAST`.
3. Set exactly one of `TAVILY_API_KEY` or `BRAVE_SEARCH_API_KEY`.
4. Restart the local API so it reads the new variables.
5. With one of those keys in the API process, `search_saudi_data` calls Tavily first, otherwise Brave. Without a key it stays `BLOCKED`. A fixture test is not a live competitor result. Prove one real URL before calling search complete.

The production Groq value already exists on the Vercel projects. Do not decrypt it into this workspace unless the owner explicitly authorizes that copy.

## Vercel configuration

API project: `feasibilityos-ai`. Web project: `saudi-business-web`. Team: `team_mLtuSkiJk36yTV2AW8Y9RiZL`.

`GROQ_API_KEY`, `GROQ_MODEL_PRIMARY`, and `GROQ_MODEL_FAST` are already present on both projects for production, preview, and development. `TAVILY_API_KEY` and `BRAVE_SEARCH_API_KEY` are not present.

To add a search key without printing it:

`vercel env add TAVILY_API_KEY production --project feasibilityos-ai`

Repeat for preview and development, or use `BRAVE_SEARCH_API_KEY` instead. Add the same name to the web project only if the web process calls search. Do not put the value in git.

## Owner decision

The founder can accept, reject, or request modification of the current recommendation. Accepting does not change it. A rejection of the same analysis cannot be rewritten to an acceptance. Credential setup remains the blocker for live search and live model output. Details are in `docs/roadmap/OWNER_ACTION_REQUIRED.md`.

## Still blocked

- General search: `NO_ALLOWLISTED_PROVIDER_CONFIGURED`.
- Groq on this machine: absent. The workspace now says deterministic fallback.
- Monsha'at: homepage HTTP 200 with verification on. No connector. Planner reason remains `BLOCKED_EXTERNAL_REACHABILITY`.
- Competitor and pricing evidence: `NOT_FOUND`.
- Full AI acceptance: not run. The owner rejection is recorded. The model-written decision narrative and a live competitor URL were not produced.

## Do not do

- Do not merge to `main`.
- Do not deploy.
- Do not force-push.
- Do not run a production database migration.
- Do not edit the dirty original checkout.
- Do not turn a missing line into zero.
- Do not disable TLS verification.
- Do not print or commit secret values.
