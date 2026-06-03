"""Tests for the checked-in seed blacklist (`seed/blacklist.json`)."""

import json

import pytest

import seed.blacklist as bl
from app.models import BandBlacklist
from seed.blacklist import append_entry, apply_blacklist, load_blacklist


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
            {"mbid": "abc", "name": "Acme", "reason": "off-genre"},
            {"mbid": "def", "reason": None},
        ],
    )
    stats = apply_blacklist(app_session, path)

    rows = {b.mbid: b for b in app_session.query(BandBlacklist).all()}
    assert set(rows) == {"abc", "def"}
    assert rows["abc"].name == "Acme"
    assert rows["abc"].reason == "off-genre"
    assert rows["def"].name is None
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


def test_apply_updates_changed_name(tmp_path, app_session):
    path = _write(tmp_path, [{"mbid": "abc", "name": "Old", "reason": "r"}])
    apply_blacklist(app_session, path)

    path.write_text(json.dumps([{"mbid": "abc", "name": "New", "reason": "r"}]))
    stats = apply_blacklist(app_session, path)

    assert app_session.get(BandBlacklist, "abc").name == "New"
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
    # The autouse _isolate_blacklist_file fixture redirects BLACKLIST_PATH to a
    # tmp path, so calling apply_blacklist() with no argument here verifies
    # default-path resolution (the module-level constant is what's consulted)
    # rather than reading the checked-in seed/blacklist.json.
    stats = apply_blacklist(app_session)
    assert stats == {"inserted": 0, "updated": 0, "total_in_file": 0}
    # Sanity-check that the path actually picked up was the monkeypatched one.
    assert bl.BLACKLIST_PATH.name == "no-real-blacklist.json"


def test_append_creates_file_with_new_entry(tmp_path):
    path = tmp_path / "blacklist.json"
    assert append_entry("abc", "Acme", "off-genre", path) == "added"

    assert json.loads(path.read_text()) == [
        {"mbid": "abc", "name": "Acme", "reason": "off-genre"}
    ]


def test_append_omits_name_and_reason_when_none(tmp_path):
    path = tmp_path / "blacklist.json"
    append_entry("abc", None, None, path)
    # Entries with no name/reason serialize as just {mbid}, matching the curated style.
    assert json.loads(path.read_text()) == [{"mbid": "abc"}]


def test_append_updates_existing_reason(tmp_path):
    path = _write(tmp_path, [{"mbid": "abc", "name": "Acme", "reason": "first"}])
    assert append_entry("abc", "Acme", "second", path) == "updated"
    assert json.loads(path.read_text()) == [
        {"mbid": "abc", "name": "Acme", "reason": "second"}
    ]


def test_append_updates_existing_name(tmp_path):
    # A band rename surfaces via a follow-up DELETE call; the file refreshes.
    path = _write(tmp_path, [{"mbid": "abc", "name": "Old", "reason": "r"}])
    assert append_entry("abc", "New", "r", path) == "updated"
    assert json.loads(path.read_text()) == [
        {"mbid": "abc", "name": "New", "reason": "r"}
    ]


def test_append_is_noop_when_unchanged(tmp_path):
    path = _write(tmp_path, [{"mbid": "abc", "name": "Acme", "reason": "same"}])
    mtime_before = path.stat().st_mtime_ns
    assert append_entry("abc", "Acme", "same", path) == "unchanged"
    # File untouched: no rewrite, mtime stays identical.
    assert path.stat().st_mtime_ns == mtime_before


def test_append_preserves_existing_entries(tmp_path):
    path = _write(tmp_path, [{"mbid": "a", "name": "A", "reason": "one"}])
    append_entry("b", "B", "two", path)
    assert json.loads(path.read_text()) == [
        {"mbid": "a", "name": "A", "reason": "one"},
        {"mbid": "b", "name": "B", "reason": "two"},
    ]


def test_append_writes_keys_in_canonical_order_on_update(tmp_path):
    # An entry that started life with a missing name should pick it up on the
    # next delete call and serialize in the canonical mbid/name/reason order.
    path = _write(tmp_path, [{"mbid": "abc", "reason": "r"}])
    append_entry("abc", "Acme", "r", path)
    text = path.read_text()
    assert text.index('"mbid"') < text.index('"name"') < text.index('"reason"')
