# V4 Phase 8B Release Acceptance — Controlled Market Research Intelligence

**Status:** MERGED  
**Date (UTC):** 2026-09-13  
**PR:** https://github.com/majaber1/saudi-business/pull/46  
**Head SHA (pre-merge):** `ad2560a0eba8e446de68da963f40ef64fcd8639b`  
**Merge SHA / Main SHA:** `02e79eb24103e667c48824109f92ad5fe5e0e833`  
**STOP:** Do **not** start Phase 8C.

## Objective

Ship Controlled Market Research Intelligence so studies can answer competitor / market / pricing / regulation questions using **sourced evidence only**, on the existing LangGraph research path, without inventing competitors, prices, or market-size numbers.

## Architecture flow

```
Existing LangGraph
        |
Research Node (Phase 8A)
        |
Market Research module (Phase 8B)
        |
MCP Boundary (source_status / source_fetch only)
        |
Source Connectors (GASTAT + MISA live)
        |
Knowledge Layer (no second RAG)
        |
Evidence Pack → Evidence Agent (official beats ai_assumption)
```

### Scope merged

| Area | Change |
|------|--------|
| `ai_engine/research/market/*` | Planner, competitor, market/pricing/regulation signals, service |
| `ai_engine/research/service.py` + `nodes/research.py` | Wire market synthesis after official research |
| `ai_engine/models/study_state.py` | Additive `market_research_context` |
| `backend/app/api/v2/study_engine.py` | Serialize + snapshot restore |
| Workspace UI | Market research panel (insight / source / URL / confidence / ref) |
| Tests + evidence docs | Phase 8B suite + validation artifacts |

### Explicitly unchanged

- Financial Engine
- Risk Engine
- Decision Engine
- Report Engine
- No second agent runtime / CrewAI / AutoGen
- No unrestricted web crawler / generic AI web agent
- No second RAG / vector database

## Source governance

| Source | Role |
|--------|------|
| GASTAT | Live economic / sector signals |
| MISA | Live investment signals |
| SAMA / ZATCA / NCA | Placeholders only |
| Monsha'at | Remains blocked (not required) |

## Final review (pre-merge)

| Check | Result |
|-------|--------|
| File scope limited to expected paths | **PASS** |
| No Financial/Risk/Decision/Report edits | **PASS** |
| No second RAG / second runtime / open crawler | **PASS** |
| Competitor requires source | **PASS** |
| Pricing requires source | **PASS** |
| Market-size never invented | **PASS** |
| Conflicts surfaced (not silent override) | **PASS** |
| User-visible provenance intact | **PASS** |
| Backend/Frontend/Alembic/Secret/Compose CI | **PASS** |
| Vercel Preview | **BLOCKED_BY_QUOTA** (`api-deployments-free-per-day` / build-rate-limit) |

Vercel failures are platform quota noise. No application code was changed to work around them. Preview is not claimed PASS.

## Post-merge validation (from `main` @ `02e79eb`)

### Automated

| Suite | Result |
|-------|--------|
| Phase 8B controlled market research | **PASS** (28) |
| Phase 8A research + final trust gate | **PASS** |
| Phase 7A source foundation | **PASS** |
| Phase 7B GASTAT | **PASS** |
| MISA | **PASS** |
| Knowledge Layer | **PASS** |
| Financial Trust | **PASS** |
| Tenant isolation (GASTAT/MISA/Knowledge) | **PASS** (3) |
| Aggregate regression | **PASS** (115) |

### Controlled smoke A–E

| Scenario | Result |
|----------|--------|
| A. Competitor with sourced evidence | **PASS** — VERIFIED + official URL |
| A2. Competitor with no evidence | **PASS** — NOT_FOUND, no fabricated names |
| B. Market signal (CPI) | **PASS** — GASTAT URL + value |
| C. Pricing signal | **PASS** — SAR 99 with MISA URL |
| C2. Pricing with no evidence | **PASS** — NOT_FOUND, no invented price |
| D. Market size / no evidence | **PASS** — no unsupported TAM number |
| E. Conflict handling | **PASS** — CONFLICT surfaced with both values |
| User-visible provenance fields | **PASS** — insight/source/URL/confidence/ref |

## User-visible evidence behavior

Workspace + API expose:

- `market_research_context.status`
- selected sources
- insights with `insight`, `research_type`, `source` / `source_key`, `official_url`, `evidence_reference`, `confidence`, `status`

Claims panel continues to show research status and claim provenance (`source_type`, `origin`, `source_url`, document/chunk ids).

## Platform quota note

Vercel Preview for `feasibilityos-ai` and `saudi-business-web` failed with **Deployment rate limited — retry in 24 hours** (`upgradeToPro=build-rate-limit`). This is quota noise, not an application defect. Preview status for this release: **BLOCKED_BY_QUOTA**.

## Known limitations

1. Monsha'at remains blocked for external reachability.
2. Competitor discovery requires sourced evidence — no open-web crawler (by design).
3. SAMA / ZATCA / NCA are framework placeholders only.
4. Pricing and market-size numbers are never invented without official/user evidence.
5. Research / market context persistence still primarily uses version snapshots.
6. Vercel Preview may remain unavailable until quota resets.

## Scorecard

| Item | Result |
|------|--------|
| PHASE 8B STATUS | **MERGED** |
| Merge SHA | `02e79eb24103e667c48824109f92ad5fe5e0e833` |
| Main SHA | `02e79eb24103e667c48824109f92ad5fe5e0e833` |
| Final Review | **PASS** |
| Post-Merge Tests | **PASS** |
| Competitor Trust | **PASS** |
| Pricing Trust | **PASS** |
| Market-Size Trust | **PASS** |
| Conflict Handling | **PASS** |
| User Visible Evidence | **PASS** |
| Regression | **PASS** |
| Vercel Preview | **BLOCKED_BY_QUOTA** |

## STOP

Phase 8B release closure complete. **Do not start Phase 8C automatically.**
