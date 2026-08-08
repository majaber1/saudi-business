# Saudi Business | سعودي بزنس — V1.2 (in progress)

This document tracks what is **implemented and verified** vs. what is **planned**, so
the version file never overstates reality. "Verified" means it passed real GitHub
Actions CI (backend tests, Alembic migrations on a live Postgres 16 service, and the
Next.js production build) on the committed artifact — not just a local working copy.

## Implemented and VERIFIED in CI (feat/saudi-business-mvp)

- **Backend engines (from V1.1, still green):** financial engine (ROI, payback, NPV,
  IRR, break-even, 5-point sensitivity) and the explainable rule-based funding engine.
- **Persistence layer:** SQLAlchemy models for 18 entities, a demo-mode fallback when
  DATABASE_URL is unset, and an Alembic migration that applies cleanly to a real
  Postgres 16 service in CI (18 tables + alembic_version verified).
- **Authentication & RBAC:** bcrypt password hashing, JWT issuance/verification,
  register / login / me endpoints, six bilingual roles seeded on demand, and audit
  logging. Auth returns 503 in demo mode rather than faking accounts. Covered by tests.
- **Bilingual frontend (Next.js App Router):** Arabic-first with full RTL/LTR handling,
  persisted language preference, home page, navbar, footer. Pages now build in CI:
  home, login (wired to /auth), register (bilingual role picker), funding (program
  names only, "requires verification" labels), Idea Bank, Franchises, Business Auctions
  (with legal disclaimer, no payments/escrow), Multazim, dashboard, and a bilingual
  Help Center.
- **CI:** four jobs green — backend tests, Alembic migrations on Postgres, Next.js
  build, and a basic secret scan.

## Implemented and verified locally (full-stack; not yet exercised in CI)

CI's Next.js job type-checks and builds these pages (compile-time verification only).
The following was additionally proven with a real running stack — backend on a
migrated SQLite DB, frontend dev server pointed at it — not just a build pass:

- **Feasibility study wizard** (`/feasibility/new`): 3-step flow — project details,
  cash-flow assumptions, results — wired to `POST /feasibility/`,
  `PATCH /feasibility/{id}/step`, `POST /feasibility/{id}/compute`. Verified
  end-to-end: register → login → create study → compute → real ROI/NPV/IRR/payback +
  5-point sensitivity + funding match returned and rendered correctly.
- **PDF/Word report generation**: `GET /reports/study/{id}` confirmed to return a
  genuinely valid PDF (verified via `file` command: "PDF document, version 1.3, 1
  page(s)"), not just a 200 status.
- **Dashboard live data**: `GET /projects` + `GET /feasibility` fetched and rendered
  when signed in, with the badge/summary/table switching to a "live" state; falls
  back to the existing labeled demo view when signed out. Never mixes the two.
- **Investment Opportunities (investor hub)**: `InvestmentOpportunity` model,
  migration `0004`, `GET/POST /opportunities` filterable by industry/risk/budget,
  and the `/opportunities` frontend page. Verified: budget filter correctly
  excludes opportunities above an investor's stated amount; industry filter
  correct; RBAC on create (403 for non-admin/consultant). 8 tests in
  `tests/test_opportunities_and_leads.py`.
- **Pricing + sales lead capture**: `SalesLead` model, migration `0005`,
  public `POST /leads` + admin-only `GET /leads`, backing the `/pricing` page.
  Verified end-to-end: submit -> `persisted: true` -> visible via admin list.
  This is a contact-capture inbox, not a payment integration -- no card data
  is collected anywhere in this codebase.
- **Design system**: `next/font` bilingual pairing (Inter + Tajawal) with
  locale-driven switching, fixed a pre-existing bug (`ink-500`/`ink-600` and
  several `brand-*` shades were used in components but never defined in
  `tailwind.config.ts`), redesigned Navbar/Footer/home page.

## Implemented but requires production configuration

- **Production PostgreSQL:** migrations are verified in CI, but the deployed preview has
  no database until DATABASE_URL is provisioned. Vercel Git is connected; provisioning a
  free Postgres (e.g. Neon) requires the account owner to accept the provider's terms.
- **Production deploy of the new frontend:** the app builds, but a deploy decision is
  pending (see README) to avoid breaking the current working landing page on main.

## Planned / not yet implemented

- Admin frontend pages (backend admin API exists; no UI yet).
- Business Qualification & Readiness UI (backend API exists; not wired to frontend).
- Full Multazim module data integration (source repo identified: multazim-ai-mvp).
- Verified Saudi funding data catalog with amounts/eligibility and source/verification dates.
- AI abstraction layer (kept optional; core workflows must not depend on a paid API).
- Live payment gateway (Moyasar/PayTabs/Stripe or similar) -- requires the account
  owner to choose a PSP and provide merchant credentials; out of scope for an
  autonomous agent to configure.

_Previous milestone: V1.1 (API-only, in-memory persistence, no frontend)._
