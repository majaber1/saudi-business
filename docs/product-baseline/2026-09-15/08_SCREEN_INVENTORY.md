# 08 — Screen Inventory

## Complete Screen List

| # | Screen | Route | Module | MVP | Priority | Phase |
|---|--------|-------|--------|-----|----------|-------|
| **Auth & Onboarding** |
| S01 | Login | `/login` | Auth | Yes | P0 | 9 |
| S02 | Register | `/register` | Auth | Yes | P0 | 9 |
| S03 | Onboarding Wizard | `/onboard` | Auth | Yes | P0 | 9 |
| **Business Command Center** |
| S04 | Command Center (Home) | `/` | Command Center | Yes | P0 | 9 |
| S05 | Action Center | `/actions` | Command Center | Yes | P1 | 9 |
| **Business Portfolio** |
| S04a | My Businesses | `/businesses` | Business Portfolio | Yes | P0 | 9 |
| S04b | Business Home | `/businesses/:bid` | Business Portfolio | Yes | P0 | 9 |
| **Business Workspace & Feasibility** |
| S06 | Business/Study Creation Wizard | `/businesses/new` | Feasibility | Yes | P0 | 9 |
| S07 | Workspace — Overview | `/businesses/:bid/studies/:id` | Feasibility | Yes | P0 | 9 |
| S08 | Workspace — Market | `/businesses/:bid/studies/:id/market` | Feasibility | Yes | P0 | 9 |
| S09 | Workspace — Competitors | `/businesses/:bid/studies/:id/competitors` | Feasibility | Yes | P0 | 9 |
| S10 | Workspace — Location | `/businesses/:bid/studies/:id/location` | Feasibility | Yes | P0 | 9 |
| S11 | Workspace — Operations | `/businesses/:bid/studies/:id/operations` | Feasibility | Yes | P0 | 9 |
| S12 | Workspace — Financials | `/businesses/:bid/studies/:id/financials` | Feasibility | Yes | P0 | 9 |
| S13 | Workspace — Evidence | `/businesses/:bid/evidence` | Evidence Center | Yes | P0 | 9 |
| S14 | Workspace — Risks | `/businesses/:bid/studies/:id/risks` | Feasibility | Yes | P1 | 9 |
| S15 | Workspace — Decision | `/businesses/:bid/studies/:id/decision` | Feasibility | Yes | P0 | 9 |
| S16 | Evidence Detail Panel | `/businesses/:bid/evidence/:eid` | Evidence Center | Yes | P1 | 9 |
| S17 | Competitor Detail | `/businesses/:bid/studies/:id/competitors/:cid` | Feasibility | Phase 9+ | P2 | 9A+ |
| **Evidence Intelligence** |
| S18 | Evidence Register (Global) | `/evidence` | Evidence Center | Phase 9+ | P2 | 9A+ |
| S19 | Evidence Comparison View | `/evidence/compare` | Evidence Center | Phase 9+ | P3 | 9A+ |
| **Funding Readiness** |
| S20 | Funding Dashboard | `/businesses/:bid/funding` | Funding | Phase 9B | P2 | 9B |
| S21 | Document Checklist | `/businesses/:bid/funding/documents` | Funding | Phase 9B | P2 | 9B |
| S22 | Program Matching | `/businesses/:bid/funding/programs` | Funding | Phase 9B | P2 | 9B |
| S23 | Investor Package Builder | `/businesses/:bid/funding/investor` | Funding | Phase 9B | P3 | 9B |
| S24 | Bank Package Builder | `/businesses/:bid/funding/bank` | Funding | Phase 9B | P3 | 9B |
| **Opportunity Radar** |
| S25 | Radar Feed | `/opportunities` | Opportunity Radar | Phase 9C | P2 | 9C |
| S26 | Opportunity Detail | `/opportunities/:oid` | Opportunity Radar | Phase 9C | P2 | 9C |
| S27 | Saved Opportunities | `/opportunities/saved` | Opportunity Radar | Phase 9C | P3 | 9C |
| **Decision Simulator** |
| S28 | Simulator Home | `/businesses/:bid/simulator` | Simulator | Phase 9A | P2 | 9A |
| S29 | Scenario Builder | `/businesses/:bid/simulator/new` | Simulator | Phase 9A | P2 | 9A |
| S30 | Scenario Comparison | `/businesses/:bid/simulator/compare` | Simulator | Phase 9A | P3 | 9A |
| S31 | Scenario Library | `/businesses/:bid/simulator/scenarios` | Simulator | Phase 9A | P3 | 9A |
| **Monitoring** |
| S32 | Monitoring Dashboard | `/businesses/:bid/monitoring` | Monitoring | Phase 10 | P3 | 10 |
| S33 | Performance Detail | `/businesses/:bid/monitoring/performance` | Monitoring | Phase 10 | P3 | 10 |
| S34 | Market Watch | `/businesses/:bid/monitoring/market` | Monitoring | Phase 10 | P3 | 10 |
| S35 | Alert History | `/businesses/:bid/monitoring/alerts` | Monitoring | Phase 10 | P3 | 10 |
| **Reports & Knowledge** |
| S36 | Report Center | `/reports` | Reports | Phase 9+ | P2 | 9A+ |
| S37 | Report Viewer | `/reports/:rid` | Reports | Phase 9+ | P2 | 9A+ |
| S38 | Knowledge Hub | `/knowledge` | Knowledge | Future | P3 | 11+ |
| S39 | Decision History | `/decisions` | Reports | Phase 9+ | P3 | 9A+ |
| **Settings** |
| S40 | Profile & Organization | `/settings/profile` | Settings | Yes | P1 | 9 |
| S41 | Notifications | `/settings/notifications` | Settings | Phase 9+ | P2 | 9A+ |
| S42 | Language & Regional | `/settings/language` | Settings | Yes | P1 | 9 |
| S43 | Team & Permissions | `/settings/team` | Settings | Future | P3 | 11 |

## Summary

| Category | Screen Count | MVP | Phase 9+ | Future |
|----------|-------------|-----|----------|--------|
| Auth & Onboarding | 3 | 3 | 0 | 0 |
| Command Center | 2 | 2 | 0 | 0 |
| Business Portfolio | 2 | 2 | 0 | 0 |
| Feasibility Workspace | 12 | 11 | 1 | 0 |
| Evidence Intelligence | 2 | 0 | 2 | 0 |
| Funding Readiness | 5 | 0 | 5 | 0 |
| Opportunity Radar | 3 | 0 | 3 | 0 |
| Decision Simulator | 4 | 0 | 4 | 0 |
| Monitoring | 4 | 0 | 0 | 4 |
| Reports & Knowledge | 4 | 0 | 3 | 1 |
| Settings | 4 | 2 | 1 | 1 |
| **Total** | **45** | **20** | **19** | **6** |
