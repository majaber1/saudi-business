# Owner action required

Updated: 2026-10-29. No secret values belong in this file or in git.

These credentials are absent from the local process, the user environment, the machine environment, and from any `.env` file in the worktree. Search stays `BLOCKED`. Classification on this machine stays a deterministic fallback. Do not decrypt the production Groq value into this workspace unless that copy is explicitly authorized.

## GROQ_API_KEY

| Item | Value |
| --- | --- |
| Credential | `GROQ_API_KEY` |
| Provider | Groq |
| Optional names | `GROQ_MODEL_PRIMARY`, `GROQ_MODEL_FAST` |
| Intended environment | Local uncommitted `.env` for the API process. The names already exist on Vercel projects `feasibilityos-ai` and `saudi-business-web` for production, preview, and development. |
| Secure setup | Copy `.env.example` to `.env` in the worktree. Put the key only in that file or in the API process environment. Restart the API. Do not commit `.env`. Do not print the value. |
| Exact test blocked | A real model classification, sourced assumption draft, risk narrative, decision explanation, and the model-written portion of the Riyadh coffee and Saudi SaaS browser journeys. |
| What can continue | Deterministic classification remains labeled `deterministic_fallback`. Financial gates, owner decision, and report generation from persisted fields do not need this key. |

## TAVILY_API_KEY or BRAVE_SEARCH_API_KEY

| Item | Value |
| --- | --- |
| Credential | Exactly one of `TAVILY_API_KEY` or `BRAVE_SEARCH_API_KEY` |
| Provider | Tavily (`https://api.tavily.com/search`) or Brave (`https://api.search.brave.com/res/v1/web/search`) |
| Intended environment | Local uncommitted `.env` for the API process, then Vercel project `feasibilityos-ai`. The web project does not need the key unless the web process calls search. |
| Secure setup | Set one key in the uncommitted `.env` and restart the API. For Vercel, run `vercel env add TAVILY_API_KEY production --project feasibilityos-ai` (or `BRAVE_SEARCH_API_KEY`) and repeat for preview and development. Do not commit the value. |
| Exact test blocked | One live competitor or price URL with a retrieval timestamp for the Riyadh specialty-coffee study and the Saudi SaaS study. Fixture tests are not this test. |
| What can continue | The existing client stays in place. With no key it returns `BLOCKED` / `NO_ALLOWLISTED_PROVIDER_CONFIGURED` and an empty result list. GASTAT and MISA retrieval, financial calculations, and the owner decision do not need this key. |

## Independent work that can continue

- Owner approve, reject, and request-modification on the current recommendation.
- Report text that repeats the persisted recommendation, pre-tax label, and owner decision.
- Coffee and SaaS financial regressions.
- Browser checks of the existing isolated study that do not claim a live search or a live model call.

## Still not authorized

Monsha'at has no connector. Homepage reachability is not an implementation. Do not add a connector until a lawful page list is tested with verification left on.
