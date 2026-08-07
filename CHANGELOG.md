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

### In progress / not yet implemented
- Admin frontend pages (backend admin API exists; no UI yet).
- DB-backed catalogs and seed data for Idea Bank, Franchises, and Auctions
  (endpoints exist and are real, but the tables are empty until seeded).
- Full Multazim data-model integration (source repo identified: multazim-ai-mvp).
- Verified Saudi funding data catalog (amounts/eligibility with source + verification dates).
- Optional AI abstraction layer (core workflows must not depend on a paid API).
- Business Qualification & Readiness UI (backend API exists; not wired to frontend).

### Infrastructure notes
- Vercel Git is connected to the repository.
- Production database is not yet provisioned; migrations are ready to apply once a
  DATABASE_URL is configured by the account owner.

## [1.1.0] — Developer Ready (previous)
- API-only FastAPI backend with in-memory persistence, financial engine, and rule-based
  funding engine. No frontend in this milestone.
