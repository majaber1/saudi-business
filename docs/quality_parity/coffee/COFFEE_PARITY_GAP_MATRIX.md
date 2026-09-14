# Coffee Quality Parity — Gap Matrix

**Baseline Main SHA:** `3a7efebad7831b635cee63060aa7aec12310199b` (Product Hardening freeze; verify with `git rev-parse 3a7efeb`)  
**Branch tip at matrix draft:** post-hardening main + this sprint  
**External Claude study:** USED AS QUALITY REFERENCE ONLY — **not** an evidence source  
**Claude data copied into product:** **NO**

## How to read this matrix

Compare *capability class / decision usefulness*, not numeric identity.
Claude numbers must not be treated as Saudi Business truth.

| Capability class | Claude coverage (class) | Pre-sprint Saudi Business | Post-sprint target | Status |
|---|---|---|---|---|
| Market macro context | Macro + sector narrative | Macro GASTAT/MISA only | Macro separated from operating claims | IMPROVED |
| Sector / coffee context | Specialty coffee sector framing | Weak / generic F&B | F&B sector pack + research principle | IMPROVED |
| Competitor intelligence | Named Riyadh competitors + pricing bands | Empty competitor list | Planner forces COMPETITOR/PRICING; extractor widened; no fabrication | IMPROVED (evidence-dependent) |
| Pricing evidence | Ticket / menu pricing discussion | Pricing NOT_FOUND | Pricing research type forced; UNKNOWN if absent | IMPROVED |
| Store / operating model | Area, seats, hours, days | Asked, but AI estimate → 10000 placeholders | Semantic types + UNKNOWN over fake precision | FIXED |
| Staffing / salaries | Role mix + SAR salaries | Labor as single monthly figure; often placeholder | Schema + gates; salary evidence category in pack | PARTIAL |
| Rent / location economics | District vs Riyadh ranges | Not distinguished; placeholder rent | Location uncertainty flagged; rent plausibility guard | PARTIAL |
| CAPEX components | Equipment / fit-out / other | Single meaningless fitout_capex=10000 | Component CAPEX (equipment/fitout/other) | FIXED |
| Working capital | Explicit WC | Omitted / invisible | Explicit WC (2-month OPEX estimate when missing) | FIXED |
| Revenue wiring | Covers × ticket × days | Revenue Y1–Y3 = 0 | Deterministic F&B extract wires revenue | FIXED |
| COGS / OPEX | COGS% + rent/labor/utilities | Effectively zero OPEX | COGS% + rent/labor/utilities/marketing wired | FIXED |
| Budget sufficiency | Budget vs total funding | CAPEX 10k vs 450k; no gap logic | SURPLUS/SHORTFALL vs owner_budget | FIXED |
| NPV / IRR / payback | Full horizon math | NPV=-10k; IRR/payback unavailable | Valid when cashflows support; no false certainty | FIXED |
| Risks | Location, ramp, competition, WC, budget | Generic + some coffee risks | Sector pack risk areas; derived from study | PARTIAL |
| Contradictions | Evidence vs assumptions | P1-A present | Preserved | UNCHANGED (preserve) |
| Evidence gaps | Explicit gaps | Partial | UNKNOWN + incomplete flags | IMPROVED |
| Final decision safety | Conditional / evidence-bound | INSUFFICIENT_EVIDENCE (good) | Keep blocking unsupported GO | PRESERVE |
| Investment-grade report structure | Full sectioned study | Thin / broken financials | Report sections still product-dependent; financials usable | PARTIAL |
| Persistence | N/A (chat) | PASS on prior RUF | Must PASS again | REQUIRED |

## Root causes addressed (pre-sprint → post-sprint)

1. **10000 placeholders:** `_default_value_for_field` catch-all → removed; semantic validation rejects sentinels; F&B operating keys return UNKNOWN.
2. **Revenue = 0:** No F&B deterministic extract → added `fnb_financial_extract`; merge preserves WC/budget fields.
3. **Competitor gap:** Planner did not force COMPETITOR for coffee → coffee/F&B markers force COMPETITOR+PRICING; extractor markers broadened; still no fabrication.
4. **Budget handling:** No owner_budget vs total funding → budget_status SURPLUS/SHORTFALL + gate.

## Explicit non-goals

- Phase 9A / Benchmark Engine / pgvector / second RAG
- Copying Claude numbers, competitors, verdict, or assumptions
- Database migrations
- Weakening Research Quality 8C.2 semantics or decision safety
