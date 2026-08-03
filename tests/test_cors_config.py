"""Isolated CORS configuration tests.

These exercise the pure ``resolve_cors`` function and the ``cors_origins``
parsing validator directly, so no ASGI app, network, or shared import state is
involved. The security-critical invariant under test: a wildcard origin is
never combined with credentials, and production never serves "*".
"""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from app.core.config import (  # noqa: E402
    DEV_DEFAULT_CORS_ORIGINS,
    Settings,
    resolve_cors,
)


def test_production_strips_wildcard_and_keeps_explicit_allowlist():
    origins, creds = resolve_cors(["*", "https://app.example.com"], "production")
    assert "*" not in origins
    assert origins == ["https://app.example.com"]
    assert creds is True


def test_production_wildcard_only_denies_all_cross_origin():
    # Only "*" configured in prod -> no origins allowed (never open to everyone).
    origins, creds = resolve_cors(["*"], "prod")
    assert origins == []
    assert creds is True


def test_production_empty_denies_cross_origin():
    origins, creds = resolve_cors([], "production")
    assert origins == []
    assert creds is True


def test_development_empty_uses_safe_localhost_defaults():
    origins, creds = resolve_cors([], "development")
    assert origins == list(DEV_DEFAULT_CORS_ORIGINS)
    assert creds is True
    assert all(o.startswith("http://localhost") or o.startswith("http://127.0.0.1") for o in origins)


def test_development_wildcard_disables_credentials():
    origins, creds = resolve_cors(["*"], "development")
    assert origins == ["*"]
    # A wildcard must NEVER be paired with credentials.
    assert creds is False


def test_development_explicit_origins_allow_credentials():
    origins, creds = resolve_cors(["http://localhost:3000"], "development")
    assert origins == ["http://localhost:3000"]
    assert creds is True


def test_never_wildcard_with_credentials_across_environments():
    for env in ("development", "staging", "production", "prod"):
        origins, creds = resolve_cors(["*", "https://a.example.com"], env)
        assert not ("*" in origins and creds), f"wildcard+credentials leaked for env={env}"


def test_settings_parses_comma_separated_cors_origins():
    s = Settings(cors_origins="https://a.example.com, https://b.example.com")
    assert s.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_settings_parses_json_list_cors_origins():
    s = Settings(cors_origins='["https://a.example.com","https://b.example.com"]')
    assert s.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_settings_cors_property_is_safe_in_production():
    s = Settings(cors_origins="*", environment="production")
    origins, creds = s.cors
    assert origins == []
    assert not ("*" in origins and creds)
