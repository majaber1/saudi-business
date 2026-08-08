// Backend origin for the same-origin proxy below. Overridable via
// BACKEND_API_URL (server-only, not exposed to the client) for other
// deployments. The safe fallback is local development only: production
// operators must set BACKEND_API_URL explicitly instead of silently sending
// credentials and business data to a stale third-party deployment.
const BACKEND_API_URL = (process.env.BACKEND_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Without this, Next.js auto-redirects /api/backend/opportunities/ ->
  // /api/backend/opportunities (308) BEFORE the rewrite runs. FastAPI then
  // 307-redirects back to the slash form -- but that second redirect's
  // Location header points at BACKEND_API_URL directly (bypassing the
  // proxy), so the client follows it as a *cross-origin* redirect and both
  // fetch() and curl correctly strip the Authorization header for security.
  // Net effect: every authenticated collection endpoint (POST /feasibility/,
  // /projects/, /leads/, ...) silently 401'd through the proxy. Disabling
  // Next's own trailing-slash handling lets the rewrite forward the request
  // in a single same-origin hop, matching FastAPI's canonical trailing-slash
  // routes exactly (see lib/api.ts call sites) -- zero redirects needed.
  skipTrailingSlashRedirect: true,
  // Proxies browser calls through this app's own origin to the FastAPI
  // backend server-side. This is what makes lib/api.ts's default
  // "/api/backend" base work without any CORS configuration on the backend:
  // the browser only ever talks to same-origin URLs; the cross-origin hop
  // happens server-to-server, where CORS does not apply. The backend's
  // production CORS policy (deny-by-default without an explicit allowlist,
  // see backend/app/core/config.py) is intentionally left untouched.
  async rewrites() {
    // :path(.*) -- a named param with an explicit regex constraint -- is
    // captured as a raw string, unlike the segment-based :path* catch-all,
    // so a trailing slash in the request survives into the destination as a
    // literal character. That desync (":path*" silently drops it) broke every
    // authenticated collection endpoint through this proxy against FastAPI's
    // trailing-slash-sensitive routes (see redirect_slashes=False in
    // backend/app/main.py).
    return [{ source: "/api/backend/:path(.*)", destination: BACKEND_API_URL + "/:path" }];
  },
};

export default nextConfig;
