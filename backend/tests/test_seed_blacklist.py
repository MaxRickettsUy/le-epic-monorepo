"""Tests for the checked-in seed blacklist (`seed/blacklist.json`)."""

import json

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import BandBlacklist
from seed.blacklist import apply_blacklist, load_blacklist


@pytest.fixture()
def app_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()
    yield db
    db.close()


def _write(tmp_path, payload):
    path = tmp_path / "blacklist.json"
    path.write_text(json.dumps(payload))
    return path


def test_load_missing_file_returns_empty(tmp_path):
    assert load_blacklist(tmp_path / "nope.json") == []


def test_load_rejects_non_list(tmp_path):
    path = _write(tmp_path, {"mbid": "x"})
    with pytest.raises(ValueError, match="JSON list"):
        load_blacklist(path)


def test_load_rejects_missing_mbid(tmp_path):
    path = _write(tmp_path, [{"reason": "no key"}])
    with pytest.raises(ValueError, match="'mbid' key"):
        load_blacklist(path)


def test_apply_inserts_new_entries(tmp_path, app_session):
    path = _write(
        tmp_path,
        [
            {"mbid": "abc", "reason": "off-genre"},
            {"mbid": "def", "reason": None},
        ],
    )
    stats = apply_blacklist(app_session, path)

    rows = {b.mbid: b for b in app_session.query(BandBlacklist).all()}
    assert set(rows) == {"abc", "def"}
    assert rows["abc"].reason == "off-genre"
    assert rows["def"].reason is None
    assert stats == {"inserted": 2, "updated": 0, "total_in_file": 2}


def test_apply_is_idempotent_and_updates_changed_reason(tmp_path, app_session):
    path = _write(tmp_path, [{"mbid": "abc", "reason": "first"}])
    apply_blacklist(app_session, path)

    path.write_text(json.dumps([{"mbid": "abc", "reason": "second"}]))
    stats = apply_blacklist(app_session, path)

    assert app_session.query(BandBlacklist).count() == 1
    assert app_session.get(BandBlacklist, "abc").reason == "second"
    assert stats == {"inserted": 0, "updated": 1, "total_in_file": 1}


def test_apply_preserves_db_only_entries(tmp_path, app_session):
    # An MBID blacklisted at runtime (via DELETE /band/{id}/delete) but not yet
    # in the file must NOT be removed when the file is re-applied.
    app_session.add(BandBlacklist(mbid="db-only", reason="from API"))
    app_session.commit()

    path = _write(tmp_path, [{"mbid": "from-file"}])
    apply_blacklist(app_session, path)

    mbids = {b.mbid for b in app_session.query(BandBlacklist).all()}
    assert mbids == {"db-only", "from-file"}


def test_apply_uses_default_path_when_omitted(app_session):
    # Smoke test: the default path exists and parses (even if empty).
    stats = apply_blacklist(app_session)
    assert "total_in_file" in stats
