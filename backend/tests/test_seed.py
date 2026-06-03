"""Seed tests against a minimal MusicBrainz-shaped SQLite fixture.

The fixture mirrors the real MB table/column names the seed SQL targets, so the
same queries that run against the full dump are exercised here in-process.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.genres import CURATED_GENRES
from app.models import Album, Band, BandBlacklist, BandGenre, BandMember, Genre, Member
from seed import band_art, cover_art
from seed.mb_dump import MEMBER_OF_BAND_GID, run_seed

MB_SCHEMA = """
CREATE TABLE area (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE artist (id INTEGER PRIMARY KEY, gid TEXT, name TEXT, area INTEGER, ended INTEGER, begin_date_year INTEGER, end_date_year INTEGER);
CREATE TABLE tag (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE artist_tag (artist INTEGER, tag INTEGER, count INTEGER);
CREATE TABLE artist_credit_name (artist_credit INTEGER, artist INTEGER, position INTEGER);
CREATE TABLE release_group_primary_type (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE release_group (id INTEGER PRIMARY KEY, gid TEXT, name TEXT, artist_credit INTEGER, type INTEGER);
CREATE TABLE release_group_meta (id INTEGER PRIMARY KEY, first_release_date_year INTEGER);
CREATE TABLE link_type (id INTEGER PRIMARY KEY, gid TEXT, name TEXT);
CREATE TABLE link (id INTEGER PRIMARY KEY, link_type INTEGER);
CREATE TABLE l_artist_artist (id INTEGER PRIMARY KEY, link INTEGER, entity0 INTEGER, entity1 INTEGER);
CREATE TABLE link_attribute_type (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE link_attribute (link INTEGER, attribute_type INTEGER);
CREATE TABLE url (id INTEGER PRIMARY KEY, url TEXT);
CREATE TABLE l_artist_url (id INTEGER PRIMARY KEY, link INTEGER, entity0 INTEGER, entity1 INTEGER);
"""

MB_DATA = [
    # Global areas.
    "INSERT INTO area VALUES (1,'United States'),(2,'United Kingdom'),(3,'Japan')",
    # tag 1 is the scope tag; 3-5 are curated sub-genres (4 is an alias of 3);
    # 2 and 6 are non-curated and must be ignored.
    # tag 6 ('rock') stands in for any tag that isn't in CURATED_GENRES — the
    # earlier 'emo' choice got absorbed when the vocabulary expanded, so picking
    # a clearly out-of-scope label keeps the "non-curated tags drop" assertion
    # honest even as the vocabulary grows.
    "INSERT INTO tag VALUES "
    "(1,'hardcore punk'),(2,'indie'),(3,'youth crew'),(4,'youthcrew'),(5,'d-beat'),(6,'rock')",
    # Bands: Minor Threat (US, split-up), Discharge (UK, active), GauZe (JP),
    # plus an off-genre band that must be excluded.
    "INSERT INTO artist VALUES "
    "(10,'mt-gid','Minor Threat',1,1,1980,1983),"
    "(11,'dis-gid','Discharge',2,0,1977,NULL),"
    "(12,'gauze-gid','GauZe',3,0,NULL,NULL),"
    "(99,'indie-gid','Indie Co',1,0,NULL,NULL),"
    # Member persons (also artists, but untagged so not seeded as bands).
    "(20,'ian-gid','Ian MacKaye',1,0,NULL,NULL),"
    "(21,'cal-gid','Cal Morris',2,0,NULL,NULL)",
    "INSERT INTO artist_tag VALUES (10,1,5),(11,1,3),(12,1,2),(99,2,4),"
    # Sub-genre tags: Minor Threat -> youth crew (votes 7) + the 'youthcrew'
    # alias (votes 3, same genre) + 'rock' (non-curated). Discharge -> d-beat.
    # GauZe gets none. Indie Co (99) is off-genre and not seeded at all.
    "(10,3,7),(10,4,3),(10,6,2),(11,5,9)",
    # artist_credit ids reuse the artist id + 100 for clarity.
    "INSERT INTO artist_credit_name VALUES (110,10,0),(111,11,0),(112,12,0)",
    "INSERT INTO release_group_primary_type VALUES (1,'Album'),(3,'EP')",
    "INSERT INTO release_group VALUES "
    "(200,'rg-mt','Out of Step',110,3),"
    "(201,'rg-dis','Hear Nothing Say Nothing',111,1),"
    "(202,'rg-gauze','Equalizing Distort',112,1)",
    "INSERT INTO release_group_meta VALUES (200,1983),(201,1982),(202,1986)",
    f"INSERT INTO link_type VALUES (1,'{MEMBER_OF_BAND_GID}','member of band'),"
    f"(2,'{band_art.WIKIDATA_LINK_GID}','wikidata')",
    "INSERT INTO link VALUES (1,1),(2,1),(3,2),(4,2)",
    # entity0 = member person, entity1 = band. Both members in Minor Threat.
    "INSERT INTO l_artist_artist VALUES (1,1,20,10),(2,2,21,10)",
    "INSERT INTO link_attribute_type VALUES (1,'vocals')",
    "INSERT INTO link_attribute VALUES (1,1)",  # link 1 (Ian) -> vocals
    # Wikidata URLs: Minor Threat -> Q123, Discharge -> Q456. GauZe has none.
    "INSERT INTO url VALUES (1,'https://www.wikidata.org/wiki/Q123'),"
    "(2,'https://www.wikidata.org/wiki/Q456')",
    "INSERT INTO l_artist_url VALUES (1,3,10,1),(2,4,11,2)",
]


@pytest.fixture()
def mb_engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as conn:
        for stmt in MB_SCHEMA.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
        for stmt in MB_DATA:
            conn.execute(text(stmt))
    return engine


def test_seed_populates_bands_albums_members(mb_engine, app_session):
    stats = run_seed(mb_engine, app_session, tag="hardcore punk")

    assert stats.bands_inserted == 3  # MT, Discharge, GauZe — Indie Co excluded
    assert stats.albums_inserted == 3
    assert stats.members_inserted == 2
    assert stats.links_inserted == 2

    bands = {b.name: b for b in app_session.query(Band).all()}
    assert set(bands) == {"Minor Threat", "Discharge", "GauZe"}
    assert bands["Minor Threat"].status == "split-up"
    assert bands["Discharge"].status == "active"
    assert bands["GauZe"].country == "Japan"
    assert (bands["Minor Threat"].begin_year, bands["Minor Threat"].end_year) == (1980, 1983)
    assert (bands["Discharge"].begin_year, bands["Discharge"].end_year) == (1977, None)
    assert (bands["GauZe"].begin_year, bands["GauZe"].end_year) == (None, None)

    mt = bands["Minor Threat"]
    assert {a.name for a in mt.releases} == {"Out of Step"}
    out_of_step = mt.releases[0]
    assert out_of_step.release_type == "EP"
    assert out_of_step.year == 1983
    assert out_of_step.release_group_mbid == "rg-mt"

    roles = {bm.member.name: bm.role for bm in mt.members}
    assert roles == {"Ian MacKaye": "vocals", "Cal Morris": None}


def test_seed_is_idempotent(mb_engine, app_session):
    run_seed(mb_engine, app_session, tag="hardcore punk")
    stats2 = run_seed(mb_engine, app_session, tag="hardcore punk")

    assert app_session.query(Band).count() == 3
    assert app_session.query(Album).count() == 3
    assert app_session.query(Member).count() == 2
    assert app_session.query(BandMember).count() == 2
    assert stats2.bands_inserted == 0
    assert stats2.bands_updated == 3
    assert stats2.links_inserted == 0


def test_seed_links_curated_subgenres(mb_engine, app_session):
    stats = run_seed(mb_engine, app_session, tag="hardcore punk")

    # The whole curated vocabulary is upserted regardless of usage.
    assert app_session.query(Genre).count() == len(CURATED_GENRES)

    # Minor Threat -> youth-crew (the 'youthcrew' alias collapses in, 'rock' is
    # dropped); Discharge -> d-beat; GauZe -> nothing.
    bands = {b.name: b for b in app_session.query(Band).all()}
    mt_genres = {g.slug: g.vote_count for g in bands["Minor Threat"].genres}
    assert mt_genres == {"youth-crew": 7}  # max of the two aliases (7 vs 3)
    assert {g.slug for g in bands["Discharge"].genres} == {"d-beat"}
    assert bands["GauZe"].genres == []

    # Two distinct (band, genre) links created; no double-count from the alias.
    assert stats.genres_linked == 2
    assert app_session.query(BandGenre).count() == 2


def test_seed_subgenres_idempotent(mb_engine, app_session):
    run_seed(mb_engine, app_session, tag="hardcore punk")
    stats2 = run_seed(mb_engine, app_session, tag="hardcore punk")

    assert app_session.query(Genre).count() == len(CURATED_GENRES)
    assert app_session.query(BandGenre).count() == 2
    assert stats2.genres_linked == 0
    assert stats2.genre_links_updated == 0


def test_seed_applies_blacklist_json_before_filtering(
    mb_engine, app_session, tmp_path, monkeypatch
):
    # A checked-in blacklist entry should be upserted into band_blacklist by
    # run_seed itself, so a fresh DB stays sticky without having to first call
    # the delete endpoint manually.
    blacklist_file = tmp_path / "blacklist.json"
    blacklist_file.write_text(
        '[{"mbid": "gauze-gid", "reason": "checked-in: not hardcore"}]'
    )
    import seed.blacklist as bl

    monkeypatch.setattr(bl, "BLACKLIST_PATH", blacklist_file)

    stats = run_seed(mb_engine, app_session, tag="hardcore punk")

    names = {b.name for b in app_session.query(Band).all()}
    assert "GauZe" not in names
    assert names == {"Minor Threat", "Discharge"}
    assert stats.bands_blacklisted == 1
    entry = app_session.get(BandBlacklist, "gauze-gid")
    assert entry is not None
    assert entry.reason == "checked-in: not hardcore"


def test_seed_skips_blacklisted_mbids(mb_engine, app_session):
    # First pass seeds all three bands.
    run_seed(mb_engine, app_session, tag="hardcore punk")
    assert app_session.query(Band).count() == 3

    # Curator removes GauZe and blacklists its MBID — the same path the
    # delete endpoint takes.
    gauze = app_session.query(Band).filter_by(name="GauZe").one()
    app_session.add(BandBlacklist(mbid=gauze.mbid, reason="not hardcore"))
    app_session.delete(gauze)
    app_session.commit()

    stats = run_seed(mb_engine, app_session, tag="hardcore punk")

    names = {b.name for b in app_session.query(Band).all()}
    assert "GauZe" not in names
    assert names == {"Minor Threat", "Discharge"}
    assert stats.bands_blacklisted == 1
    # Albums that belonged only to the skipped artist aren't resurrected either.
    assert app_session.query(Album).filter_by(release_group_mbid="rg-gauze").count() == 0


def test_cover_art_sets_only_found_art(mb_engine, app_session):
    run_seed(mb_engine, app_session, tag="hardcore punk")

    # Fake CAA: only the Minor Threat release-group has a front image.
    found = {cover_art.cover_art_url("rg-mt")}
    stats = cover_art.fetch_cover_art(app_session, check=lambda url: url in found)

    assert stats["set"] == 1
    assert stats["missing"] == 2
    art = {a.release_group_mbid: a.art for a in app_session.query(Album).all()}
    assert art["rg-mt"] == cover_art.cover_art_url("rg-mt")
    assert art["rg-dis"] is None


def test_band_art_sets_picture_and_logo_from_wikidata(mb_engine, app_session):
    run_seed(mb_engine, app_session, tag="hardcore punk")

    # Fake Wikidata: Q123 has both image + logo; Q456 has only an image.
    def fake_resolve(qids):
        catalog = {
            "Q123": {"image": "Minor Threat band.jpg", "logo": "MT logo.svg"},
            "Q456": {"image": "Discharge.png", "logo": None},
        }
        return {q: catalog[q] for q in qids if q in catalog}

    stats = band_art.fetch_band_art(mb_engine, app_session, resolve=fake_resolve)

    assert stats.checked == 3  # MT, Discharge, GauZe — all eligible (no art yet)
    assert stats.picture_set == 2
    assert stats.logo_set == 1
    assert stats.no_wikidata == 1  # GauZe has no wikidata link

    bands = {b.name: b for b in app_session.query(Band).all()}
    assert bands["Minor Threat"].band_picture == band_art.commons_url("Minor Threat band.jpg")
    assert bands["Minor Threat"].logo == band_art.commons_url("MT logo.svg")
    assert bands["Discharge"].band_picture == band_art.commons_url("Discharge.png")
    assert bands["Discharge"].logo is None
    assert bands["GauZe"].band_picture is None


def test_band_art_only_fills_missing_fields(mb_engine, app_session):
    run_seed(mb_engine, app_session, tag="hardcore punk")

    # First pass: pictures only, no logos.
    def first(qids):
        return {q: {"image": f"{q}-first.jpg", "logo": None} for q in qids}

    band_art.fetch_band_art(mb_engine, app_session, resolve=first)

    # Second pass: Wikidata now exposes both fields. Pictures are already set,
    # so they must not be overwritten — only the still-null logos get filled.
    def second(qids):
        return {q: {"image": f"{q}-second.jpg", "logo": f"{q}-logo.svg"} for q in qids}

    stats2 = band_art.fetch_band_art(mb_engine, app_session, resolve=second)

    assert stats2.picture_set == 0  # already set; not clobbered
    assert stats2.logo_set == 2  # Minor Threat + Discharge

    bands = {b.name: b for b in app_session.query(Band).all()}
    assert bands["Minor Threat"].band_picture == band_art.commons_url("Q123-first.jpg")
    assert bands["Minor Threat"].logo == band_art.commons_url("Q123-logo.svg")
    assert bands["Discharge"].band_picture == band_art.commons_url("Q456-first.jpg")
    assert bands["Discharge"].logo == band_art.commons_url("Q456-logo.svg")
