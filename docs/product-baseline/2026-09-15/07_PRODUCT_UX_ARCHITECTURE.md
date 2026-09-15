# 07 — Product UX Architecture

## Experience Philosophy

**Enterprise decision intelligence + Modern AI SaaS + Executive business command center**

The product must communicate:
- Trust (evidence-backed, auditable)
- Intelligence (AI doing substantive work, not decoration)
- Agency (user controls decisions, AI serves)
- Persistence (workspace is alive, not a one-shot report)

## Information Architecture Principles

### 1. Progressive Disclosure
- **Level 1 (Glance)**: Key metrics, status badges, health indicators — Command Center
- **Level 2 (Understand)**: Summary sections with evidence counts, confidence, ranges — Workspace Overview
- **Level 3 (Investigate)**: Full evidence detail, provenance chains, raw sources — Evidence Center
- **Level 4 (Audit)**: Decision history, version comparison, override log — Reports & History

### 2. Evidence Visibility Without Overwhelm
Every material number surfaces its evidence class inline:
- Green checkmark = VERIFIED_FACT
- Bar chart icon = SYSTEM_ESTIMATE
- User icon = USER_ASSUMPTION
- Question mark = UNKNOWN

Click/hover reveals: source, date, confidence, derivation. Full detail in Evidence Center.

### 3. Decision-Oriented Layout
Every screen answers: "What should I decide, and based on what evidence?"
- Primary action area always visible
- Recommendation prominent but not coercive
- Override always available with tracking

### 4. Workspace Persistence
- Workspace state survives sessions
- "Continue where you left off" on return
- Study phases show progress, not completion percentage (misleading)
- All user edits/overrides preserved with timestamp

## Navigation Model

### Primary Navigation (Sidebar — Always Visible)
```
[Logo] Saudi Business
─────────────────────
[Home icon] Home
[Briefcase] My Businesses
[+ icon] New Evaluation
[Radar] Opportunity Radar
[Calculator] Simulator
[Shield] Funding
[File] Reports
[Bell/Inbox] Action Center [badge: 3]
─────────────────────
[Gear] Settings
[?] Help & Support
```

### Secondary Navigation (Context-Dependent)
Within a study workspace: tab bar (Overview | Market | Competitors | Location | Operations | Financials | Evidence | Risks | Decision)

### Tertiary Navigation
Within a tab: section anchors, filters, view toggles

## Layout System

### Desktop (Primary Experience)
```
┌──────────────────────────────────────────────┐
│ Top Bar: Search | Notifications | Language | Profile │
├────────┬─────────────────────────────────────┤
│        │                                     │
│ Side   │     Main Content Area               │
│ Nav    │                                     │
│ 240px  │     Max 1280px centered             │
│        │                                     │
│        │                                     │
├────────┴─────────────────────────────────────┤
│ (Footer only on auth pages)                  │
└──────────────────────────────────────────────┘
```

### Tablet (Responsive)
- Sidebar collapses to icon-only rail
- Content fills available width
- Cards stack to 2-column where needed

### Mobile (Functional, Not Primary)
- Sidebar becomes bottom tab bar (5 key items)
- Single column layout
- Evidence detail via bottom sheet
- Decision actions via full-screen modal
- Limited simulator capability (view results, not build complex scenarios)

## Component Architecture

### Card System
- **Study Card**: Title, sector badge, status, progress indicator, key metrics, evidence coverage bar, last updated, CTA
- **Opportunity Card**: Signal type, title, evidence count, potential score, risk badge, relevance, action buttons
- **Metric Card**: Value (range), evidence class icon, trend indicator, confidence bar
- **Risk Card**: Risk name, severity badge, likelihood, mitigation status, evidence link
- **Decision Card**: Recommendation badge (GO/CONDITIONS/DEFER/NO_GO), key conditions, CTA

### Evidence Display Components
- **Evidence Badge**: Inline icon showing classification
- **Evidence Pill**: Compact: value + class + confidence
- **Evidence Row**: Full row: value, class, source, date, confidence, actions
- **Evidence Detail Panel**: Full provenance, derivation chain, source preview, edit/override
- **Coverage Heatmap**: Grid showing information needs vs evidence status

### Financial Components
- **Scenario Bar**: Low | Base | High with visual bars
- **Financial Summary Tile**: Metric + range + evidence class + trend
- **Cash Flow Chart**: Monthly/annual with scenarios
- **Sensitivity Chart**: Tornado diagram showing impact of each variable
- **Break-even Indicator**: Timeline with confidence band

### Decision Components
- **Decision Banner**: Prominent recommendation with reasoning summary
- **Decision Tree Visual**: Stepped logic: evidence check → viability → risk → outcome
- **Condition List**: Numbered conditions with status (met/unmet/pending)
- **Owner Action Bar**: Approve | Override | Request Research — sticky at bottom

### Status & Progress
- **Study Progress**: Phase indicator (not percentage) — e.g., "Research Complete → Evidence Classification"
- **Agent Activity**: "AI is researching competitors..." with progress context
- **Alert Badge**: Notification count with severity color

## Cross-Module Navigation Rules

1. **Context preservation**: Navigating between modules preserves scroll position and filters within the originating module
2. **Breadcrumbs**: Always show: Home > [Business Workspace Name] > [Module] > [Sub-section] (Business Workspace is the first-class navigation anchor)
3. **Quick switch**: Cmd+K / search bar for global navigation to any study, opportunity, or report
4. **Related links**: Each module surfaces relevant cross-module actions (e.g., Feasibility → "Test with Simulator", "Check Funding Readiness")
5. **Action Center**: Accessible from any screen via persistent badge in sidebar
6. **Future module navigation policy**: During Phase 9, unimplemented modules (Simulator, Funding, Opportunity Radar, Monitoring) must be feature-flag hidden until enabled. No broken or dead routes. Sidebar items for unimplemented modules are not rendered until the module is available.

## State Handling

### Empty States
- **No businesses**: "Create your first Business Workspace" with prominent CTA and brief value proposition
- **No evidence yet**: "AI is researching..." with progress indicator
- **No monitoring data**: "Connect your business data or enter actuals to start monitoring"
- **No opportunities**: "Opportunity Radar is scanning — you'll be notified when relevant signals appear"

### Loading States
- **Research in progress**: Skeleton cards with "AI is researching [topic]..." 
- **Financial model computing**: Progress bar with "Building financial scenarios..."
- **Report generating**: Progress with "Compiling report from workspace data..."

### Partial/UNKNOWN States
- **Partial evidence**: Show available data with UNKNOWN badges for gaps; prominent "Fill gaps" CTA
- **Partial financials**: Show calculable metrics; mark uncalculable with "Requires: [missing input]"
- **Decision with unknowns**: Show recommendation with confidence caveat; highlight what additional research would improve

### Error/Recovery States
- **Source unavailable**: "Unable to reach [source]. Retrying..." → "Some research sources were unavailable. Evidence may be incomplete."
- **Model error**: "Financial model encountered an issue. Showing last valid result." → option to retry
- **Network error**: Toast notification + retry button. Never lose user's in-progress work.

## Bilingual Considerations (Arabic/English)

- Full RTL layout support when Arabic is active
- Language toggle in top bar (persistent preference)
- Content fields support mixed Arabic/English (business names, locations may be in either)
- Evidence sources may be in English even when UI is Arabic — display source language indicator
- Financial figures always use SAR with Arabic or English numeral preference
- Date format: Gregorian primary, Hijri secondary (user configurable)
