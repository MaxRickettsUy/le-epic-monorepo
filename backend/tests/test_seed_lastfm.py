"""Tests for the Last.fm enrichment seeder.

Drive `enrich_lastfm_tags` with an injected `fetch_top_tags` (no network) and a
hand-seeded app DB so the seeder has bands + the curated Genre vocabulary to
key off.
"""

from __future__ import annotations

import pytest

from app.genres import CURATED_GENRES
from app.models import Band, BandGenre, Genre
from app.services.lastfm import LastfmError
from seed.lastfm_tags import WEIGHT_FLOOR, bucket_weight, enrich_lastfm_tags


@pytest.fixture()
def seeded_session(app_session):
    """An app_session pre-loaded with curated Genre rows and a few bands."""
    for slug, (name, _aliases) in CURATED_GENRES.items():
        app_session.add(Genre(slug=slug, name=name))
    app_session.flush()
    # Two enrichable bands (have an MBID) + one without (must be skipped).
    app_session.add_all(
        [
            Band(
                name="Minor Threat",
                status="split-up",
                location="",
                country="",
                label="",
                mbid="mt-gid",
                mb_tags=[],
                auto_flagged=True,
            ),
            Band(
                name="Discharge",
                status="active",
                location="",
                country="",
                label="",
                mbid="dis-gid",
                mb_tags=[],
                auto_flagged=False,
            ),
            Band(
                name="No MBID Band",
                status="active",
                location="",
                country="",
                label="",
                mbid=None,
                mb_tags=[],
            ),
        ]
    )
    app_session.commit()
    return app_session


def _fetcher(by_mbid):
    """Build a fetch callable from a {mbid: [(name, weight), ...]} mapping."""

    def _fetch(mbid):
        return by_mbid.get(mbid, [])

    return _fetch


def test_curated_tags_become_lastfm_links(seeded_session):
    fetch = _fetcher(
        {
            "mt-gid": [("youth crew", 80), ("metalcore", 40)],
            "dis-gid": [("d-beat", 100)],
        }
    )

    enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)

    links = (
        seeded_session.query(BandGenre)
        .join(Genre)
        .join(Band)
        .filter(BandGenre.source == "lastfm")
        .all()
    )
    by_band = {(link.band.name, link.genre.slug): link.vote_count for link in links}
    assert by_band == {
        ("Minor Threat", "youth-crew"): bucket_weight(80),
        ("Minor Threat", "metalcore"): bucket_weight(40),
        ("Discharge", "d-beat"): bucket_weight(100),
    }


def test_noise_and_sub_floor_tags_dropped(seeded_session):
    fetch = _fetcher(
        {
            "mt-gid": [
                ("seen live", 100),  # noise: not curated
                ("favorite", 90),  # noise: not curated
                ("metalcore", WEIGHT_FLOOR - 1),  # below floor
                ("youth crew", WEIGHT_FLOOR),  # at floor, curated → kept
            ],
        }
    )

    enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)

    links = seeded_session.query(BandGenre).filter(BandGenre.source == "lastfm").all()
    assert len(links) == 1
    assert links[0].genre.slug == "youth-crew"


def test_idempotent_rerun(seeded_session):
    fetch = _fetcher({"mt-gid": [("youth crew", 80)]})

    enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)
    enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)

    links = seeded_session.query(BandGenre).filter(BandGenre.source == "lastfm").all()
    assert len(links) == 1
    assert links[0].vote_count == bucket_weight(80)


def test_mb_link_provenance_not_flipped(seeded_session):
    """An existing MB link must stay source='mb' even if Last.fm corroborates."""
    mt = seeded_session.query(Band).filter_by(name="Minor Threat").one()
    yc = seeded_session.query(Genre).filter_by(slug="youth-crew").one()
    seeded_session.add(
        BandGenre(band_id=mt.id, genre_id=yc.id, vote_count=3, source="mb")
    )
    seeded_session.commit()

    fetch = _fetcher({"mt-gid": [("youth crew", 100)]})  # buckets to 5
    enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)

    link = (
        seeded_session.query(BandGenre)
        .filter_by(band_id=mt.id, genre_id=yc.id)
        .one()
    )
    assert link.source == "mb"
    assert link.vote_count == bucket_weight(100)  # bumped to stronger signal


def test_mb_link_not_downgraded(seeded_session):
    """A strong MB vote shouldn't be lowered by a weaker Last.fm bucket."""
    mt = seeded_session.query(Band).filter_by(name="Minor Threat").one()
    yc = seeded_session.query(Genre).filter_by(slug="youth-crew").one()
    seeded_session.add(
        BandGenre(band_id=mt.id, genre_id=yc.id, vote_count=9, source="mb")
    )
    seeded_session.commit()

    fetch = _fetcher({"mt-gid": [("youth crew", 40)]})  # buckets to 2
    enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)

    link = (
        seeded_session.query(BandGenre)
        .filter_by(band_id=mt.id, genre_id=yc.id)
        .one()
    )
    assert link.source == "mb"
    assert link.vote_count == 9


def test_auto_flag_clears_in_pass(seeded_session, tmp_path, monkeypatch):
    """An enriched band's auto_flagged must clear in the same pass."""
    import seed.genre_allowlist as al

    allowlist_file = tmp_path / "allow.json"
    allowlist_file.write_text('{"core": ["d-beat"], "ignore": []}')
    monkeypatch.setattr(al, "ALLOWLIST_PATH", allowlist_file)

    mt = seeded_session.query(Band).filter_by(name="Minor Threat").one()
    # Simulate mb_dump's verdict: MB tagged it but none of the core set hit, so
    # it was flagged. mb_tags carries enough signal for decide_auto_flag.
    mt.mb_tags = [
        {"name": "hardcore punk", "votes": 5},
        {"name": "rock", "votes": 2},
    ]
    mt.auto_flagged = True
    seeded_session.commit()

    fetch = _fetcher({"mt-gid": [("metalcore", 80)]})
    stats = enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)

    seeded_session.expire(mt)
    assert mt.auto_flagged is False
    assert stats.flags_cleared == 1


def test_no_mbid_bands_skipped(seeded_session):
    fetch = _fetcher({})
    stats = enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)
    # Only the two bands with MBIDs were checked.
    assert stats.bands_checked == 2


def test_no_api_key_no_ops(seeded_session, monkeypatch):
    from app.settings import settings as app_settings

    monkeypatch.setattr(app_settings, "lastfm_api_key", None)
    stats = enrich_lastfm_tags(seeded_session, sleep_seconds=0)
    assert stats.bands_checked == 0
    assert seeded_session.query(BandGenre).count() == 0


def test_fetcher_errors_counted_and_dont_halt_pass(seeded_session):
    """A LastfmError on one band must be counted, and other bands keep going."""

    def fetch(mbid):
        if mbid == "mt-gid":
            raise LastfmError("fetch failed: simulated network error")
        return [("d-beat", 80)]

    stats = enrich_lastfm_tags(seeded_session, fetch_top_tags=fetch, sleep_seconds=0)

    assert stats.bands_checked == 2  # both MBID-bearing bands attempted
    assert len(stats.errors) == 1
    assert "mt-gid" in stats.errors[0]
    # Discharge still got its link despite Minor Threat failing.
    discharge_links = (
        seeded_session.query(BandGenre)
        .join(Band)
        .filter(Band.name == "Discharge", BandGenre.source == "lastfm")
        .all()
    )
    assert len(discharge_links) == 1
    assert discharge_links[0].genre.slug == "d-beat"


def test_bucket_weight_floor():
    assert bucket_weight(10) == 1  # just clears the floor → min bucket
    assert bucket_weight(20) == 1
    assert bucket_weight(30) == 2
    assert bucket_weight(100) == 5


# --- service-level (app.services.lastfm.top_tags) ------------------------------


def test_top_tags_raises_on_network_error():
    """URLError from the underlying fetch must surface as a LastfmError."""
    import urllib.error

    from app.services.lastfm import top_tags

    def boom(_url):
        raise urllib.error.URLError("network unreachable")

    with pytest.raises(LastfmError, match="fetch failed"):
        top_tags("any-mbid", api_key="fake", fetch=boom)


def test_top_tags_returns_empty_on_artist_not_found():
    """Last.fm error code 6 is a clean 'no such artist' — not an error."""
    from app.services.lastfm import top_tags

    def not_found(_url):
        return {"error": 6, "message": "The artist you supplied could not be found"}

    assert top_tags("any-mbid", api_key="fake", fetch=not_found) == []


def test_top_tags_raises_on_other_lastfm_errors():
    """Non-6 Last.fm error payloads (rate limit, auth, etc.) must raise."""
    from app.services.lastfm import top_tags

    def rate_limited(_url):
        return {"error": 29, "message": "Rate limit exceeded"}

    with pytest.raises(LastfmError, match="error 29"):
        top_tags("any-mbid", api_key="fake", fetch=rate_limited)
