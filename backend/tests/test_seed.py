"""Seed tests against a minimal MusicBrainz-shaped SQLite fixture.

The fixture mirrors the real MB table/column names the seed SQL targets, so the
same queries that run against the full dump are exercised here in-process.
"""

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Album, Band, BandMember, Member
from seed import cover_art
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
"""

MB_DATA = [
    # Global areas.
    "INSERT INTO area VALUES (1,'United States'),(2,'United Kingdom'),(3,'Japan')",
    "INSERT INTO tag VALUES (1,'hardcore punk'),(2,'indie')",
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
    "INSERT INTO artist_tag VALUES (10,1,5),(11,1,3),(12,1,2),(99,2,4)",
    # artist_credit ids reuse the artist id + 100 for clarity.
    "INSERT INTO artist_credit_name VALUES (110,10,0),(111,11,0),(112,12,0)",
    "INSERT INTO release_group_primary_type VALUES (1,'Album'),(3,'EP')",
    "INSERT INTO release_group VALUES "
    "(200,'rg-mt','Out of Step',110,3),"
    "(201,'rg-dis','Hear Nothing Say Nothing',111,1),"
    "(202,'rg-gauze','Equalizing Distort',112,1)",
    "INSERT INTO release_group_meta VALUES (200,1983),(201,1982),(202,1986)",
    f"INSERT INTO link_type VALUES (1,'{MEMBER_OF_BAND_GID}','member of band')",
    "INSERT INTO link VALUES (1,1),(2,1)",
    # entity0 = member person, entity1 = band. Both members in Minor Threat.
    "INSERT INTO l_artist_artist VALUES (1,1,20,10),(2,2,21,10)",
    "INSERT INTO link_attribute_type VALUES (1,'vocals')",
    "INSERT INTO link_attribute VALUES (1,1)",  # link 1 (Ian) -> vocals
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


@pytest.fixture()
def app_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, _record):
        # SQLite ignores FK constraints unless told otherwise.
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()
    yield db
    db.close()


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
