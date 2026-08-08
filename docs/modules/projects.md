# Module 3 — Projects

Status: **COMPLETE** for the current scoped lifecycle.

## Existing functionality

Owner-scoped create, list, read, strict partial update, archive, unarchive and
soft-delete APIs were already present with server-derived ownership and audit
events. Backend tests cover happy paths, validation, IDOR and archive behavior.

## Problems found

- No dedicated customer project workspace existed.
- Users reached projects only indirectly through feasibility.
- Archived projects had no customer-facing recovery path.
- Dashboard's "view all" returned to new feasibility rather than a project list.

## Fixes and UX changes

- Added bilingual `/projects` workspace.
- Minimal progressive creation: name, sector, approximate budget and stage.
- Added active/archive views, edit, archive and restore actions.
- Added useful empty state and direct feasibility CTA.
- Dashboard and primary navigation now link to projects.

## Security and data safety

- UI never sends owner, archive, workflow or organization fields.
- API continues to derive ownership from the authenticated user.
- Delete/archive remains reversible and preserves feasibility/report relations.

## Tests

- Existing backend project CRUD, ownership, persistence and authorization suites.
- Frontend lint, TypeScript and production build required after this change.

## Remaining limitations

- Large project lists will eventually need server pagination/search.
- Feasibility must consume the `project_id` query parameter to fully deep-link an
  existing project; until that module update, the link opens the feasibility
  workspace but does not yet preselect the saved project.
