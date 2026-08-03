"""
Isolated database configuration tests (C2).

app.db resolves DATABASE_URL / POSTGRES_URL at import time. Because pytest
imports every test module into one long-lived process, importing app.db more
than once with different environment variables can silently reuse the first
import's cached module and hide real configuration bugs. Every scenario here
runs in its own throwaway subprocess with a tightly-controlled environment so
app.db is imported exactly once, fresh, per case.

Safety: no test prints, logs, or asserts against a full connection string.
The probe subprocess only emits a small JSON object of non-secret, derived
values (booleans, the SQLAlchemy dialect name, and a short "source" label).
Connection strings below (e.g. postgresql://u:p@primary-host/db) are
disposable placeholders, not real credentials.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
_RELEVANT_VARS = ("DATABASE_URL", "POSTGRES_URL", "ENVIRONMENT", "VERCEL_ENV")
_PROBE_SCRIPT = r"""
import json, os, sys
sys.path.insert(0, {backend_dir!r})
from app import db
def _norm(raw):
    if not raw: return None
    raw = raw.strip()
    if not raw: return None
    if raw.startswith("postgres://"): return "postgresql+psycopg2://" + raw[len("postgres://"):]
    if raw.startswith("postgresql://"): return "postgresql+psycopg2://" + raw[len("postgresql://"):]
    return raw
_d = _norm(os.environ.get("DATABASE_URL"))
_p = _norm(os.environ.get("POSTGRES_URL"))
if db.DATABASE_URL is None: source = "none"
elif db.DATABASE_URL == _d: source = "DATABASE_URL"
elif db.DATABASE_URL == _p: source = "POSTGRES_URL"
elif db.DATABASE_URL == "sqlite:///./demo.db": source = "demo_fallback"
else: source = "other"
result = {{"db_enabled": db.DB_ENABLED, "backend": db.safe_backend(), "engine_configured": db.engine is not None, "source": source, "scheme": (db.DATABASE_URL or "").split("://", 1)[0], "has_sslmode": bool(db.DATABASE_URL) and "sslmode=" in db.DATABASE_URL}}
print("PROBE_RESULT=" + json.dumps(result))
"""

def _run_probe(overrides):
    env = os.environ.copy()
    for v in _RELEVANT_VARS:
        env.pop(v, None)
    for k, v in overrides.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    script = _PROBE_SCRIPT.format(backend_dir=str(BACKEND_DIR))
    proc = subprocess.run([sys.executable, "-c", script], env=env, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, "probe failed exit=" + str(proc.returncode) + " stderr_tail=" + proc.stderr[-500:]
    line = next((l for l in proc.stdout.splitlines() if l.startswith("PROBE_RESULT=")), None)
    assert line is not None, "no PROBE_RESULT produced"
    for k, v in overrides.items():
        if v and any(m in v for m in ("secretpass", "sentinel", "leak-me")):
            assert v not in proc.stdout and v not in proc.stderr, k + " leaked"
    return json.loads(line[len("PROBE_RESULT="):])

@pytest.mark.parametrize("overrides,expected", [
    ({"DATABASE_URL": "postgresql://u:secretpass1@primary-host/db1", "POSTGRES_URL": "postgresql://u:secretpass2@secondary-host/db2"}, {"source": "DATABASE_URL", "db_enabled": True, "backend": "postgresql"}),
    ({"DATABASE_URL": None, "POSTGRES_URL": "postgresql://u:secretpass3@secondary-host/db2"}, {"source": "POSTGRES_URL", "db_enabled": True, "backend": "postgresql"}),
    ({"DATABASE_URL": "   ", "POSTGRES_URL": "postgresql://u:secretpass4@secondary-host/db2"}, {"source": "POSTGRES_URL"}),
    ({"DATABASE_URL": None, "POSTGRES_URL": "   ", "ENVIRONMENT": "development"}, {"source": "demo_fallback", "db_enabled": False}),
    ({"DATABASE_URL": None, "POSTGRES_URL": None, "ENVIRONMENT": "development"}, {"source": "demo_fallback", "scheme": "sqlite", "db_enabled": False, "engine_configured": True}),
    ({"DATABASE_URL": None, "POSTGRES_URL": None, "ENVIRONMENT": "production"}, {"source": "none", "engine_configured": False, "db_enabled": False}),
    ({"DATABASE_URL": None, "POSTGRES_URL": None, "ENVIRONMENT": None, "VERCEL_ENV": "production"}, {"source": "none", "engine_configured": False}),
    ({"DATABASE_URL": None, "POSTGRES_URL": None, "ENVIRONMENT": "production", "VERCEL_ENV": None}, {"source": "none", "engine_configured": False}),
    ({"DATABASE_URL": "postgres://u:secretpass5@primary-host/db1", "POSTGRES_URL": None}, {"scheme": "postgresql+psycopg2", "backend": "postgresql"}),
    ({"DATABASE_URL": "postgresql://u:secretpass6@primary-host/db1", "POSTGRES_URL": None}, {"scheme": "postgresql+psycopg2"}),
    ({"DATABASE_URL": "postgresql://u:secretpass7@primary-host/db1?sslmode=require", "POSTGRES_URL": None}, {"has_sslmode": True}),
    ({"DATABASE_URL": "sqlite:///./explicit-test.db", "POSTGRES_URL": None, "ENVIRONMENT": "development"}, {"source": "DATABASE_URL", "backend": "sqlite", "db_enabled": True}),
    ({"DATABASE_URL": "sqlite:///./explicit-test.db", "POSTGRES_URL": None, "ENVIRONMENT": "production"}, {"db_enabled": False, "engine_configured": False}),
])
def test_resolution_scenarios(overrides, expected):
    result = _run_probe(overrides)
    for key, value in expected.items():
        assert result[key] == value, key + " expected " + repr(value) + " got " + repr(result[key])


def test_explicit_sqlite_rejected_in_production_never_reports_sqlite_backend():
    result = _run_probe({"DATABASE_URL": "sqlite:///./explicit-test.db", "POSTGRES_URL": None, "ENVIRONMENT": "production"})
    assert result["backend"] != "sqlite"

def test_safe_backend_returns_only_dialect_no_connection_markers():
    result = _run_probe({"DATABASE_URL": "postgresql://sentineluser:sentinelpass99@sentinelhost:5433/sentineldb?sslmode=require", "POSTGRES_URL": None})
    backend = result["backend"]
    assert backend == "postgresql"
    for marker in ("sentineluser", "sentinelpass99", "sentinelhost", "sentineldb", "5433", "sslmode", "://", "@", "?"):
        assert marker not in backend

def test_no_secret_values_printed_in_subprocess_or_pytest_output(capfd):
    overrides = {"DATABASE_URL": "postgresql://leak-me-user:leak-me-pass@leak-me-host/leak-me-db", "POSTGRES_URL": None}
    result = _run_probe(overrides)
    assert result["backend"] == "postgresql"
    captured = capfd.readouterr()
    for marker in ("leak-me-user", "leak-me-pass", "leak-me-host", "leak-me-db"):
        assert marker not in captured.out and marker not in captured.err
