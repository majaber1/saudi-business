# Saudi-Buisness V2 readiness ledger

Reviewed: 2026-08-08. Current released version: 1.0.0. V2 is a staged target,
not a label applied to unfinished work.

## Module status

| Module | Status | Evidence / remaining work |
|---|---|---|
| Authentication and RBAC | Production-capable core | Register, login, restoration, verification, reset, role gates, ownership tests and per-instance abuse limits work. SMTP credentials and centralized multi-instance limits remain operational configuration. |
| Projects and feasibility | Production-capable core | Owner-scoped CRUD, study wizard, computation and report downloads are wired. Browser E2E is missing. |
| Financial engine | Production-capable deterministic engine | ROI, NPV, IRR, payback, break-even and sensitivity work. Results are calculations, not financial advice. |
| Reports | Production-capable core | Authenticated PDF/DOCX and ownership enforcement work. Add visual Arabic regression tests. |
| Qualification | Production-capable core | Profiles, expiry, scores, missing analysis and bilingual recommendations work. Source verification and document storage remain. |
| Admin | V2 foundation implemented | Statistics, audit, user list, secure account creation and lead inbox are wired. Lead updates, pagination and catalog editing remain. |
| Opportunities, ideas, franchises, auctions | Demo/catalog ready | Browsing works; seeded rows are demo/unverified. Production needs verified sources and review dates. Auctions are not payments or escrow. |
| Funding matching | Rules ready; catalog unverified | Matching works. Eligibility, amounts and URLs need an accountable catalog owner. |
| Multazim hand-off | Boundary-safe summary only | Summarized requests work. Full ISO/NCA/PDPL/SAMA GRC remains outside this product. |
| Database and migrations | Runtime-verified locally | PostgreSQL 16 is healthy at revision `0006_account_security`. A live `0006 -> 0005 -> 0006` cycle preserved marker data and recreated the account-security schema. Production provisioning, backup and restore drills remain operational work. |
| Docker | Full local stack verified | PostgreSQL, API and Web images build and run together with health gates. API, readiness, Web and the Web-to-API proxy returned HTTP 200. External deployment remains. |
| AI and RAG | Not implemented | `ai-engine` and `knowledge-base` contain design documents, not callable modules. |
| Payments | Not implemented | Pricing captures leads only. PSP selection and merchant credentials require the account owner. |

## V2 delivery order

1. Provision production PostgreSQL, object storage, domains and secrets, then run the deployment and restore drill in the target environment.
2. Configure SMTP, centralized rate limits, monitoring collection and automated backups.
3. Add Playwright auth, feasibility/report, qualification and admin coverage, including Arabic RTL/mobile.
4. Establish catalog ownership for sources, verification dates, review status and expiry.
5. Add AI/RAG only with citations, deterministic fallback, evals, budgets and human review.

## Verification snapshot

- Backend application suite: 184 passed; the 4 separate child-process probes were blocked by the restricted Windows Winsock provider; 127 third-party JWT warnings remain.
- Critical backend subset after changes: 64 passed.
- Frontend ESLint, TypeScript and Next.js production build passed.
- Frontend production dependency audit: 0 vulnerabilities.
- Docker Compose resolved successfully with validation secrets.
- API and Web Docker images built successfully; PostgreSQL 16, API and Web all reached healthy state together.
- Live PostgreSQL migration preservation test passed: `0006_account_security -> 0005_sales_leads -> 0006_account_security` with marker data retained.
- Live HTTP checks passed for API health, API readiness, Arabic Web home and the Web-to-API proxy (all HTTP 200).
- Account lifecycle tests: 12 passed before the local test environment was removed to recover disk space.
- Frontend with verification/reset routes: ESLint, TypeScript and 20-route production build passed.
- Python audit tooling installed, but the advisory lookup was blocked by the local Windows network provider; CI now runs `pip-audit` as an acceptance gate.
- Not executed: browser E2E, external deployment, production backup/restore drill and real SMTP delivery.
