# Changelog

All notable changes to this project are documented here. Only changes that were
implemented **and verified in CI** are listed under "Added"; work still in progress is
listed under "In progress" so the changelog never overstates completion.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — V2 foundation

- Expanded protected administration with account listing, secure user
  provisioning, sales-lead inbox, statistics, and audit activity.
- Removed the stale hard-coded external backend from the Next.js proxy.
- Required Compose secrets, added API/web health checks, and made web wait for API health.
- Replaced application-owned deprecated UTC calls without changing the database schema.
- Added frontend lint and Docker Compose validation to CI.
- Added expiring single-use email-verification and password-reset tokens,
  optional SMTP delivery, bilingual account-recovery pages, and production
  verification enforcement.
- Added request IDs, structured JSON access events, protected runtime metrics,
  production readiness checks, and per-instance abuse limits.
- Added migration `0006_account_security`, minimal Docker build contexts, and
  migration files inside the API image.

## [1.0.0] — Saudi-Buisness V1

- Upgraded to Next.js 16.3 and React 19; production dependency audit is clean.
- Added live Business Qualification & Readiness workspace and starter checklist.
- Added protected bilingual administration dashboard and audit activity view.
- Added complete Docker Compose packaging for web, API and PostgreSQL 16.
- Normalized product/backend/frontend version to 1.0.0 and refreshed documentation.
- Acceptance: 188 backend tests, TypeScript check and production frontend build pass.

## [Historical development] — feat/saudi-business-mvp

### Added (verified in CI)
- CI pipeline (GitHub Actions) with four jobs: backend tests, Alembic migrations on a
  live Postgres 16 service, Next.js production build, and a basic secret scan.
- Persistence layer: SQLAlchemy models for 18 entities, demo-mode fallback when
  DATABASE_URL is unset, and an Alembic initial migration verified against Postgres 16.
- Authentication & RBAC: bcrypt hashing, JWT, register/login/me endpoints, six bilingual
  roles seeded on demand, and audit logging (returns 503 in demo mode instead of faking).
- Bilingual (AR/EN, RTL) Next.js frontend: language provider with persisted preference,
  navbar, footer, and home page.
- Frontend routes: login (wired to /auth), register (bilingual role picker), funding
  (program names only, "requires verification" labels), Idea Bank, Franchise
  Opportunities, Business Auctions (with legal disclaimer, no payments/escrow), Multazim,
  and a bilingual Help Center.
- Typed API client (apps/web/lib/api.ts) aligned with the backend auth schema.
- Documentation: implementation plan, README status ledger, and VERSION.md V1.2 ledger.

### Added (verified locally; full stack)
- Feasibility study wizard frontend (`apps/web/app/feasibility/new`): real
  3-step flow (project details -> cash flow assumptions -> results) wired to
  `POST /feasibility/`, `PATCH /feasibility/{id}/step`, and
  `POST /feasibility/{id}/compute`, plus a PDF/DOCX report download and a
  funding-match panel. Verified end-to-end against a migrated SQLite DB:
  register -> login -> create study -> compute -> valid PDF returned.
  Requires sign-in; shows a sign-in prompt otherwise.
- Typed API client (`apps/web/lib/api.ts`) expanded beyond auth to cover
  projects, feasibility studies, financial evaluation, and funding matching.
- Dashboard now fetches real `GET /projects` and `GET /feasibility` data when
  signed in and switches its badge/summary/table to a "live" view; falls back
  to the existing labeled demo view otherwise. Never mixes real and demo
  numbers in the same view.
- PDF (reportlab) + Word (python-docx) report generation is fully wired, not
  just dependency-installed as previously stated here.

### Added (verified locally; design + investor hub + monetization)
- Repository renamed `FeasibilityOS-AI` -> `saudi-business` (GitHub redirects
  the old name automatically; local remotes updated).
- Bilingual typography overhaul: `next/font` pairing (Inter for Latin,
  Tajawal for Arabic), locale-driven font switching via `:lang(ar)`/`:lang(en)`
  in `globals.css`, refined Tailwind design tokens (added missing `ink-500`/
  `ink-600`/`brand-200`/`brand-400`/`brand-800` shades that were referenced
  in components but never defined -- a pre-existing bug), and new
  `shadow-card`/`shadow-card-hover` tokens. Navbar/Footer/home page redesigned
  for a cleaner, more professional first impression; footer is now a real
  multi-column footer with product/investor/company links.
- **Investment Opportunities module** (the investor hub): new
  `InvestmentOpportunity` model + migration `0004`, `GET/POST /opportunities`
  API filterable by `industry`, `risk_level`, and `max_amount` (an investor's
  available budget -- "show me what fits"), and `/opportunities` frontend page
  with an amount/industry/risk filter form. 8 new backend tests
  (`tests/test_opportunities_and_leads.py`) cover public listing, RBAC on
  create, budget filtering, and industry filtering.
- **Pricing + sales lead capture** (monetization surface, no live payments):
  new `SalesLead` model + migration `0005`, public `POST /leads` (admin-only
  `GET /leads`) backing a real `/pricing` page with 3 tiers and a
  "Request access" form. Explicitly NOT a payment integration -- no card
  details are collected anywhere; this is a contact-capture inbox for a human
  sales follow-up, since live payment processing needs the account owner's
  own merchant/PSP credentials.
- Seed script (`database/seed.py`, idempotent) populating Idea Bank,
  Franchises, Auctions, and Investment Opportunities with clearly-labeled
  (`verification_status="demo"`, "illustrative example" in every description)
  placeholder rows so those pages show real content instead of an empty list.
  Verified against a migrated SQLite DB.
- Full migration chain `0001` -> `0005` re-verified end-to-end locally.

### In progress / not yet implemented
- Admin frontend pages (backend admin API exists; no UI yet).
- Full Multazim data-model integration (source repo identified: multazim-ai-mvp).
- Verified Saudi funding data catalog (amounts/eligibility with source + verification dates).
- Optional AI abstraction layer (core workflows must not depend on a paid API).
- Business Qualification & Readiness UI (backend API exists; not wired to frontend).
- Live payment gateway integration (Moyasar/PayTabs/Stripe or similar) --
  requires the account owner to choose a PSP and provide merchant credentials.

### Infrastructure notes
- Vercel Git is connected to the repository.
- **Production database is still not provisioned.** Migrations (`0001`-`0005`)
  are ready to apply, and the seed script is ready to run, once `DATABASE_URL`
  (or `POSTGRES_URL`) is configured by the account owner in Vercel project
  settings -- e.g. via Neon, Supabase, or Vercel Postgres. Until then the
  production deployment runs in demo/in-memory mode and none of the new
  persistence-backed features (auth, projects, opportunities, leads) retain
  data between cold starts.

## [1.1.0] — Developer Ready (previous)
- API-only FastAPI backend with in-memory persistence, financial engine, and rule-based
  funding engine. No frontend in this milestone.
