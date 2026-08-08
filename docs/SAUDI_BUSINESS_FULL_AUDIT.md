# Saudi Business full repository audit

Audit date: 2026-08-09. Evidence comes from source, routes, migrations, tests,
local PostgreSQL/Docker runtime and production builds—not README claims.

Status key: **GREEN** production-capable core; **YELLOW** partially complete;
**RED** broken or materially incomplete; **GRAY** not implemented.

## Architecture

- Frontend: Next.js 16 App Router, React 19, TypeScript, Tailwind, client-side locale provider, Arabic-first RTL and English LTR. Eighteen customer/admin pages plus framework routes build successfully.
- Backend: FastAPI with SQLAlchemy ORM, PyJWT, RBAC dependencies, owner-scoped resources, report generation, health/readiness and in-process monitoring/rate limiting.
- Data: PostgreSQL 16 production stack; SQLite portability for tests. Six immutable Alembic revisions currently end at `0006_account_security`.
- Deployment: Docker Compose runs PostgreSQL/API/Web with health gates. Vercel currently has separate API and Web projects; Web uses `apps/web/vercel.json`.
- Tests: 191 backend tests plus frontend lint/type/build and PostgreSQL migration CI. Browser E2E and visual/mobile regression are absent.
- AI: `ai-engine` and `knowledge-base` contain design notes only; no callable grounded advisor exists.

## Module inventory

| Module | Existing | Working | Missing | Bugs | UX Issues | Tests | Priority |
|---|---|---|---|---|---|---|---|
| Authentication & account | Register/login/me, PyJWT, bcrypt, RBAC, verification and reset tokens | **YELLOW** core flows and abuse limits pass | Profile edit, in-account password change, refresh/session revocation, device/session view | Test keys trigger weak-key warnings; SMTP is external | Forms are simple but account lifecycle is fragmented; no profile screen | Strong backend auth/security coverage; no browser E2E | P0 |
| Dashboard | Live projects/studies plus demo fallback and module shortcuts | **YELLOW** page builds and authenticated loading exists | Next-action engine, recent continuation, funding/readiness aggregation | Demo fallback can obscure why live data failed | Too many equal modules; limited personalized guidance | Build only; no dedicated UI/E2E tests | P0 |
| Projects | Owner-scoped create/list/read/update/archive/unarchive/soft-delete | **GREEN** API core | Dedicated project UI, richer filters, minimal progressive form | No critical ownership bug found | Project work is embedded in feasibility rather than a clear workspace | CRUD, ownership, IDOR and persistence tests | P0 |
| Idea bank | List/detail/admin create API and page | **YELLOW** catalog browsing | Budget/city/experience/type/risk/B2B filters, verification enum, AI generation abstraction | `source` is free text; status cannot express all required provenance | Cards do not guide fit or next action deeply | Aggregate router auth tests; weak catalog-specific coverage | P1 |
| Feasibility study | Create/list/get/step-save/compute, financial assumptions/results, PDF/DOCX | **YELLOW** core journey works | Market/funding steps, clearer result decision model, resume UX, browser E2E | Six-step product vision is compressed in current wizard | Still finance-led; contextual help and progressive disclosure incomplete | Engine math, persistence/auth and report ownership tests | P0 |
| Feasibility result | ROI/NPV/IRR/payback/break-even/verdict/sensitivity | **YELLOW** deterministic calculations | Overall score and market/risk/funding/execution explanations | Verdict is narrow and lacks calibrated reasons | Numbers dominate over plain-language decision/actions | Mathematical unit tests exist; no visual acceptance | P0 |
| Funding | Explainable rules matcher and funding-program model | **YELLOW** matching engine works | Persistent catalog API/admin ownership, user questionnaire, verification workflow | Seed/catalog freshness cannot be guaranteed | Technical matching inputs; insufficient guided eligibility flow | Funding engine unit tests | P1 |
| Investment opportunities | List/detail/filter by industry/risk/ticket; admin create | **YELLOW** API/page function | Region/source-review dates/comparison/personal fit | Expected returns remain source-dependent demo data | Needs stronger verification and risk messaging | Opportunity/lead and authz tests | P1 |
| Franchises | List/detail/filter and admin create | **YELLOW** catalog works | Comparison, region/fee requirements filtering, review workflow | Commercial terms may become stale | Limited decision support | Aggregate authz tests | P1 |
| Auctions | List/detail/admin create and authenticated expression-of-interest bids | **YELLOW** non-payment workflow works | Source URL/verification fields, expiry UI, connectors architecture | Model lacks explicit source provenance | Could be mistaken for transactional auction/escrow | Aggregate authz tests | P1 |
| Business qualification | Profiles, requirements, score, recommendations, Multazim hand-off | **YELLOW** substantial API/page | Digital/market/funding readiness simplification and richer dashboard linkage | No critical ownership bug found | Terminology is still compliance-heavy in places | Dedicated qualification tests | P1 |
| Pricing & leads | Pricing page, public lead submission, admin list, rate limit | **YELLOW** request-access model works | Consent fields, lead status/update, pagination, production anti-bot | No payment exists (correctly not faked) | Pricing should state contact/request model more plainly | Lead validation/auth tests | P1 |
| Reports | Authenticated owner-checked PDF/DOCX generation | **YELLOW** downloads work | Branded cover/executive summary/assumptions/risks, durable storage | Arabic visual quality is not regression-tested | Output needs stronger investor/bank presentation | Ownership and generation coverage; no visual tests | P1 |
| Admin | Stats, audit, user list/create, lead inbox | **YELLOW** secure foundation | Pagination, edits/status transitions, catalog governance UI | Large lists can grow unbounded | Functional, not yet operator-efficient | Admin/router authz coverage | P2 |
| Arabic/English | Locale provider, RTL/LTR, bilingual primary content | **YELLOW** core UI builds in both | Full module copy audit and report visual tests | Some raw English finance terms and mixed wording remain | Arabic is professional but sometimes consultant-oriented | Build/type only | P0 |
| Design system | Tailwind tokens and repeated card/button patterns | **RED** informal patterns only | Reusable Button/Card/Status/Progress/Stepper/Empty/Table/Form/Modal/Tooltip system | Duplication encourages drift | Pages feel related but not governed by components | No component/accessibility tests | P1 |
| AI business advisor | Markdown agent/RAG concepts | **GRAY** no runtime | Grounded provider abstraction, citations, evals, budgets, deterministic fallback | Not callable | No UI | None | P3 |
| Analytics | Request monitoring counters | **RED** operational metrics only | Privacy-conscious product event abstraction and consent policy | No funnel/product events | No product insight loop | Monitoring tests only | P2 |
| Payments | None; leads only | **GRAY** intentionally absent | PSP/account decision and compliant implementation | N/A | Pricing must avoid implying checkout | None | P3/external |

## Cross-cutting findings

### Security

- Positive: server-derived ownership, role gates, hashed one-time account tokens,
  generic reset responses, explicit production secrets, CORS policy and IDOR tests.
- Gaps: access tokens cannot be revoked; limits/monitoring are process-local; real
  multi-instance deployment needs Redis or equivalent; no CSP/security-header
  acceptance suite; SMTP and backup operations remain external.

### Data trust

Funding programs and franchises have verification fields, and investment
opportunities carry a status, but provenance is not consistent across ideas and
auctions. Production catalogs need a shared verification vocabulary, source URL,
verified/reviewed timestamps and accountable editor workflow.

### UX and accessibility

The interface is Arabic-first and responsive at CSS level, with visible focus
styling and semantic tables/forms in several areas. It still lacks a guided
"what do you want to do?" entry, consistent reusable primitives, tested keyboard
flows, useful empty states everywhere and mobile/browser acceptance tests.

### Performance and operations

Current catalogs and admin lists are small and mostly unpaginated. Report
generation is synchronous. Monitoring is per process. Add pagination/query
measurement, async report jobs only when volume requires it, centralized metrics,
backups and restore drills before scale.

## Prioritized execution order

1. Authentication/account UX and lifecycle completion.
2. Dashboard and guided business-journey entry.
3. Project workspace and simple creation.
4. Idea discovery/provenance.
5. Feasibility wizard and plain-language results.
6. Funding, opportunities, franchises and auctions with shared source governance.
7. Qualification, pricing/leads and professional reports.
8. Shared design system, accessibility/mobile E2E, analytics and performance.
9. Grounded AI advisor only after trusted platform data and evaluation gates exist.

## Current quality scores (evidence-based)

| Category | Score / 10 | Main reason below 9 |
|---|---:|---|
| Functionality | 7.5 | Core modules exist, but several are catalogs/foundations rather than complete journeys. |
| UX | 6.5 | No central guided journey; advanced concepts surface too early. |
| UI | 7.0 | Consistent visual direction, but no formal reusable component system or visual tests. |
| Arabic | 7.0 | First-class RTL, but copy remains technical in important flows. |
| English | 7.5 | Broad coverage; full natural-language audit is missing. |
| Security | 8.0 | Strong API controls; session revocation and centralized controls remain. |
| Testing | 7.5 | Strong backend/CI baseline; browser, mobile and visual coverage missing. |
| Performance | 6.5 | No measured budgets, pagination strategy or load tests. |
| Maintainability | 7.0 | Clear modules, but frontend duplication and mixed catalog governance. |
| Business value | 7.5 | Useful feasibility core; guided advisor experience is not complete. |

No claim of 9/10 production readiness is justified at this audit point.
