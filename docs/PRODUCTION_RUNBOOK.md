# Saudi-Buisness V2 production runbook

## Required configuration

- `POSTGRES_PASSWORD`: strong URL-safe password for the Compose database user.
- `JWT_SECRET`: at least 32 random characters.
- `PUBLIC_WEB_URL`: public HTTPS web origin.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, and provider credentials.
- `REQUIRE_EMAIL_VERIFICATION=true` for public production.
- `BACKEND_API_URL`: API origin used by the Next.js server-side proxy.

Never set `EXPOSE_ACCOUNT_TOKENS=true` in production. The API ignores that
setting in production, but it should remain absent as defense in depth.

## Docker deployment

```powershell
Copy-Item .env.example .env
# Replace every placeholder in .env, then:
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://localhost:8000/health/ready
```

`/health` is liveness. `/health/ready` is the deployment gate and returns 503
in production if PostgreSQL is unreachable, the JWT secret is weak, or required
email delivery is unconfigured. API containers run `alembic upgrade head` under
a PostgreSQL advisory lock when `AUTO_MIGRATE_DB=true`.

## Migration and rollback validation

```powershell
docker compose exec api alembic -c /app/database/alembic.ini current
docker compose exec api alembic -c /app/database/alembic.ini upgrade head
docker compose exec db pg_dump -U saudi_business -d saudi_business -Fc -f /tmp/pre_release.dump
```

Copy backups to protected external storage and test restoration before launch.
Do not downgrade a production schema without a reviewed data-preservation plan.

## Monitoring

- Scrape `/health/ready` from the platform load balancer or uptime monitor.
- Collect container stdout; API request events are JSON and include request ID,
  method, safe path, status, and duration—never query strings or credentials.
- Responses include `X-Request-ID` for support correlation.
- Administrators can inspect `/admin/metrics` for per-process request counts and
  average latency. Use centralized metrics for multi-instance aggregation.
- Alert on readiness failures, HTTP 5xx rate, latency, database capacity,
  migration errors, email delivery failures, and backup failures.

## Account lifecycle

Verification tokens expire after 24 hours. Password-reset tokens expire after
30 minutes. Only SHA-256 token digests are stored; tokens are single-use and a
new request invalidates the previous active token. Forgot-password responses do
not disclose whether an email address exists.

Per-instance abuse limits protect registration, login, reset/verification
requests, and lead submission. A production edge/WAF or Redis limiter is still
recommended for horizontally scaled deployments.
