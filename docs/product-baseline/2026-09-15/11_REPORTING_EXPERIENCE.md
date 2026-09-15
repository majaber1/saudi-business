# 11 — Reporting Experience

## Principle

Reports are **outputs** of the operating system — not the product itself. They inherit live workspace data, evidence, provenance, and version history. Reports are not static documents; they are compiled snapshots of a living workspace.

## Report Types

| # | Report Type | Source Modules | Primary Audience | MVP/Later |
|---|------------|----------------|------------------|-----------|
| 1 | **Full Feasibility Study** | Feasibility Workspace (all tabs) | Investor, Bank, Owner | Phase 9+ |
| 2 | **Executive Decision Memo** | Decision tab, key financials, top risks | Board, Partners | Phase 9+ |
| 3 | **Financial Model Export** | Financials tab | CFO, Advisor, Bank | Phase 9+ |
| 4 | **Market Intelligence Report** | Market + Competitors tabs | Strategy team | Phase 9+ |
| 5 | **Competitor Analysis** | Competitors tab | Owner, Strategy | Future |
| 6 | **Location Analysis** | Location tab | Owner, Real estate | Future |
| 7 | **Risk Report** | Risks tab | Board, Compliance | Future |
| 8 | **Evidence Register** | Evidence tab | Audit, Due diligence | Phase 9+ |
| 9 | **Funding Package** | Funding module | Bank, Government program | Phase 9+ |
| 10 | **Investor Package** | Funding module + Feasibility | Investor, VC, Angel | Phase 9+ |

## Report Generation Rules

1. **Live data**: Reports compile from current workspace state at generation time
2. **Evidence inheritance**: Every claim in a report traces to its evidence item
3. **Provenance preservation**: Report shows which evidence classes support which claims
4. **Version control**: Each generation creates a versioned snapshot
5. **No fabrication**: Reports cannot add information not in the workspace
6. **UNKNOWN disclosure**: UNKNOWN items appear in reports with explicit "Not determined" labels — never omitted
7. **Confidence visible**: Overall study confidence and per-section confidence shown
8. **Decision recorded**: If a decision exists, report includes it with reasoning chain and conditions

## Report Structure (Full Feasibility Study — Reference)

```
Cover Page
  Business name, sector, location, date, version, confidence level

Executive Summary
  1-page: opportunity, investment, revenue, break-even, recommendation, key conditions

1. Business Profile
   Business description, goals, constraints, budget

2. Market Analysis
   Market size, demand, segments, trends, growth (each with evidence badges)

3. Competitive Landscape
   Competitor count, positioning, key competitors, differentiation

4. Location Analysis
   Selected location, demographics, traffic, rent benchmarks, map

5. Operating Model
   Staffing, hours, capacity, supply chain, COGS, regulatory requirements

6. Financial Analysis
   6.1 Investment Requirement (CAPEX + Working Capital)
   6.2 Revenue Model (Low/Base/High with drivers)
   6.3 Operating Costs (breakdown)
   6.4 Cash Flow Projection (chart)
   6.5 Break-even Analysis
   6.6 Budget Sufficiency
   6.7 Sensitivity Analysis

7. Risk Assessment
   Risk register, severity, mitigations

8. Evidence Register
   Full list of evidence items with classification and confidence

9. Decision
   AI recommendation, reasoning chain, conditions, owner decision

Appendices
   Source list, methodology notes, assumptions register
```

## Export Formats

| Format | Use Case |
|--------|----------|
| **PDF** | Print, email, formal submission |
| **Spreadsheet (XLSX)** | Financial model, editable data |
| **Presentation data** | Pitch deck, board presentation (structured data for user to assemble into slides) |
| **Web link** | Shareable report view (read-only, with permissions) |

## Report Center UX

- **Generate Report**: Select type → preview → generate → download/share
- **Report History**: All generated reports, versioned, with generation timestamp and workspace state at time of generation
- **Scheduled Reports**: Future — auto-generate monitoring reports on schedule
- **Share**: Generate shareable link with permission control (view-only, time-limited)

## Arabic/English

- Reports generate in the user's selected language
- Mixed-language content (business names, sources) preserved as-is
- Financial figures in SAR with locale formatting
- Bilingual report option: side-by-side AR/EN for formal submissions (Future)
