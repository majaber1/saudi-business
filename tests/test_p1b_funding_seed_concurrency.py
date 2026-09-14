"""P1-B: Funding program seed must be idempotent and concurrency-safe."""
from __future__ import annotations

import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

if not os.environ.get("DATABASE_URL"):
    handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    handle.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + handle.name

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app import db as app_db  # noqa: E402
from app import models  # noqa: E402
from app.services.funding_programs import (  # noqa: E402
    VERIFIED_PROGRAM_CATALOG,
    ensure_seed_programs,
)


@pytest.fixture()
def funding_db(monkeypatch):
    handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    handle.close()
    url = "sqlite:///" + handle.name
    monkeypatch.setenv("DATABASE_URL", url)
    # Rebind engine/session for this isolated sqlite file.
    app_db.engine = app_db.create_engine(url, connect_args={"check_same_thread": False})
    app_db.SessionLocal.configure(bind=app_db.engine)
    models.Base.metadata.create_all(
        bind=app_db.engine,
        tables=[models.FundingProgram.__table__, models.FundingProgramRule.__table__],
    )
    session = app_db.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_p1b_first_seed_inserts_catalog(funding_db):
    count = ensure_seed_programs(funding_db)
    assert count == len(VERIFIED_PROGRAM_CATALOG)
    slugs = {p.slug for p in funding_db.query(models.FundingProgram).all()}
    assert "sdb-excellence-track" in slugs
    assert len(slugs) == len(VERIFIED_PROGRAM_CATALOG)


def test_p1b_repeated_seed_idempotent(funding_db):
    first = ensure_seed_programs(funding_db)
    second = ensure_seed_programs(funding_db)
    third = ensure_seed_programs(funding_db)
    assert first == second == third == len(VERIFIED_PROGRAM_CATALOG)
    assert funding_db.query(models.FundingProgram).count() == len(VERIFIED_PROGRAM_CATALOG)


def test_p1b_parallel_seed_stable_unique_slugs(funding_db):
    errors: list[BaseException] = []
    results: list[int] = []

    def worker():
        session = app_db.SessionLocal()
        try:
            results.append(ensure_seed_programs(session))
        except BaseException as exc:  # noqa: BLE001 — capture for assertion
            errors.append(exc)
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert errors == [], f"unexpected seed errors: {errors}"
    assert results
    assert all(r == len(VERIFIED_PROGRAM_CATALOG) for r in results)
    session = app_db.SessionLocal()
    try:
        rows = session.query(models.FundingProgram).all()
        slugs = [r.slug for r in rows]
        assert len(slugs) == len(set(slugs)) == len(VERIFIED_PROGRAM_CATALOG)
        assert "sdb-excellence-track" in slugs
    finally:
        session.close()


def test_p1b_integrity_error_race_is_handled(funding_db):
    """Force IntegrityError on flush to prove duplicate-slug race is absorbed."""
    ensure_seed_programs(funding_db)  # prime one program path partially via normal seed
    # Clear and simulate race: pretend slug missing, then IntegrityError on flush.
    funding_db.query(models.FundingProgramRule).delete()
    funding_db.query(models.FundingProgram).delete()
    funding_db.commit()

    calls = {"n": 0}
    original_flush = funding_db.flush

    def flaky_flush(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            # Simulate concurrent unique violation on first program insert.
            raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed: funding_programs.slug"))
        return original_flush(*args, **kwargs)

    with patch.object(funding_db, "flush", side_effect=flaky_flush):
        # begin_nested path catches IntegrityError; remaining catalog still seeds.
        # Because first program hits IntegrityError inside nested tx, it is skipped;
        # ensure we still complete without raising.
        try:
            ensure_seed_programs(funding_db)
        except IntegrityError:
            pytest.fail("UniqueViolation race must be handled, not raised")


def test_p1b_unrelated_db_failure_not_swallowed(funding_db):
    def boom(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("disk I/O error"))

    with patch.object(funding_db, "query", side_effect=boom):
        with pytest.raises(OperationalError):
            ensure_seed_programs(funding_db)
