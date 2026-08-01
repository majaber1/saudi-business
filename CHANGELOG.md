# Changelog

All notable changes to this project are documented here. Only changes that were
implemented **and verified in CI** are listed under "Added"; work still in progress is
listed under "In progress" so the changelog never overstates completion.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — feat/saudi-business-mvp (targeting V1.2)

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

### In progress / not yet implemented
- Feasibility study wizard UI, dashboard, and admin pages.
- PDF and Word report generation (dependencies present; generators pending).
- DB-backed catalogs and seed data for Idea Bank, Franchises, and Auctions.
- Full Multazim data-model integration (source repo identified: multazim-ai-mvp).
- Verified Saudi funding data catalog (amounts/eligibility with source + verification dates).
- Optional AI abstraction layer (core workflows must not depend on a paid API).

### Infrastructure notes
- Vercel Git is connected to the repository.
- Production database is not yet provisioned; migrations are ready to apply once a
  DATABASE_URL is configured by the account owner.

## [1.1.0] — Developer Ready (previous)
- API-only FastAPI backend with in-memory persistence, financial engine, and rule-based
  funding engine. No frontend in this milestone.
