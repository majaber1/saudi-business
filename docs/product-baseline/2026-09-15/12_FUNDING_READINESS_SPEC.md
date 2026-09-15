# 12 — Funding Readiness Specification

## Module Purpose

Transform a GO/GO_WITH_CONDITIONS decision into actionable funding preparation. Answer: "Am I ready to seek funding? What's missing? Which programs match? What packages do I need?"

## Entry Conditions

- Study must have an approved decision (GO or GO_WITH_CONDITIONS)
- Financial model must exist (even if partial)
- Business profile must be complete

## Funding Readiness Score

### Composite Score (0-100)

> **NOTE**: All scoring weights below are **DRAFT**, **CONFIGURABLE** (system parameters, not hardcoded), and **REQUIRE CALIBRATION** against real usage data before being treated as reliable.

Dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Financial Documentation | 25% | Financial model completeness, evidence quality, projection credibility |
| Business Plan | 20% | Business profile, market evidence, operating model clarity |
| Legal & Regulatory | 15% | Business registration, licenses, permits status |
| Market Evidence | 20% | Evidence coverage, verification level, recency |
| Management & Track Record | 10% | Team composition, relevant experience (user-provided) |
| Collateral & Guarantees | 10% | Available assets, personal guarantees (user-provided) |

### Score Display
- 80-100: "Funding Ready" (green)
- 60-79: "Nearly Ready" (yellow) — specific gaps identified
- 40-59: "Preparation Needed" (orange) — significant gaps
- 0-39: "Not Ready" (red) — major requirements missing

## Funding Requirement Calculation

```
Funding Requirement = Investment Required (from financial model)
                    = CAPEX + Working Capital

Available Funding = User's stated budget + confirmed funding

Funding Gap = Funding Requirement - Available Funding
```

Display: Visual bar showing Available vs Required with Gap highlighted.

## Document Checklist

### Required Documents (domain-configured)

| Document | Source | Status Options |
|----------|--------|---------------|
| Business Plan | Generated from workspace | Auto-generated / Draft / Final |
| Financial Projections | Generated from financial model | Auto-generated |
| Market Analysis Summary | Generated from market evidence | Auto-generated |
| CR (Commercial Registration) | User upload | Missing / Uploaded / Verified |
| IBAN Certificate | User upload | Missing / Uploaded |
| National ID / Iqama | User upload | Missing / Uploaded |
| Lease Agreement (if applicable) | User upload | Missing / Uploaded / N/A |
| Collateral Documentation | User upload | Missing / Uploaded / N/A |
| Existing Financial Statements (if existing business) | User upload | Missing / Uploaded / N/A |

### Status Tracking
- Each document: required / optional / N/A
- Status: missing / draft / uploaded / generated / verified
- Readiness impact: how much the missing document affects the readiness score

## Funding Program Matching

### Program Types
1. **Government Programs**: Monsha'at, Social Development Bank (SDB), SME Fund, sector-specific programs
2. **Bank Financing**: Commercial banks with SME lending programs
3. **Investor**: Angel investors, VC, family offices (matching criteria)

### Matching Algorithm
```
For each program:
  1. Sector eligibility check (business sector vs program sectors)
  2. Size eligibility (funding amount vs program limits)
  3. Geography eligibility (location vs program coverage)
  4. Stage eligibility (startup vs existing vs expansion)
  5. Special criteria (Saudi ownership %, employee count, Vision 2030 alignment)
  
  Eligibility Score = matched criteria / total criteria
```

### Program Card Display
- Program name and provider
- Eligibility percentage with breakdown
- Funding range available
- Key requirements (met/unmet)
- Application guidance (steps)
- "Apply" CTA (links to program or generates application package)

## Package Generation

### Investor Package
Compiled from workspace data:
1. Investment Memo (executive summary of feasibility)
2. Financial Model (exportable)
3. Market Analysis Summary
4. Competitive Positioning
5. Risk Assessment with Mitigations
6. Team/Management Profile (user-provided)
7. Funding Request (amount, terms, use of funds)

### Bank Package
Compiled from workspace data:
1. Business Plan (formal format)
2. Financial Projections (3-5 year)
3. Cash Flow Analysis
4. Collateral List
5. Owner Financial Statement
6. Market Evidence Summary
7. CR and Legal Documents

### Package Status
- Not started → In preparation → Generated → Owner approved → Submitted
- Each package version tracked
- Evidence and financial data linked at generation time (snapshot)

## Missing-Information Workflow

When gaps are identified:
1. System flags the gap (e.g., "Lease agreement needed for bank application")
2. Gap appears in Action Center
3. User can: Upload document / Mark N/A with reason / Request AI help (e.g., generate financial projection)
4. Readiness score updates in real-time as gaps are filled

## Owner Approval Gates

1. **Package review**: Owner must review and approve each generated package before it's considered "final"
2. **Application submission**: Owner confirms before any external submission guidance
3. **Funding terms**: If funding is secured, owner records terms → updates financial model

## Integration Points

- **From Feasibility**: Financial model, evidence, decision
- **To Simulator**: "What if I get funding at X% interest?" scenario
- **To Monitoring**: Post-funding tracking of terms and disbursement
- **To Reports**: Funding package as a report type
