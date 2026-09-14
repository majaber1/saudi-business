# Saudi Business — Evidence Capture (Coffee Case)

**Study:** `study_04778d06a34f`  
**Main SHA:** `3a7efebad7831b635cee63060aa7aec12310199b`  
**Captured:** 2026-09-14  

No evidence was manually injected. Below is what the product attached.

---

## Research quality observability (8C.3 projection)

- Policy version: `8c2-v1` / observability `8c3-v1`  
- Preferred: 5 · Alternate: 2 · Unresolved conflicts: 0 · Resolved: 0  
- Stale: 0 · Unknown freshness: 7 · Low quality: 3  
- Official source count: 4 · Total evaluated: 7  

---

## Claims used

### 1) GASTAT — Inflation ~1.8–1.9% (Mar 2026)

| Field | Value |
|------|--------|
| Claim | CPI annual inflation ~1.9% Mar 2026 vs Mar 2025; WPI ~3.3% |
| Source key | `gastat` |
| Source type | official |
| URL | https://www.stats.gov.sa/en/w/news/180 |
| Retrieved | 2026-09-14 |
| Confidence | 0.85 |
| Origin | research / market_research |
| Geography | Saudi Arabia (national) |
| Supports coffee unit economics? | **No** — macro inflation only |
| Supports demand/covers/ticket? | **No** |

### 2) GASTAT — GDP growth 3.0% Q1 2026

| Field | Value |
|------|--------|
| Claim | Saudi economy records 3.0% growth in Q1 2026 |
| Source key | `gastat` |
| URL | https://www.stats.gov.sa/en/w/news/199 |
| Confidence | 0.85 |
| Supports coffee CAPEX/rent/competition? | **No** — macro growth |

### 3) GASTAT — Wholesale & retail operating revenues +3.2% Q2 2026

| Field | Value |
|------|--------|
| Claim | Operating Revenues Index wholesale/retail +3.2% YoY Q2 2026 |
| Source key | `gastat` |
| URL | https://www.stats.gov.sa/en/w/news/212 |
| Confidence | 0.85 |
| Supports specialty coffee local demand? | **Weak / indirect** only |

### 4) MISA knowledge fragment

| Field | Value |
|------|--------|
| Claim | Truncated fragment about statistical output quality / transparency |
| Source key | `misa` |
| URL | null |
| Confidence | 0.5 |
| Origin | knowledge |
| Supports investment decision? | **No** (fragmentary / off-target) |

### 5) Market signal `cpi_inflation=1.8 (March)`

| Field | Value |
|------|--------|
| Source | gastat (same news family) |
| URL | https://www.stats.gov.sa/en/w/news/180 |
| Status | VERIFIED |
| Role | SECTOR_SIGNAL |

---

## Pricing research

| Item | Status |
|------|--------|
| Specialty coffee ticket / competitor price | **NOT_FOUND** (`no_sourced_pricing_evidence`) |

---

## Competitors

| Status | Detail |
|--------|--------|
| REAL_AND_SPECIFIC / PARTIAL / GENERIC / MISSING | **MISSING** |
| `competitors` array | `[]` |
| Named Riyadh cafés | None |
| Competitor pricing | None |

---

## Saudi authority coverage (this run)

| Authority | Found & used? |
|-----------|----------------|
| GASTAT | **Yes** (live) |
| Monsha’at | No |
| Ministry of Commerce | No |
| Balady / municipality | No |
| ZATCA | No |
| MISA | Partial / low-quality fragment |

---

## Evidence ↔ assumption contradictions (natural)

| Topic | Observation |
|------|-------------|
| Seats 10000 / covers 10000 / ticket 10000 SAR | No supporting coffee evidence; product rationale itself rejects realism |
| Macro inflation/GDP | Does not validate local Riyadh café demand or rent |
| Empty competitors | Contradicts ability to claim competitive GO |

Product response: verdict **INSUFFICIENT_EVIDENCE** + conditions to collect competitors, location_economics, demand.

**EVIDENCE_ASSUMPTION_NUMERIC_CONTRADICTION gate:** Not emitted as a typed P1-A code in `decision_safety` (null), but narrative + INSUFFICIENT_EVIDENCE blocked strong GO.
