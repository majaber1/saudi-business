# Coffee Source Strategy

**Claude report role:** DISCOVERY MAP only (source *types* / categories).  
**Claude report role NOT:** evidence registry. No Claude claims enter the product as evidence.

## Principle

FINDING A SOURCE IS NOT ENOUGH.  
Match **source category → assumption type**.

| Assumption class | Acceptable source categories | Not sufficient alone |
|---|---|---|
| Macro (GDP, CPI) | GASTAT, official Saudi | Does not prove ticket / rent / orders |
| Sector demand | Market/industry research, Monsha’at sector stats | Macro GDP |
| Rent / location | Saudi/Riyadh commercial real-estate | National inflation |
| Ticket / pricing | Competitor menus, delivery listings, F&B research | GDP |
| Salaries | Saudi salary/recruitment platforms, labor evidence | Macro employment rate alone |
| CAPEX equipment | Supplier/vendor quotes (prefer Saudi/GCC) | Macro CAPEX indices alone |
| Fit-out | Commercial fit-out references with unit/geography/scope | Confusing SAR/m² with total fit-out |
| Competitors | Primary competitor sites, menus, verified listings | Invented names |
| Regulation | MoC, Balady, ZATCA, MISA as applicable | Unrelated macro |

## Diversity rule

For high-impact assumptions (rent, ticket, salary, CAPEX, market size): attempt multiple independent sources when reasonably available. Conflicts use existing Research Quality / conflict intelligence — do not silently pick the favorable value.

## Failure behavior

If evidence cannot be found: **INSUFFICIENT_EVIDENCE / UNKNOWN / SYSTEM_ESTIMATE** — never fabricate. Transparent estimate > fake evidence.

## Product wiring (this sprint)

- F&B sector pack `source_categories`: official_saudi, market_industry_research, real_estate_location, competitor_primary, staffing_salary, equipment_supplier, fitout, fnb_operations
- F&B sector pack `evidence_classes`: commercial_rent, menu_pricing, salary_labor, equipment_capex, fitout_capex, furniture_pos_opening, cogs_inputs
- Evidence-class source strategy (`ai_engine/research/evidence/`): domain classes → allowlists + seed catalogs + adapters (scalable beyond coffee)
- Market planner: coffee/F&B markers force COMPETITOR, PRICING, SECTOR_SIGNAL, REGULATION research types
- Competitor extractor: café/coffee markers; empty evidence → empty list (safe); skips numeric observation / seed catalog docs
- Coverage recovery: targeted commercial re-fetch for missing material numeric keys before financials

See also: `COFFEE_OPERATING_ECONOMICS_REPORT.md`
