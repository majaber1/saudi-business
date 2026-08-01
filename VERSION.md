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
  (with legal disclaimer, no payments/escrow), Multazim, and a bilingual Help Center.
- **CI:** four jobs green — backend tests, Alembic migrations on Postgres, Next.js
  build, and a basic secret scan.

## Implemented but requires production configuration

- **Production PostgreSQL:** migrations are verified in CI, but the deployed preview has
  no database until DATABASE_URL is provisioned. Vercel Git is connected; provisioning a
  free Postgres (e.g. Neon) requires the account owner to accept the provider's terms.
- **Production deploy of the new frontend:** the app builds, but a deploy decision is
  pending (see README) to avoid breaking the current working landing page on main.

## Planned / not yet implemented

- Feasibility study wizard UI and dashboard/admin pages.
- PDF and Word report generation (dependencies installed; generators not written yet).
- DB-backed catalogs + seed data for Idea Bank, Franchises, and Auctions.
- Full Multazim module data integration (source repo identified: multazim-ai-mvp).
- Verified Saudi funding data catalog with amounts/eligibility and source/verification dates.
- AI abstraction layer (kept optional; core workflows must not depend on a paid API).

_Previous milestone: V1.1 (API-only, in-memory persistence, no frontend)._
