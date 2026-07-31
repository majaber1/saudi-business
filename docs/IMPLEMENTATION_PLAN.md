# Saudi Business | سعودي بزنس — Implementation Plan & Architecture Decisions

Status doc for the transformation of FeasibilityOS-AI (V1.1 API prototype) into the
bilingual "Saudi Business" MVP. This file is the source of truth for scope and decisions.

## 1. Baseline (verified by inspection on this branch)
- Backend: FastAPI (backend/app), financial-engine/, funding-engine/.
- Persistence: NONE at runtime — projects are in-memory (backend/app/api/projects.py).
  database/schema.sql exists but is not wired to the app.
- Frontend: NONE in this repo — index.html is a static placeholder; README's Next.js
  stack is aspirational.
- Deploy: Vercel @vercel/python via api/index.py + vercel.json.
- Multazim MVP repo confirmed as majaber1/multazim-ai-mvp (apps/web Next.js, apps/api
  FastAPI, compliance dashboard/assessment). majaber1/multazim-ai is an empty decoy.

## 2. Target architecture
- Monorepo: apps/web (Next.js App Router + TS + Tailwind, bilingual AR/EN + RTL),
  apps/api (FastAPI), database/ (SQLAlchemy + Alembic migrations + seed), docs/,
  .github/workflows/ (CI).
- Persistence: PostgreSQL via SQLAlchemy 2.x + Alembic, driven by DATABASE_URL.
  Safe demo/in-memory fallback when DATABASE_URL is absent so preview never 500s.
- Auth: password hashing (passlib/bcrypt), JWT sessions, server-side RBAC.
- Reports: PDF (reportlab) + Word (python-docx) — open-source only.
- AI: provider-abstraction layer; deterministic rule-based defaults, optional key.

## 3. Decisions (made autonomously, documented here)
- D1: Keep the existing pure-Python financial & funding engines; refactor, do not rewrite.
- D2: Backend stays FastAPI on Vercel Python runtime; if serverless limits bite,
  document a free-tier fallback (e.g. Render/Fly free) — no paid infra introduced.
- D3: DB access must degrade gracefully to demo mode; never claim persistence when
  DATABASE_URL is unset.
- D4: Secrets only via env vars; .env.example carries names only. No secret ever committed.
- D5: All Saudi funding/franchise/idea seed data labelled with source URL + verification
  status; nothing presented as confirmed official fact without a source.

## 4. Delivery order (each chunk verified by its own CI run)
1. This plan + CI workflow running existing pytest suite. (Phase 1/19)
2. SQLAlchemy models + Alembic migration + DB session + demo fallback. (Phase 3)
3. Auth + RBAC + seed data + .env.example. (Phase 4/18)
4. Next.js bilingual frontend shell + core pages. (Phase 5/6/7)
5. Feature modules: feasibility wizard, funding, Idea Bank, Franchise, Auctions,
   Multazim integration, reports. (Phase 8-16)

## 5. Honesty ledger
Every phase reported as one of: IMPLEMENTED+VERIFIED / IMPLEMENTED-UNVERIFIED / PLANNED.
Test/CI/deploy status is only ever reported from real logs, never assumed.
