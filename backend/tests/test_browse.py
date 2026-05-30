"""Browse facets on GET /band/ (genre / country / letter), plus the
GET /genre/ vocabulary and GET /band/countries facet endpoints."""

from app.genres import CURATED_GENRES
from app.models import Band, BandGenre, Genre
from tests.test_band import _create


def _tag_band(db, band_id, slug, name):
    band = db.get(Band, band_id)
    genre = db.query(Genre).filter_by(slug=slug).one_or_none() or Genre(slug=slug, name=name)
    db.add(genre)
    db.flush()
    db.add(BandGenre(band=band, genre=genre))
    db.commit()


# --- genre facet -----------------------------------------------------------


def test_genre_facet_restricts_listing(client, db):
    bold = _create(client, name="Bold").json()["id"]
    _create(client, name="Bulldoze")
    _tag_band(db, bold, "youth-crew", "Youth Crew")

    body = client.get("/band/?genre=youth-crew").json()
    assert [b["name"] for b in body["bands"]] == ["Bold"]


def test_unknown_genre_slug_is_empty(client):
    _create(client, name="Bold")
    assert client.get("/band/?genre=nope").json()["bands"] == []


# --- country facet ---------------------------------------------------------


def test_country_facet_exact_match(client):
    _create(client, name="Bold", country="United States")
    _create(client, name="Discharge", country="United Kingdom")

    body = client.get("/band/?country=United Kingdom").json()
    assert [b["name"] for b in body["bands"]] == ["Discharge"]


# --- letter facet ----------------------------------------------------------


def test_letter_facet_prefix(client):
    _create(client, name="Bold")
    _create(client, name="Agnostic Front")
    _create(client, name="Bad Brains")

    names = [b["name"] for b in client.get("/band/?letter=B").json()["bands"]]
    assert names == ["Bad Brains", "Bold"]  # name-sorted, both start with B


def test_letter_facet_hash_matches_non_alpha(client):
    _create(client, name="7 Seconds")
    _create(client, name="Bold")

    names = [b["name"] for b in client.get("/band/?letter=%23").json()["bands"]]
    assert names == ["7 Seconds"]


def test_letter_facet_rejects_digit(client):
    assert client.get("/band/?letter=1").status_code == 422


# --- facets respect pagination total ---------------------------------------


def test_filtered_total_drives_next(client):
    # 12 B-bands (over one page of 10) and 1 A-band. The B facet must paginate
    # over 12, not the catalogue of 13.
    for i in range(12):
        _create(client, name=f"B{i:02d}")
    _create(client, name="Agnostic Front")

    page1 = client.get("/band/?letter=B&page=1").json()
    assert len(page1["bands"]) == 10
    assert page1["next"] == 2
    page2 = client.get("/band/?letter=B&page=2").json()
    assert len(page2["bands"]) == 2
    assert page2["next"] is None


def test_combined_facets(client, db):
    bold = _create(client, name="Bold", country="United States").json()["id"]
    _create(client, name="Bulldoze", country="United States")
    _create(client, name="Bane", country="United States")
    _tag_band(db, bold, "youth-crew", "Youth Crew")

    body = client.get("/band/?country=United States&genre=youth-crew&letter=B").json()
    assert [b["name"] for b in body["bands"]] == ["Bold"]


# --- /genre/ vocabulary ----------------------------------------------------


def test_genre_list_returns_full_vocabulary_sorted(client):
    body = client.get("/genre/").json()
    assert len(body) == len(CURATED_GENRES)
    names = [g["name"] for g in body]
    assert names == sorted(names, key=str.lower)
    # Shape is {slug, name} and slugs are the curated keys.
    assert {g["slug"] for g in body} == set(CURATED_GENRES)


# --- /band/countries -------------------------------------------------------


def test_countries_facet_counts_and_orders(client):
    _create(client, name="Bold", country="United States")
    _create(client, name="Bane", country="United States")
    _create(client, name="Discharge", country="United Kingdom")

    body = client.get("/band/countries").json()
    assert body == [
        {"country": "United States", "count": 2},
        {"country": "United Kingdom", "count": 1},
    ]


def test_countries_empty(client):
    assert client.get("/band/countries").json() == []
