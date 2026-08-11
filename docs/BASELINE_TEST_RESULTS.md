# Saudi Business baseline test results

Baseline date: 2026-08-09 (Asia/Riyadh)

Git baseline: `main` at `977bf13`

Rule: these results were captured before product-module changes on `agent/full-product-audit`.

## Results

| Area | Command / environment | Result | Notes |
|---|---|---|---|
| Python dependency audit | Python 3.11 container, `pip-audit -r requirements.txt` | PASS | No known vulnerabilities found. |
| Backend suite | Python 3.11 container, `pytest tests/ -q` | PASS | 191 passed in 120.63s; 139 warnings. |
| Frontend install | `npm ci --no-fund` | PASS with advisory | 392 packages installed; npm initially reported one high advisory. |
| Frontend audit | `npm audit --omit=dev` | INCONCLUSIVE / FAIL-OPEN RISK | Registry bulk-advisory request ended with `ECONNRESET`; it must be rerun successfully before release. |
| Frontend lint | `npm run lint` | PASS | No lint errors. |
| Frontend types | `npm run typecheck` | PASS | No TypeScript errors. |
| Frontend production build | `npm run build` | PASS | Next.js 16.3.0; 20 routes generated. |
| Docker Compose | production-shaped local variables, `docker compose up -d --wait` | PASS | PostgreSQL, API and Web healthy. |
| PostgreSQL migrations | `alembic current` inside API container | PASS | `0006_account_security (head)`. |
| API readiness | `GET /health/ready` | PASS | HTTP 200, database connected. |
| Web smoke | local Web root | PASS | HTTP 200. |

## Warning inventory

- PyJWT emitted short-HMAC-key warnings in tests because several tests replace the production-length secret with an 11-byte fixture. Production configuration rejects missing/weak setup separately, but test fixtures should be lengthened.
- Passlib uses Python's deprecated `crypt` module; this is a forward-compatibility warning for Python 3.13 rather than a current test failure.
- Starlette warns that its `httpx` TestClient compatibility path is deprecated in favor of `httpx2`; plan a controlled test-client migration.
- npm warned that `unrs-resolver` has an install script that is not covered by npm's `allowScripts` policy.
- The npm security result is not acceptable as a pass until the registry call completes and the reported high advisory is identified or removed.

## Coverage gaps at baseline

- No browser E2E suite for the complete entrepreneur journey.
- No automated visual regression for Arabic RTL, mobile, PDF or DOCX output.
- No load, concurrency or database-query performance tests.
- Catalog routes have backend authorization tests in aggregate, but limited module-specific validation and source-governance tests.
- No live SMTP-delivery acceptance test.
- No production backup/restore drill in CI.

## Previously verified migration evidence

The local PostgreSQL 16 environment was also exercised through
`0006_account_security -> 0005_sales_leads -> 0006_account_security`; marker data
survived and the account-security table/columns were restored. This is recorded
in `docs/V2_READINESS.md`; the current baseline reconfirmed head and readiness.
