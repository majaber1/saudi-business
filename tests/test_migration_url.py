"""Tests for the Alembic migration-URL resolver (database/migration_url.py).

These are pure-function tests over an INJECTED environment mapping, so they
never rely on process env, shared import state, or Alembic side effects. They
prove the migration priority (explicit DIRECT_DATABASE_URL override wins, then
the provider non-pooling endpoint, then DATABASE_URL / POSTGRES_URL) and that
the psycopg2 driver + query params are preserved.
"""
import sys
from pathlib import Path

# The resolver lives in the top-level database/ package.
_DB_DIR = Path(__file__).resolve().parents[1] / "database"
sys.path.insert(0, str(_DB_DIR))

from migration_url import (  # noqa: E402
    normalize_pg_url,
    resolve_migration_url,
    MIGRATION_URL_VARS,
)

# Distinct, non-overlapping hostnames so substring checks are unambiguous.
_POOLED = "postgresql://u:p@pooler.example.com:5432/db?sslmode=require"
_NONPOOL = "postgresql://u:p@nonpooling.example.com:5432/db?sslmode=require"
_OWNER = "postgresql://u:p@owner-override.example.com:5432/db?sslmode=require"


def test_direct_database_url_wins_over_non_pooling_when_both_present():
    # The explicit operator override must beat the provider non-pooling URL.
    env = {
        "DIRECT_DATABASE_URL": _OWNER,
        "POSTGRES_URL_NON_POOLING": _NONPOOL,
        "DATABASE_URL": _POOLED,
        "POSTGRES_URL": _POOLED,
    }
    url = resolve_migration_url(env)
    assert "owner-override.example.com" in url
    assert "nonpooling.example.com" not in url
    assert "pooler.example.com" not in url
    assert url.startswith("postgresql+psycopg2://")


def test_direct_database_url_wins_over_everything():
    env = {
        "DIRECT_DATABASE_URL": _OWNER,
        "DATABASE_URL": _POOLED,
        "POSTGRES_URL": _POOLED,
    }
    assert "owner-override.example.com" in resolve_migration_url(env)


def test_non_pooling_used_when_direct_override_absent():
    env = {
        "POSTGRES_URL_NON_POOLING": _NONPOOL,
        "DATABASE_URL": _POOLED,
        "POSTGRES_URL": _POOLED,
    }
    url = resolve_migration_url(env)
    assert "nonpooling.example.com" in url
    assert "pooler.example.com" not in url
    assert url.startswith("postgresql+psycopg2://")


def test_database_url_used_when_no_direct_endpoint():
    env = {"DATABASE_URL": _POOLED, "POSTGRES_URL": "postgresql://u@p2/db"}
    url = resolve_migration_url(env)
    assert "pooler.example.com" in url


def test_postgres_url_is_last_resort():
    env = {"POSTGRES_URL": _POOLED}
    url = resolve_migration_url(env)
    assert "pooler.example.com" in url


def test_blank_values_are_ignored_and_do_not_shadow():
    env = {
        "DIRECT_DATABASE_URL": "",
        "POSTGRES_URL_NON_POOLING": "   ",
        "DATABASE_URL": _POOLED,
    }
    url = resolve_migration_url(env)
    assert "pooler.example.com" in url


def test_returns_none_when_nothing_configured():
    assert resolve_migration_url({}) is None


def test_query_params_and_credentials_preserved():
    env = {"DATABASE_URL": _NONPOOL}
    url = resolve_migration_url(env)
    # sslmode must survive so Neon TLS still works; credentials untouched.
    assert url.endswith("?sslmode=require")
    assert "u:p@" in url


def test_normalize_rewrites_both_postgres_schemes():
    assert normalize_pg_url("postgres://a@b/c").startswith("postgresql+psycopg2://")
    assert normalize_pg_url("postgresql://a@b/c").startswith("postgresql+psycopg2://")


def test_normalize_leaves_sqlite_and_empty_untouched():
    assert normalize_pg_url("sqlite:///./x.db") == "sqlite:///./x.db"
    assert normalize_pg_url("") is None
    assert normalize_pg_url(None) is None


def test_var_priority_order_is_explicit_and_stable():
    assert MIGRATION_URL_VARS == (
        "DIRECT_DATABASE_URL",
        "POSTGRES_URL_NON_POOLING",
        "DATABASE_URL",
        "POSTGRES_URL",
    )
