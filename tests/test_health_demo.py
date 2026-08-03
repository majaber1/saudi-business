"""Demo-mode /health contract test (subprocess-isolated).

app.db resolves the engine URL at IMPORT time, and the rest of the suite
imports the app with a real DATABASE_URL. To exercise the demo/unconfigured
fallbacks we spawn a FRESH Python process with the DB env vars cleared, so
there is no shared import state. We then assert the /health persistence label
is truthful for each state and NEVER leaks a URL or claims "in-memory" for a
file DB.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND = _REPO_ROOT / "backend"

_CHILD = r"""
import json, os, sys
sys.path.insert(0, os.environ["BACKEND_DIR"])
from app.main import app
from fastapi.testclient import TestClient
from app.db import DB_ENABLED, DATABASE_URL
body = TestClient(app).get("/health").json()
print("HEALTH_JSON:" + json.dumps({
    "body": body,
    "db_enabled": DB_ENABLED,
    "database_url": DATABASE_URL,
}))
"""


def _run_health(env_overrides):
    """Run /health in a fresh subprocess with a controlled DB environment."""
    env = dict(os.environ)
    for var in (
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRES_URL_NON_POOLING",
        "DIRECT_DATABASE_URL",
        "VERCEL_ENV",
    ):
        env.pop(var, None)
    env.update(env_overrides)
    env["BACKEND_DIR"] = str(_BACKEND)
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(_REPO_ROOT),
    )
    assert proc.returncode == 0, f"child failed: {proc.stderr}\n{proc.stdout}"
    line = next(l for l in proc.stdout.splitlines() if l.startswith("HEALTH_JSON:"))
    return json.loads(line[len("HEALTH_JSON:"):])


def _run_demo_health():
    # Development, no DB env vars -> sqlite:///./demo.db, DB_ENABLED=False.
    return _run_health({"ENVIRONMENT": "development"})


def _run_production_no_db():
    # Production, no DB env vars -> engine is None, DB_ENABLED=False.
    return _run_health({"ENVIRONMENT": "production"})


def test_demo_fallback_reports_disabled_persistence():
    result = _run_demo_health()
    assert result["db_enabled"] is False
    body = result["body"]
    assert body["db_enabled"] is False
    assert body["db_connected"] is False


def test_demo_persistence_label_is_truthful_file_sqlite():
    result = _run_demo_health()
    persistence = str(result["body"]["persistence"]).lower()
    url = str(result["database_url"] or "")

    # The demo fallback is a local FILE sqlite db, not in-memory.
    assert ":memory:" not in url, f"unexpected in-memory demo url: {url}"
    assert "sqlite" in persistence
    assert "in-memory" not in persistence, (
        f"file-backed demo must not be labeled in-memory: {persistence}"
    )
    # Truthful development label: names sqlite, demo, and non-production.
    assert "demo" in persistence
    assert "non-production" in persistence


def test_production_without_db_reports_disabled_unconfigured():
    """Production with NO Postgres URL must NOT claim a sqlite demo fallback.

    Before the fix, _persistence_label reported a sqlite demo whenever
    DB_ENABLED was False -- even in production where the engine is None. That
    was misleading. The truthful label is "disabled (database unconfigured)".
    """
    result = _run_production_no_db()
    body = result["body"]
    assert body["db_enabled"] is False
    assert body["db_connected"] is False
    # In production with no URL, there is no engine at all.
    assert result["database_url"] in (None, "", "None") or not result["database_url"]
    persistence = str(body["persistence"]).lower()
    assert "disabled" in persistence
    assert "unconfigured" in persistence
    # Never fabricate a sqlite demo fallback in production.
    assert "sqlite" not in persistence
    assert "demo" not in persistence
    # db_backend is the safe "none" sentinel (no engine).
    assert body["db_backend"] in ("none", "unknown")


def test_demo_persistence_label_matches_actual_backend():
    result = _run_demo_health()
    persistence = str(result["body"]["persistence"]).lower()
    # Never claim postgres in demo mode.
    assert "postgres" not in persistence
    # Leak-free: no connection markers in the persistence label.
    for marker in ("://", "@", "password", "sslmode"):
        assert marker not in persistence, f"leaked via persistence: {persistence}"
