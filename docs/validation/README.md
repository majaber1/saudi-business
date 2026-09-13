# Product Validation Sprint

- Report (owner deliverable): [`PRODUCT_VALIDATION_SPRINT_REPORT.md`](./PRODUCT_VALIDATION_SPRINT_REPORT.md)
- Machine evidence: [`evidence/`](./evidence/)
- Browser harness (live local servers only): `apps/web/e2e/product_validation_sprint.spec.ts`
- Config: `apps/web/playwright.validation.config.ts`

Run (servers must already be up on `:3000` / `:8000`):

```bash
cd apps/web
npx playwright test --config=playwright.validation.config.ts
```

Artifacts land in `/opt/cursor/artifacts/product-validation/`.
Harness PASS ≠ business PASS — see the report scorecard.
