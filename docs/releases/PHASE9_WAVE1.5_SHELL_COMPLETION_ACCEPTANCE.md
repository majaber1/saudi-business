# Phase 9 Wave 1.5 — Shell Completion + Critical UX Defect Closure

**Date**: 2026-09-15
**Branch**: `claude/saudi-business-service-arch-udm2r3`
**Commit**: `eab67e0`
**Base**: `6d8c406` (Wave 1)

---

## Acceptance Summary

| Section | Description | Status |
|---------|-------------|--------|
| A | Command Center module grid | **PASS** |
| B | Sidebar grouped structure | **PASS** |
| C | New Business 404 fix | **PASS** |
| D | Duplicate study rows fix | **PASS** |
| E | Evidence deduplication | **DEFERRED** (Wave 2) |
| F | Study workspace shell fixes | **PASS** |
| G | Arabic PDF black squares fix | **PASS** |
| H | Report trust/confidence labels | **PASS** |
| I | Report experience minimum | **DEFERRED** (Wave 2) |
| J | Module status classification | **PASS** |
| K | Defect register | **PASS** |
| L | Browser acceptance | **PASS** (13/13) |

**Overall**: 10/12 PASS, 2/12 DEFERRED to Wave 2

---

## Section Details

### A: Command Center Module Grid — PASS

8 AI Business OS module cards rendered in a 4-column grid (signed-in) or 2-column grid (signed-out):

| Module | Status | Clickable | Destination |
|--------|--------|-----------|-------------|
| AI Feasibility | ACTIVE | Yes | /businesses |
| Evidence Intelligence | ACTIVE | Yes | /businesses |
| Decision Simulator | BETA | No (no working standalone UI) | — |
| Funding Readiness | ACTIVE | Yes | /tools/funding |
| Opportunity Radar | ACTIVE | Yes | /tools/opportunities |
| Monitoring | COMING NEXT | No | — |
| Reports | ACTIVE | Yes | /tools/reports |
| Action Center | COMING NEXT | No | — |

Module grid visible on both signed-in and signed-out states. "AI Business Operating System" subtitle added.

### B: Sidebar Grouped Structure — PASS

6 navigation groups:

| Group | Items |
|-------|-------|
| HOME | Command Center (ACTIVE) |
| BUSINESS | My Businesses (ACTIVE), New Business (ACTIVE) |
| INTELLIGENCE | Opportunity Radar (ACTIVE), Action Center (COMING NEXT, disabled) |
| DECISIONS | Funding Readiness (ACTIVE), Decision Simulator (BETA badge), Monitoring (COMING NEXT, disabled) |
| OUTPUTS | Reports (ACTIVE) |
| SYSTEM | Settings (ACTIVE) |

- COMING NEXT items: `aria-disabled="true"`, opacity-60, no href, SOON badge
- BETA items without working destination: disabled
- Group labels uppercase, 10px tracking
- Works in both desktop sidebar and mobile overlay

### C: New Business 404 — PASS

Replaced manual `fetch("/api/backend/api/projects")` with `createProject()` from `@/lib/api`. Form renders, no 404 on submit path. Browser verification screenshot captured.

### D: Duplicate Study Rows — PASS

Added `deduplicateStudies()` function to all three pages that display studies:
- `app/page.tsx` (Command Center)
- `app/businesses/page.tsx` (My Businesses)
- `app/businesses/[id]/page.tsx` (Business Home)

Groups by `study_id`, keeps entry with latest `updated_at`. Each study appears exactly once showing current state.

### E: Evidence Deduplication — DEFERRED

Requires backend evidence query changes and frontend "Observed N times" grouping with lineage key design. Recorded in defect register as D05. Functional without it — evidence displays correctly, may show repeated claims across research cycles.

### F: Study Workspace Shell — PASS

- Removed `h-[calc(100vh-4rem)]` fixed height → `min-h-0` for natural page scroll
- Removed `max-h-56 overflow-y-auto` from filled panels grid → content flows with page
- Fixed back-link: "← Projects" → "← My Businesses" / "← أعمالي"

### G: Arabic PDF Fix — PASS

- Registered FreeSerif and FreeSerifBold from `/usr/share/fonts/truetype/freefont/`
- `_font(locale, bold)` helper returns Arabic-capable fonts for `locale == "ar"`
- All `setFont()` calls updated to use `_font()`

### H: Report Trust/Confidence Labels — PASS

- `_trust_label(result)` classifies: ROI > 500% or IRR > 200% → `UNVERIFIED_PROJECTION`, else `SYSTEM_ESTIMATE`
- PDF: Warning text + confidence label rendered after financial results
- DOCX: Same trust/confidence labels added to Word output

### I: Report Experience Minimum — DEFERRED

Current reports show financial summary with trust labels. Full executive sections (business profile, evidence coverage, assumptions, market findings, scenarios, risks, conditions, sources, unknowns) require significant template redesign. Recorded as D10.

### J: Module Status Classification — PASS

Classification based on implementation audit:

| Module | Backend | Frontend | Classification |
|--------|---------|----------|---------------|
| AI Feasibility | 12+ endpoints | Multi-tab study + workspace | ACTIVE |
| Evidence Intelligence | 5 CRUD endpoints | EvidenceTab in study UI | ACTIVE |
| Decision Simulator | 3 scenario endpoints | Tab label only, no standalone UI | BETA |
| Funding Readiness | GET endpoint + evaluation | Standalone page + study tab | ACTIVE |
| Opportunity Radar | 6 match endpoints | Standalone page with filters | ACTIVE |
| Monitoring | None | None | COMING NEXT |
| Reports | PDF/DOCX generation | Download page | ACTIVE |
| Action Center | None | None | COMING NEXT |

### K: Defect Register — PASS

Created at `docs/audits/PHASE9_OWNER_BROWSER_DEFECTS_2026-09-15.md` with 10 defects (D01-D10), root cause, fix description, and status.

### L: Browser Acceptance — PASS (13/13)

| # | Test | Result |
|---|------|--------|
| L1 | Command Center signed-out AR (module grid visible) | **PASS** |
| L2 | Command Center signed-out EN (module grid visible) | **PASS** |
| L3 | Sidebar grouped EN (desktop, 6 groups) | **PASS** |
| L4 | Sidebar COMING NEXT items disabled (aria-disabled) | **PASS** |
| L5 | New Business page loads (no 404) | **PASS** |
| L6 | My Businesses page | **PASS** |
| L7 | Settings page | **PASS** |
| L8 | Dashboard redirect → / | **PASS** |
| L9 | Sidebar AR RTL | **PASS** |
| L10 | Module grid AR | **PASS** |
| L11 | Mobile Command Center | **PASS** |
| L12 | Mobile sidebar overlay | **PASS** |
| L13 | Route persistence (4/4 routes) | **PASS** |

Evidence screenshots at `docs/audits/evidence/phase9-wave1.5/`.

---

## Constraint Verification

| Constraint | Status |
|-----------|--------|
| Wave 2 not started | **YES** |
| Product architecture not redesigned | **YES** |
| Coffee PR #56 not touched | **YES** |
| No destructive schema changes | **YES** |
| No dead links created | **YES** |
| COMING NEXT: visible, disabled, no fake link | **YES** |
| ACTIVE modules: clickable with working destination | **YES** |
| BETA modules: clickable only if working destination | **YES** |
| No merge to main | **YES** |
| .env not committed | **YES** |

---

## Backend Regression

596/597 tests pass. 1 pre-existing GASTAT external connector failure (not introduced by Wave 1.5).

---

## Files Changed

### Modified
- `apps/web/app/page.tsx` — Module grid + deduplication + "AI Business OS" branding
- `apps/web/components/AppSidebar.tsx` — 6 grouped nav sections + disabled future modules
- `apps/web/app/businesses/new/page.tsx` — createProject() fix
- `apps/web/app/businesses/page.tsx` — Study deduplication
- `apps/web/app/businesses/[id]/page.tsx` — Study deduplication
- `apps/web/app/projects/[projectId]/studies/[studyId]/workspace/page.tsx` — Shell layout + terminology
- `backend/app/services/reporting.py` — Arabic fonts + trust labels (PDF + DOCX)

### New
- `docs/audits/PHASE9_OWNER_BROWSER_DEFECTS_2026-09-15.md` — Defect register
- `docs/audits/evidence/phase9-wave1.5/` — 12 browser screenshots
