# Phase 9 Wave 1.5 — Owner Browser Defect Register

**Date**: 2026-09-15
**Branch**: `claude/phase9-wave1-business-os-shell-20260915`
**Reporter**: Owner browser review
**Status**: Wave 1.5 closure in progress

---

## Defect Summary

| ID | Severity | Section | Description | Status |
|----|----------|---------|-------------|--------|
| D01 | Critical | C | New Business 404 — `POST /api/backend/api/projects` double path | **FIXED** |
| D02 | Major | A | Command Center lacks AI Business OS module grid | **FIXED** |
| D03 | Major | B | Sidebar flat list — no grouped structure, no future modules | **FIXED** |
| D04 | Major | D | Duplicate study rows in Command Center and My Businesses | **FIXED** |
| D05 | Moderate | E | Evidence duplication in study workspace | **DEFERRED** (Wave 2) |
| D06 | Major | F | Study workspace fixed-height shell clips content | **FIXED** |
| D07 | Minor | F | Workspace back-link says "Projects" instead of "My Businesses" | **FIXED** |
| D08 | Critical | G | Arabic PDF renders black squares (Helvetica has no Arabic glyphs) | **FIXED** |
| D09 | Major | H | Reports show extreme ROI/IRR without trust/confidence labels | **FIXED** |
| D10 | Moderate | I | Report content lacks executive sections (risks, conditions, unknowns) | **DEFERRED** (Wave 2) |

---

## Defect Details

### D01 — New Business 404

**Root cause**: `apps/web/app/businesses/new/page.tsx` used a manual `fetch()` with incorrect URL path `/api/backend/api/projects` (double `/api/`).
**Fix**: Replaced with `createProject()` from `@/lib/api` which uses the correct `authedRequest("/projects/", ...)`.
**Verification**: Frontend build passes. Browser test with test data ("Tabea AI" / "B2B SaaS" / 350000) pending.

### D02 — Missing Module Grid

**Root cause**: Command Center (`app/page.tsx`) only showed KPI cards and business list. No visibility into platform capabilities.
**Fix**: Added 8 AI Business OS module cards with proper status (ACTIVE/BETA/COMING NEXT) based on implementation audit. Visible to both signed-in and signed-out users. COMING NEXT modules are visible but non-clickable. BETA modules without working destination are non-clickable.
**Modules**: AI Feasibility (ACTIVE), Evidence Intelligence (ACTIVE), Decision Simulator (BETA), Funding Readiness (ACTIVE), Opportunity Radar (ACTIVE), Monitoring (COMING NEXT), Reports (ACTIVE), Action Center (COMING NEXT).

### D03 — Sidebar Not Grouped

**Root cause**: `AppSidebar.tsx` had a flat list of 5 items with no grouping and no future modules visible.
**Fix**: Reorganized into 6 groups (HOME, BUSINESS, INTELLIGENCE, DECISIONS, OUTPUTS, SYSTEM) with COMING NEXT items visible but disabled (no href, `aria-disabled`, opacity-60). BETA items with `#` href shown as disabled. Active items with real routes are clickable.

### D04 — Duplicate Study Rows

**Root cause**: `listV2Studies()` returns all `StudyStateRow` entries including historical revisions per study. Frontend displayed all rows without deduplication.
**Fix**: Added `deduplicateStudies()` function to Command Center, My Businesses, and Business Home pages. Groups by `study_id`, keeps the entry with the latest `updated_at`. Each study now appears exactly once showing current state.

### D05 — Evidence Duplication (DEFERRED)

**Root cause**: Evidence items may appear multiple times across research cycles. Deduplication requires lineage key design (evidence ID, normalized claim, source URL, snapshot hash).
**Decision**: Deferred to Wave 2 — requires backend evidence deduplication query and frontend "Observed N times" grouping. Current display is functional but may show repeated claims.

### D06 — Workspace Shell Fixed Height

**Root cause**: Workspace page used `h-[calc(100vh-4rem)]` forcing a fixed viewport height, which clipped content below the fold and created nested scroll regions.
**Fix**: Changed to `min-h-0` to allow natural document flow. Removed `max-h-56 overflow-y-auto` from filled panels grid so content flows with the page. Chat area still uses `flex-1` for reasonable sizing.

### D07 — Workspace Back Link Terminology

**Root cause**: Workspace back link said "Projects" (old terminology).
**Fix**: Changed to "My Businesses" / "أعمالي" linking to `/businesses`.

### D08 — Arabic PDF Black Squares

**Root cause**: `generate_pdf()` in `reporting.py` used `Helvetica` font which contains no Arabic glyphs. Arabic text rendered as black squares.
**Fix**: Added `_register_arabic_fonts()` to register FreeSerif and FreeSerifBold from `/usr/share/fonts/truetype/freefont/`. Added `_font(locale, bold)` helper that returns Arabic-capable fonts when `locale == "ar"`. All `setFont` calls now use `_font()`.

### D09 — Missing Trust/Confidence Labels

**Root cause**: PDF and DOCX reports displayed raw financial projections (ROI, IRR, NPV) without any indication of data quality or confidence level. Extreme values (ROI 12,500%, IRR 746%) were presented without warning.
**Fix**: Added `_trust_label(result)` function that classifies results as `UNVERIFIED_PROJECTION` when ROI > 500% or IRR > 200%, otherwise `SYSTEM_ESTIMATE`. Both PDF and DOCX generators now show:
- Warning text for unverified projections
- Confidence label ("System estimate — requires independent review") for all results
- Existing disclaimer preserved

### D10 — Report Content Minimum (DEFERRED)

**Root cause**: Reports show only basic financial figures. Missing: executive summary, business profile, evidence coverage, key assumptions, market findings, risk factors, conditions, sources, confidence breakdown, unknowns.
**Decision**: Deferred to Wave 2. Requires significant report template redesign with section-based layout. Current reports are functional for financial summary with trust labels.

---

## Classification Summary

| Status | Count |
|--------|-------|
| FIXED | 8 |
| DEFERRED (Wave 2) | 2 |
| Total | 10 |

---

## Wave 2 Carry-Forward

- D05: Evidence deduplication with lineage keys and "Observed N times" grouping
- D10: Full report template with executive sections (risks, conditions, unknowns, sources, confidence)
