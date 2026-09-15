# 16 — Design System Direction

## Visual Identity

### Brand Direction
- **Name**: Saudi Business
- **Tagline**: "Ideas to Impact"
- **Feel**: Premium enterprise decision intelligence — trustworthy, intelligent, authoritative
- **NOT**: Startup playful, generic SaaS, template dashboard

### Color System

**Primary Palette** (Saudi green as controlled accent — not a green-dominant theme)
- Primary accent: Deep green (#1B5E20 range) — trust, Saudi identity, growth. Used for CTAs, active states, key indicators. NOT for large surface areas.
- Primary light: Lighter green for hover states, selected row backgrounds (subtle)
- Primary dark: Darker green for emphasis on small elements (badges, icons)

**Surface Palette** (dominant visual tone — strong neutrals)
- Application background: Light warm gray (#F8F9FA)
- Card/panel surface: White (#FFFFFF)
- Sidebar: Dark neutral (#1E1E2E range) or white, depending on mode
- Headers: Neutral (not green)

**Semantic Colors**
- Success/GO: Green (#2E7D32)
- Warning/CONDITIONS: Amber (#F57F17)
- Caution/DEFER: Orange (#E65100)
- Error/NO_GO: Red (#C62828)
- Info: Blue (#1565C0)

**Evidence Class Colors**
- VERIFIED_FACT: Green (same as success)
- SYSTEM_ESTIMATE: Blue
- USER_ASSUMPTION: Amber
- UNKNOWN: Gray

**Neutral Palette**
- Background: White (#FFFFFF) / very light gray (#F8F9FA)
- Surface: White (#FFFFFF)
- Text primary: Near-black (#212121)
- Text secondary: Dark gray (#757575)
- Border: Light gray (#E0E0E0)
- Divider: Very light gray (#EEEEEE)

**Dark Mode** (Future consideration)
- Invert backgrounds to dark grays
- Maintain semantic colors with adjusted luminance
- Evidence class colors remain distinguishable

### Typography

**Font Stack**
- Latin: Inter (primary), system sans-serif fallback
- Arabic: IBM Plex Arabic or Noto Kufi Arabic (matches Inter weight range)
- Monospace: JetBrains Mono (financial figures, code)

**Scale**
- Display: 32px / 40px line height (page titles)
- H1: 24px / 32px (section headers)
- H2: 20px / 28px (subsection headers)
- H3: 16px / 24px (card headers)
- Body: 14px / 20px (primary text)
- Small: 12px / 16px (captions, metadata)
- Micro: 11px / 14px (badges, timestamps)

**Financial Figures**: Tabular numerals, monospace for alignment

### Spacing

8px base unit:
- 4px: Tight (badge padding)
- 8px: Default element spacing
- 16px: Card internal padding, section gaps
- 24px: Between card groups
- 32px: Major section separation
- 48px: Page section separation

### Elevation & Depth

- Level 0: Flat (page background)
- Level 1: Subtle shadow (cards, panels) — `0 1px 3px rgba(0,0,0,0.08)`
- Level 2: Modal, dropdown, tooltip — `0 4px 12px rgba(0,0,0,0.12)`
- Level 3: Dialog, overlay — `0 8px 24px rgba(0,0,0,0.16)`

### Border Radius
- Small: 4px (badges, small elements)
- Medium: 8px (cards, inputs)
- Large: 12px (modals, large containers)
- Round: 9999px (pills, avatar)

## Component Design Principles

### Cards
- White background, subtle border or shadow
- Clear header area with title + metadata
- Content area with consistent padding
- Action area at bottom or inline
- Evidence badges inline with data

### Data Display
- Tables: Clean, sortable, with row hover
- Charts: Minimal, evidence-linked, scenario-aware
- Metrics: Large number + trend + evidence class icon
- Ranges: Visual bar showing Low | Base | High

### Forms & Input
- Clean inputs with clear labels
- Validation inline
- Progressive disclosure (show advanced only when needed)
- Accessible: proper labels, contrast, focus states

### Navigation
- Sidebar: Fixed, collapsible, icon + text
- Tab bar: Underline style within workspace
- Breadcrumbs: Always present in workspace context
- Action buttons: Primary (filled green), Secondary (outlined), Destructive (red outlined)

## Evidence Visualization System

### Inline Badge
Small icon next to any data value:
- ✓ (green) = VERIFIED_FACT
- ▊ (blue) = SYSTEM_ESTIMATE
- ⊡ (amber) = USER_ASSUMPTION
- ? (gray) = UNKNOWN

### Confidence Bar
Thin horizontal bar (0-100%) with color gradient:
- 80-100%: Green
- 60-79%: Amber
- 40-59%: Orange
- <40%: Red

### Coverage Heatmap
Grid of information needs:
- Green cell: covered by VERIFIED_FACT
- Blue cell: covered by SYSTEM_ESTIMATE
- Amber cell: covered by USER_ASSUMPTION
- Gray cell: UNKNOWN
- Empty cell: Not yet researched

## Decision Visualization

### Decision Banner
Full-width banner at top of Decision tab:
- GO: Green background, checkmark icon
- GO_WITH_CONDITIONS: Yellow background, conditional icon
- DEFER: Orange background, clock icon
- NO_GO: Red background, X icon

### Decision Tree
Visual flow: three gates (evidence → viability → risk) with pass/fail indicators leading to outcome

## Responsive Behavior

| Breakpoint | Layout | Notes |
|------------|--------|-------|
| ≥1280px | Full desktop | Sidebar + full content |
| 1024-1279px | Compact desktop | Narrower sidebar, content adapts |
| 768-1023px | Tablet | Sidebar rail (icons only), content fills |
| <768px | Mobile | Bottom tab bar, single column, simplified |

## RTL Support

- Full RTL layout when Arabic is active
- Sidebar moves to right
- Content flow reverses
- Charts maintain readability (labels flip, data direction preserved)
- Icons: directional icons flip (arrows); non-directional icons stay
- Numbers: always LTR even in RTL context

## Accessibility

- WCAG 2.1 AA minimum
- Color is never the sole indicator — always paired with icon/text
- Focus states visible
- Screen reader labels for all interactive elements
- Keyboard navigation for all actions
- Touch targets ≥44px on mobile

## Animation & Motion

- Minimal, purposeful
- Transitions: 200ms ease for state changes
- Loading: skeleton screens (not spinners) for content areas
- Progress: subtle pulse for "AI working" states
- No decorative animation
