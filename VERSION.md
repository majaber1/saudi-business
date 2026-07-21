# FeasibilityOS AI — V1.1 Developer Ready

## What actually works end-to-end in this version
- FastAPI backend with health check, project CRUD (in-memory), financial
  evaluation endpoint, and funding match endpoint — all runnable locally
  or via Docker (`docker-compose up`).
- Financial engine: ROI, payback period, NPV, IRR (Newton-Raphson with
  bisection fallback), break-even, and a 5-point revenue sensitivity
  analysis. Pure Python, no external numerical dependency.
- Funding engine: transparent, explainable rule-based scoring across the
  6 Saudi programs (NTDP, Monsha'at, CODE, SVC, Kafalah, RDIA) based on
  industry, stage, MVP status, and technical team — replacing the V1
  stub that returned all programs unconditionally.
- Full Postgres schema (`database/schema.sql`) covering every entity
  listed in the README (users, organizations, projects, feasibility
  studies, AI tasks, financial models, funding programs/matches,
  documents, knowledge sources, investors, audit logs).
- Test suite (`pytest tests/`) covering both engines.
- Dockerfile + docker-compose for local/Postgres-backed runs.

## Still a stub / not yet implemented (roadmap, not V1)
- Multi-agent orchestration (AI CEO / Market / Risk / Document agents) —
  `/projects/{id}/analyze` returns the intended workflow shape but does
  not yet call an LLM or LangGraph graph.
- RAG knowledge base (`knowledge-base/rag_pipeline.md`) — pipeline is
  documented, not implemented; no vector DB or ingestion code yet.
- Frontend (Next.js/React per the README's tech stack) — not present in
  this package; the backend is API-only for now.
- Persistence — project data is in-memory in V1.1; wiring the existing
  schema.sql to SQLAlchemy/psycopg2 is the next concrete step.
