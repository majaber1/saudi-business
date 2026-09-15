# 19 — Owner Decisions Required

**Status**: ALL DECISIONS RESOLVED. Owner provided answers on 2026-09-15.

See also: `00_OWNER_APPROVED_DECISIONS_AND_CORRECTIONS.md` for the authoritative record.

---

## Decision 1: MVP Scope Confirmation

**Question**: Is the proposed MVP scope (feasibility workspace end-to-end + Command Center + Action Center + My Businesses + Business Home) the right scope for Phase 9?

**Owner Decision**: **A) Approve with adjustment.** 20 MVP screens after adding My Businesses and Business Home. Screen count is not a constraint — it adjusts honestly to the Business Workspace model.

---

## Decision 2: Domain Generalization Priority

**Question**: Should Coffee-specific code audit and refactoring happen BEFORE Phase 9 implementation, or can it be done during Phase 9?

**Owner Decision**: **A) Before Phase 9.** Clean architecture first. Adds 1-2 weeks but prevents rework.

---

## Decision 3: Arabic/English Priority

**Question**: Must Arabic RTL support be in MVP, or can it follow shortly after?

**Owner Decision**: **A) MVP must be bilingual from day one.** RTL-first architecture.

---

## Decision 4: Report Generation in MVP

**Question**: Should basic PDF report generation be part of MVP?

**Owner Decision**: **A) Yes.** Include basic Feasibility Report PDF export in MVP.

---

## Decision 5: Decision Inbox Complexity

**Question**: How complex should the Decision Inbox (now "Action Center") be in MVP?

**Owner Decision**: **B) Simple notification list.** "You have N pending decisions" linking to workspace Decision tabs. Full inbox deferred to post-MVP.

---

## Decision 6: Onboarding Flow

**Question**: What should the first-use onboarding experience be?

**Owner Decision**: **A) Guided wizard (refined).** Adaptive: Profile → Goals → Add Business (Existing Business OR New Venture).

---

## Decision 7: Study Progress Representation

**Question**: How should study progress be shown to users?

**Owner Decision**: **A) Phase indicators only.** "Research → Evidence → Financial Model → Decision" with current phase highlighted. No percentage.

---

## Decision 8: Prototype Visual Direction

**Question**: Are the prototype references (green Saudi theme, enterprise density, sidebar navigation) the approved visual direction?

**Owner Decision**: **A) Yes.** Proceed with this direction.

---

## Decision 9: Module Phasing Order (Post-MVP)

**Question**: Which module should come first after MVP?

**Owner Decision**: **Modified order.**
- Phase 9A: Decision Simulator (2-3 weeks)
- Phase 9B: Funding Readiness (3-4 weeks)
- Phase 9C: Opportunity Radar (3-4 weeks)
- Phase 10: Monitoring (4-6 weeks)

Reporting is a basic export in Phase 9 (MVP), not a standalone post-MVP phase.

---

## Decision 10: Cursor Integration Strategy

**Question**: Should Cursor continue independently on Coffee validation while this product review is applied, or should all work pause until this review is approved?

**Owner Decision**: **A) Cursor continues Coffee validation independently.** Phase 9 implementation starts after this review approval.

---

## Summary

| # | Decision | Owner Answer | Status |
|---|----------|-------------|--------|
| 1 | MVP Scope | Approve as proposed | RESOLVED |
| 2 | Domain audit timing | Before Phase 9 | RESOLVED |
| 3 | Arabic/English | MVP bilingual, RTL-first | RESOLVED |
| 4 | PDF reports in MVP | Yes, basic export | RESOLVED |
| 5 | Action Center complexity | Simple notification list | RESOLVED |
| 6 | Onboarding | Guided wizard | RESOLVED |
| 7 | Progress display | Phase indicators only | RESOLVED |
| 8 | Visual direction | Approved | RESOLVED |
| 9 | Post-MVP phasing | Simulator → Funding → Radar → Monitoring | RESOLVED |
| 10 | Cursor strategy | Continue Coffee independently | RESOLVED |

**All 10 decisions are resolved. No outstanding owner decisions remain.**
