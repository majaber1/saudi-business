# Saudi Business | سعودي بزنس

> **Rebrand in progress** — this repository is being transformed from the
> FeasibilityOS-AI V1.1 prototype into the bilingual **Saudi Business** MVP.
> Work is tracked on branch \`feat/saudi-business-mvp\` (PR #1). The original
> product vision is preserved further down this file.

## Current status (v1.2.0 branch) — honest ledger

Each item is one of: **VERIFIED** (proven green in CI), **UNVERIFIED**
(implemented, not yet exercised), or **PLANNED**.

**Backend & data — VERIFIED in CI (3 green jobs: tests, Postgres migrations, secret scan):**
- FastAPI backend refactored; app + Vercel entrypoint import-check green.
- Persistence: SQLAlchemy 2.x models for 18 entities (users, organizations,
  roles, projects, feasibility studies, financial assumptions/results,
  sensitivity scenarios, funding programs/matches, idea bank, franchise,
  auctions/bids, multazim requirements, documents, reports, audit logs).
  Round-trip proven on SQLite; full schema created via \`alembic upgrade head\`
  against a real PostgreSQL 16 service in CI.
- Safe demo-mode fallback when \`DATABASE_URL\` is unset (in-memory, and
  \`/health\` reports \`db_enabled: false\` — persistence is never faked).
- Authentication: bcrypt password hashing + JWT, \`/auth/register\`,
  \`/auth/login\`, \`/auth/me\`, RBAC (\`require_roles\`), 6 canonical roles,
  audit logging. Register->login->protected-route flow proven end-to-end in CI.
- Financial & funding engines preserved and still under test.
- \`.env.example\` carries names only; no secrets committed.

**PLANNED / not yet in this branch (tracked in PR #1):**
- Next.js bilingual (AR/EN + RTL) frontend and all public/dashboard/admin pages.
- Feasibility-study wizard UI, PDF/Word report generation (deps installed;
  generators not yet wired).
- Database-backed Idea Bank / Franchise / Auctions catalogs + seed data.
- Multazim module integration (source repo confirmed: \`majaber1/multazim-ai-mvp\`).
- Production PostgreSQL provisioning + Vercel production verification.

## Local development

Windows PowerShell:
\`\`\`powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH="backend"; uvicorn app.main:app --reload --app-dir backend
\`\`\`

Linux/macOS:
\`\`\`bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --app-dir backend
\`\`\`

Run tests: \`pytest tests/ -v\`
Apply migrations (needs \`DATABASE_URL\`): \`alembic -c database/alembic.ini upgrade head\`

---

# FeasibilityOS AI

**AI Operating System for Investment Decisions**

## 1. Project Overview

FeasibilityOS AI is an AI-powered investment intelligence platform that
transforms business ideas into investment-ready opportunities.

The platform combines:
- Artificial Intelligence
- Financial Engineering
- Market Intelligence
- Saudi Government Funding Intelligence
- Multi-Agent AI Architecture
- RAG Knowledge Base

The goal is to become the trusted investment decision platform for
entrepreneurs, investors, consultants, banks, and government organizations.

---

## 2. Product Vision

From idea to investment decision:

Idea → Business Analysis → Feasibility Study → Financial Model → Funding
Match → Investor Package → Business Growth

---

## 3. Quick Start (V1)

This version ships a working FastAPI backend with a real financial
engine and funding matcher — everything else in this README describes
the full product vision (see [VERSION.md](VERSION.md) for exactly
what's implemented vs. planned).

### Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd backend
PYTHONPATH=. uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/docs` for interactive API docs.

### Run with Docker (includes Postgres)

```bash
docker-compose up --build
```

### Run tests

```bash
pytest tests/
```

### Example requests

```bash
curl -X POST http://localhost:8000/financial/evaluate \
  -H "Content-Type: application/json" \
  -d '{"investment": 500000, "annual_cash_flows": [150000,150000,150000,150000,150000], "discount_rate": 0.10}'

curl -X POST http://localhost:8000/funding/match \
  -H "Content-Type: application/json" \
  -d '{"industry": "technology", "stage": "mvp", "has_mvp": true, "has_technical_team": true}'
```

---

## 4. Core Features

### Business Intelligence
- Business Model Canvas
- Lean Canvas
- SWOT Analysis
- PESTEL Analysis
- Porter's Five Forces
- Market Analysis
- Competitor Analysis

---

## 5. Feasibility Engines

Supported feasibility types:
- General Business
- Financial
- Technical
- Startup
- Investment
- Industrial
- Real Estate
- Tourism
- Hospitality
- Healthcare
- Education
- Retail
- E-Commerce
- Franchise
- Government Projects
- AI Projects
- Entertainment & Events

---

## 6. AI Agent Architecture

| Agent | Responsible for |
|---|---|
| AI CEO Agent | Understanding project objectives, selecting workflows, managing other agents |
| Market Research Agent | Market size, demand analysis, competitors, pricing |
| Financial Agent | CAPEX, OPEX, revenue model, ROI, IRR, NPV, cash flow |
| Risk Agent | Risk identification, risk scoring, mitigation plans |
| Funding Agent | NTDP, Monsha'at, CODE, SVC, Kafalah, RDIA matching |
| Document Agent | Feasibility study, business plan, pitch deck, investor memo |

> V1 note: agent orchestration is a workflow stub today (see
> `ai-engine/workflows/feasibility_flow.md`). The Financial and Funding
> agents are the only ones with real, callable logic so far
> (`financial-engine/calculator.py`, `funding-engine/matcher.py`).

---

## 7. Technical Architecture

```
Frontend → FastAPI Backend → AI Orchestrator → AI Agents → RAG Knowledge Base
                                    ↓
                     Vector Database · Financial Engine · Document Engine
```

---

## 8. Technology Stack

**Frontend:** Next.js · React · TypeScript · Tailwind CSS · Arabic RTL support

**Backend:** FastAPI · Python

**AI:** OpenAI · Claude · Qwen · DeepSeek

**AI Framework:** LangGraph

**Database:** PostgreSQL

**Vector Database:** FAISS / Qdrant

**Deployment:** Docker · Kubernetes · Terraform

---

## 9. Database Entities

Users · Organizations · Projects · Feasibility Studies · AI Tasks ·
Agents · Financial Models · Funding Programs · Documents ·
Knowledge Sources · Investors · Audit Logs

Full schema: [`database/schema.sql`](database/schema.sql)

---

## 10. RAG Knowledge Base

Knowledge sources:
- Saudi Regulations
- Government Programs
- Industry Benchmarks
- Market Data
- Investment Information

Pipeline:

```
Documents → OCR → Cleaning → Chunking → Embedding → Vector Database → Retrieval → AI Response
```

---

## 11. Financial Engine

Capabilities (implemented in `financial-engine/calculator.py`):
- Revenue Forecast (via cash flow input)
- ROI, Payback Period
- NPV, IRR
- Break-even Analysis
- Sensitivity Analysis (revenue shock scenarios)

Planned: full Income Statement / Balance Sheet generation, cost modeling.

---

## 12. Funding Intelligence

Example:

**Project:** AI SaaS Platform (industry: technology, stage: mvp)

**Result:**
- NTDP Match: 100%
  - Reasons: technology sector match, stage supported, MVP validated, technical team in place
- SVC Match: 75%
  - Missing: stage not yet in SVC's typical funding range (early_revenue/growth)

---

## 13. User Roles

| Role | Capability |
|---|---|
| Entrepreneur | Create and manage projects |
| Consultant | Manage client feasibility studies |
| Investor | Review investment opportunities |
| Government | Evaluate supported projects |
| Admin | Manage platform |

---

## 14. Roadmap

**V1** — Project Wizard · AI Analysis · Financial Model · Report Generation

**V2** — Multi-Agent AI · RAG Knowledge Base · Funding Engine

**V3** — Investor Marketplace · AI CFO · Due Diligence

**V4** — GCC Expansion

---

## 15. Business Model

Revenue streams:
- SaaS Subscription
- Enterprise License
- Consultant Platform
- Government Solutions
- Investor Marketplace

---

## 16. Development Principles

- Modular Architecture
- Security First
- Explainable AI
- Human Review
- Saudi Market Intelligence
- Scalable Cloud Native Design

---

## 17. Repository Structure

```
.
├── backend/            FastAPI app (routers: projects, financial, funding)
├── financial-engine/   ROI / NPV / IRR / sensitivity calculations
├── funding-engine/     Saudi program matching logic
├── ai-engine/          Agent + workflow design docs (V2 target)
├── knowledge-base/     RAG pipeline design docs (V2 target)
├── database/           Postgres schema
├── docs/               Product overview and implementation notes
├── tests/              Pytest suite for both engines
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

See [VERSION.md](VERSION.md) for what's implemented vs. planned.
