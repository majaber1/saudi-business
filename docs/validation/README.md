# Product Validation Sprint

## Deliverables
- Owner report: [`PRODUCT_VALIDATION_SPRINT_REPORT.md`](./PRODUCT_VALIDATION_SPRINT_REPORT.md)
- Evidence: [`evidence/`](./evidence/) (includes `integrity-classification.json`)
- Browser harness (live servers only): `apps/web/e2e/product_validation_sprint.spec.ts`
- Config: `apps/web/playwright.validation.config.ts`

## Validation Integrity Rule
Every case must be classified as one of:

| Class | Meaning | Acceptable? |
|-------|---------|-------------|
| `REAL_USER_FLOW` | Actual product workflow + real persisted Study/Research/Financial/Risk | Yes (primary) |
| `SEEDED_VALIDATION` | Approved isolated fixture; clearly marked | Yes only when labeled; cannot alone prove readiness |
| `MOCK_ONLY` | UI simulation without backend persistence | **No** |

This sprint’s three business cases are **`REAL_USER_FLOW`**. No seeded scorecard claims. No mock-only claims.  
**Do not claim product ready from mocked data.**

## Run (servers already up on `:3000` / `:8000`)

```bash
cd apps/web
npx playwright test --config=playwright.validation.config.ts
```

Artifacts: `/opt/cursor/artifacts/product-validation/`
