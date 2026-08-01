"""
/health contract tests.

Verifies the health endpoint reports the database observability fields required
by the Saudi Business deployment contract (db_enabled, db_backend, db_connected)
and, critically, that it never leaks credentials, host, or the connection URL.

Runs against a throwaway file-based SQLite database configured BEFORE importing
app.db, so DB_ENABLED is True and a live ping (SELECT 1) succeeds — exercising the
real connectivity path rather than a mock.
"""
import os
import sys
import tempfile
from pathlib import Path

# Configure a file-based SQLite DB BEFORE importing the app so DB_ENABLED is True
# and the health ping can open a real connection.
if not os.environ.get("DATABASE_URL"):
    _TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _TMP.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _TMP.name

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app import db as app_db  # noqa: E402
from app.main import app  # noqa: E402


client = TestClient(app)


def test_health_reports_db_observability_fields():
    """/health must expose db_enabled, db_backend and db_connected."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()

    for field in ("status", "service", "environment", "db_enabled", "db_backend", "db_connected"):
        assert field in body, f"missing '{field}' in /health payload: {body}"

    assert body["status"] == "running"


def test_health_reports_live_connection_when_enabled():
    """With an explicit DATABASE_URL the app must report an enabled, connected DB."""
    assert app_db.DB_ENABLED is True

    body = client.get("/health").json()
    assert body["db_enabled"] is True
    # sqlite in tests; the field must be the dialect NAME only, never a URL.
    assert body["db_backend"] == "sqlite"
    assert body["db_connected"] is True


def test_health_never_leaks_credentials_or_url():
    """The backend field must be a bare dialect name — no host, user, pass or query."""
    body = client.get("/health").json()
    backend = str(body["db_backend"])

    # A safe backend name contains none of these connection-string markers.
    for marker in ("://", "@", ":", "/", "?", "password", "sslmode"):
        assert marker not in backend, f"/health leaked connection detail via '{marker}': {backend}"
