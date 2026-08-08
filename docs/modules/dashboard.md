# Module 2 — Dashboard

Status: **PARTIAL**

## Existing functionality

- Bilingual responsive dashboard with projects, feasibility studies, shortcuts,
  qualification preview and module links.
- Authenticated API loading for real projects/studies.
- Explicit demo badge when no account token exists.

## Problems found

- A signed-in API failure silently fell back to fabricated demo figures, which
  could make a user believe demo projects belonged to their account.
- The page summarized data but did not clearly recommend the next action.
- Empty project state was explanatory but lacked a direct action.
- Every project rendered in an unpaginated recent-project table.

## Fixes and UX changes

- Signed-in load failures now show an honest bilingual error and never substitute
  demo account data.
- Added a personalized next-step card based on projects/study completion:
  create first project, start feasibility, or review funding.
- Added a direct CTA to the useful empty state.
- Recent projects are limited to five rows pending a dedicated project workspace.
- Dashboard wording focuses on the decision and action rather than vanity data.

## Tests

- Frontend lint, TypeScript and production build.
- Existing authenticated project/study API tests cover the data sources.
- Browser E2E for live, empty and failed-loading states remains required.

## Remaining limitations

- Funding matches and qualification score are not yet aggregated live.
- No dedicated continue-existing-study route is available, so the current action
  returns to the feasibility workspace rather than a saved-step deep link.
- No product event analytics or notification/activity feed.
