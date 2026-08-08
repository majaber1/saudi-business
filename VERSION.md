# Saudi-Buisness V1

Release version: **1.0.0**

## Included

- Bilingual Arabic/English Next.js 16 interface with RTL/LTR support.
- Authentication, role-based access, projects, feasibility studies and reports.
- Financial analysis: ROI, NPV, IRR, payback, break-even and sensitivity.
- Funding matching, ideas, franchises, auctions and investment opportunities.
- Business Qualification & Readiness workspace connected to the live API.
- Admin dashboard connected to protected platform statistics and audit activity.
- PostgreSQL persistence with Alembic migrations and guarded automatic migration.
- Docker Compose stack for PostgreSQL, FastAPI and the Next.js web application.
- Same-origin backend proxy, restrictive production CORS and no embedded secrets.

## Product boundary

Saudi-Buisness assesses SME commercial, funding, tender and licensing readiness.
Institutional GRC controls and evidence remain in the separate Multazim product;
this release only records a summarized hand-off request.

## Verification target

The release is accepted only after backend tests, TypeScript checking, production
frontend build, dependency audit and archive secret scan complete successfully.
