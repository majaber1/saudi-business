"""Demo-mode /health contract test (subprocess-isolated).

app.db resolves the engine URL at IMPORT time, and the rest of the suite
imports the app with a real DATABASE_URL. To exercise the development demo
fallback (no DB env vars -> sqlite:///./demo.db, DB_ENABLED=False) we spawn a
FRESH Python process with the DB env vars cleared, so there is no shared import
state. We then assert the /health persistence label is truthful: it names a
file-backed sqlite demo fallback and NEVER claims "in-memory" for a file DB.
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


def _run_demo_health():
    env = dict(os.environ)
    # Force demo mode: no explicit DB URLs, not production.
    for var in (
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRES_URL_NON_POOLING",
        "DIRECT_DATABASE_URL",
    ):
        env.pop(var, None)
    env["ENVIRONMENT"] = "development"
    env.pop("VERCEL_ENV", None)
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
    # Must signal non-durability so it is never mistaken for production storage.
    assert "non-persistent" in persistence or "demo" in persistence


def test_demo_persistence_label_matches_actual_backend():
    result = _run_demo_health()
    persistence = str(result["body"]["persistence"]).lower()
    # Never claim postgres in demo mode.
    assert "postgres" not in persistence
    # Leak-free: no connection markers in the persistence label.
    for marker in ("://", "@", "password", "sslmode"):
        assert marker not in persistence, f"leaked via persistence: {persistence}"
