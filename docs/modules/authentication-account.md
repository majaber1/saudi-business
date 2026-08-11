# Module 1 — Authentication & user account

Status: **PARTIAL**

The production-capable core is tested, but the module is not marked COMPLETE
because access-token refresh/revocation and device/session management are not
implemented. Those require a deliberate server-side session model rather than
pretending that clearing local storage revokes a JWT.

## Existing functionality

- Public registration with strict role allowlist and mass-assignment rejection.
- Bcrypt password hashes and maintained PyJWT signing/validation.
- Login, `/auth/me`, active-user checks and RBAC dependencies.
- Email verification and password reset with hashed, expiring, single-use tokens.
- Generic forgot-password responses, abuse limits and audit entries.
- Arabic/English login, registration, verification and recovery pages.

## Problems found

- A signed-in user could read but not update their basic profile.
- The only password-change path required email reset; there was no
  re-authenticated in-account change.
- Navbar always displayed login/register even after successful login.
- No clear account page or visible logout action.
- Raw backend errors are still surfaced by some account forms.
- JWT access tokens remain valid until expiry after client-side logout.

## Fixes and functions added

- `PATCH /auth/me` updates only `full_name` and supported locale; email, role,
  active state and organization cannot be mass-assigned.
- `POST /auth/password/change` verifies the current password, enforces the
  password policy, rejects reuse and invalidates outstanding reset links.
- Added bilingual `/account` UI for profile and password management.
- Navbar now detects authenticated state and provides account/logout actions.
- Token storage emits an application auth-change event so shared navigation
  reacts without a page reload.

## Security

- Both new endpoints require a valid active user.
- Profile input forbids unknown fields.
- Password change is rate-limited, audited and never logs passwords.
- Existing role, verification, ownership and token protections remain intact.

## Tests

- Safe profile update and whitespace normalization.
- Rejection of role/email mass assignment.
- Current-password reauthentication.
- Old-password rejection/new-password login.
- Outstanding reset-link invalidation after password change.
- Full backend suite plus frontend lint/type/build are required before merge.

## Remaining limitations

- No refresh-token rotation, server-side session inventory or immediate JWT
  revocation. Current logout removes the browser token only.
- SMTP delivery still depends on operator credentials and domain reputation.
- Browser E2E and keyboard/mobile acceptance are not yet in the repository.
