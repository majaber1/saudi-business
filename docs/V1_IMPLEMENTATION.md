# V1 Implementation Status

## Implemented and tested
- FastAPI backend: `/health`, `/projects`, `/financial/evaluate`,
  `/financial/sensitivity`, `/funding/match`
- Financial engine: ROI, payback, NPV, IRR, break-even, sensitivity
  analysis — pure Python, unit tested
- Funding engine: explainable rule-based matcher across 6 Saudi
  programs — unit tested
- Postgres schema covering all entities in the README
- Docker + docker-compose for local runs

## Documented but not yet implemented (see ai-engine/ and knowledge-base/)
- Multi-agent orchestration (LangGraph-based AI CEO / Market / Risk /
  Document agents)
- RAG knowledge base ingestion and retrieval
- Frontend (Next.js)
- Persistent storage wired to the schema (V1 API is in-memory)

See [VERSION.md](../VERSION.md) for the same breakdown with more detail.
