# Product Validation Sprint

- Report: `PRODUCT_VALIDATION_SPRINT_REPORT.md` (primary deliverable)
- Browser harness (runs against live local servers): `apps/web/e2e/product_validation_sprint.spec.ts`
- Config: `apps/web/playwright.validation.config.ts`

Run (servers must already be up on :3000 / :8000):

```bash
cd apps/web
npx playwright test --config=playwright.validation.config.ts
```
