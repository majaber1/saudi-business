# Saudi Business — Product Architecture

## Core Architecture

```
Customer Account
  ↓
Organization
  ↓
Business / Project
  ↓
Independent Tools / Services
```

## Service Boundaries

Each major tool is an independent service that can:
- Be used standalone without other tools
- Be sold separately with its own subscription
- Be independently navigated via `/tools/<service>`
- Optionally link to a shared Business context

### Services

| Service | Route | API Prefix | DB Model | Status |
|---------|-------|------------|----------|--------|
| Feasibility Study | `/tools/feasibility` | `/api/feasibility` | FeasibilityStudy | Complete |
| Financial Analysis | `/tools/financial` | `/api/financial` | FinancialResult | Complete |
| Proposal Builder | `/tools/proposal` | `/api/proposals` | Proposal | MVP |
| Funding Matcher | `/tools/funding` | `/api/funding` | FundingMatch | Complete |
| Business Qualification | `/tools/qualification` | `/api/qualification` | QualificationProfile | Complete |
| Investment Opportunities | `/tools/opportunities` | `/api/opportunities` | InvestmentOpportunity | Complete |
| Franchise | `/tools/franchise` | `/api/franchises` | FranchiseOpportunity | Catalog |
| Auctions | `/tools/auctions` | `/api/auctions` | Auction | Catalog |
| Reports | `/tools/reports` | `/api/reports` | Report | Complete |

## Shared Business Context

The `Business / Project` entity provides shared context across all tools:
- Business name, sector, description
- Investment amount, stage
- Location, company profile

Each tool can:
1. **Read** shared business context (name, sector, investment)
2. **Own** its specific records (studies, proposals, matches)
3. **Link** optionally to other tool outputs

### Service Linking (Optional)

- Proposal Builder → "Import from Feasibility Study"
- Funding Matcher → "Use Business Profile"
- Reports → "Combine feasibility + financial + proposal"
- Qualification → "Apply existing business information"

Linking is always explicit and optional. Never silently combined.

## Entitlement Model

```
ServiceEntitlement
  - service_key: feasibility | financial_analysis | proposal | funding | qualification | ...
  - enabled: boolean
  - plan: starter | professional | enterprise
  - quota: integer (optional)
  - used: integer
  - reset_at: datetime (optional)
```

Development mode provides all services enabled with starter plan.

## Navigation Structure

### Primary Nav
- Dashboard
- My Businesses
- Tools
- Opportunities
- Pricing

### Tools Hub (`/tools`)
Service cards showing all available tools with status and CTA.

### Business Hub (`/businesses`)
Project cards with linked tool access.

## Future Extraction

The modular monolith design allows any service to be extracted into:
- Its own deployable service
- Its own API
- Its own subscription product

Cross-service integration happens through documented internal interfaces.
