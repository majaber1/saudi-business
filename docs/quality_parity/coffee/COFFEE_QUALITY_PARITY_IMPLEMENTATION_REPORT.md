# Coffee Quality Parity — Implementation Report

## Mission

Make Saudi Business independently capable of producing a specialty-coffee feasibility study at least as useful/detailed/decision-ready as the external Claude study **in coverage class**, without copying Claude data.

## Baseline

- Authoritative freeze SHA: `3a7efebad7831b635cee63060aa7aec12310199b`
- Product Hardening: CLOSED_AND_FROZEN
- Phase 9A: NOT STARTED
- Research Quality 8C.2 semantics: UNCHANGED

## Root causes

| Area | Root cause |
|---|---|
| 10000 placeholders | `assumption._default_value_for_field` catch-all returned `"10000"` for numeric/currency |
| Financial wiring | No F&B deterministic path; services fallthrough; `_merge_extract` dropped WC/budget fields |
| Research depth | Macro sources treated as sufficient; wrong source→assumption matching |
| Competitors | COMPETITOR research not forced for coffee; extractor markers too narrow |

## Implementation (reuse existing architecture)

1. **`ai_engine/hardening/assumption_semantics.py`** — semantic types, placeholder rejection, hours≤24, % 0–100, F&B plausibility, provenance mapping
2. **`ai_engine/agents/assumption.py`** — no catch-all 10000; F&B operating keys → UNKNOWN; provenance on Assumption
3. **`ai_engine/agents/fnb_financial_extract.py`** — café P&L + component CAPEX + WC + budget gap
4. **`ai_engine/agents/financial_analyst.py`** — F&B path first; merge preserves parity fields
5. **`ai_engine/hardening/financial_gates.py`** — PLACEHOLDER / HOURS / BUDGET / REVENUE_UNWIRED
6. **`ai_engine/hardening/sector_packs.py`** — F&B critical assumptions + source categories + research principle
7. **`ai_engine/archetypes/schemas.py` + discovery interview** — expanded F&B keys
8. **Market planner + competitor extractor** — coffee forces COMPETITOR/PRICING; broader café markers
9. **Tests:** `tests/test_coffee_quality_parity.py`

## Governance

- Migration: **NONE**
- Phase 9A: **NOT_STARTED**
- Claude data copied: **NO**
- Architecture redesign: **NO**

## REAL_USER_FLOW

See `COFFEE_REAL_USER_FLOW_REPORT.md` (populated after live run).
