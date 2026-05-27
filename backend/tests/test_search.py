from app.models import Band, BandGenre, Genre
from tests.test_band import _create


def _release(client, band_id, **overrides):
    payload = {"name": "Out of Step", "release_type": "Album", "year": 1983}
    return client.post(f"/release/new?band={band_id}", json={**payload, **overrides})


def test_search_empty_query_rejected(client):
    # min_length=1 on the query param.
    assert client.get("/search/?q=").status_code == 422
    assert client.get("/search/").status_code == 422
    # Whitespace-only survives min_length but is blank after trimming.
    assert client.get("/search/?q=%20%20").status_code == 422


def test_search_matches_band_by_name(client):
    _create(client, name="Minor Threat")
    _create(client, name="Black Flag")

    body = client.get("/search/?q=minor").json()
    assert [b["name"] for b in body["bands"]] == ["Minor Threat"]
    assert body["albums"] == []
    assert body["query"] == "minor"


def test_search_is_case_insensitive_and_substring(client):
    _create(client, name="Bad Brains")
    body = client.get("/search/?q=BRAIN").json()
    assert [b["name"] for b in body["bands"]] == ["Bad Brains"]


def test_search_matches_album_and_carries_band(client):
    band_id = _create(client, name="Minor Threat").json()["id"]
    _release(client, band_id, name="Out of Step")

    body = client.get("/search/?q=out of step").json()
    assert body["bands"] == []
    assert len(body["albums"]) == 1
    album = body["albums"][0]
    assert album["name"] == "Out of Step"
    assert album["band_id"] == band_id
    assert album["band_name"] == "Minor Threat"
    assert album["year"] == 1983


def test_search_returns_both_types(client):
    band_id = _create(client, name="Step Forward").json()["id"]
    _release(client, band_id, name="One Step Beyond")

    body = client.get("/search/?q=step").json()
    assert [b["name"] for b in body["bands"]] == ["Step Forward"]
    assert [a["name"] for a in body["albums"]] == ["One Step Beyond"]


def test_search_matches_band_by_location(client):
    _create(client, name="Bad Seed", location="Wilkes-Barre, Pennsylvania")
    _create(client, name="Black Flag", location="Hermosa Beach, California")

    body = client.get("/search/?q=pennsylvania").json()
    assert [b["name"] for b in body["bands"]] == ["Bad Seed"]


def test_search_no_match_is_empty(client):
    _create(client, name="Minor Threat")
    body = client.get("/search/?q=zzzznope").json()
    assert body["bands"] == []
    assert body["albums"] == []


def test_search_wildcards_are_literal(client):
    _create(client, name="Minor Threat")
    # A bare "%" must not match everything.
    body = client.get("/search/?q=%").json()
    assert body["bands"] == []


def test_search_band_rows_carry_genres_ordered_by_votes(client, db):
    band_id = _create(client, name="Bold").json()["id"]
    band = db.get(Band, band_id)
    nyhc = Genre(slug="nyhc", name="NYHC")
    yc = Genre(slug="youth-crew", name="Youth Crew")
    db.add_all([nyhc, yc])
    db.flush()
    db.add_all(
        [
            BandGenre(band=band, genre=nyhc, vote_count=2),
            BandGenre(band=band, genre=yc, vote_count=9),
        ]
    )
    db.commit()

    row = client.get("/search/?q=bold").json()["bands"][0]
    assert row["genres"] == [
        {"slug": "youth-crew", "name": "Youth Crew"},
        {"slug": "nyhc", "name": "NYHC"},
    ]


def test_search_band_rows_default_to_empty_genres(client):
    _create(client, name="Minor Threat")
    assert client.get("/search/?q=minor").json()["bands"][0]["genres"] == []


def _tag_band(db, band_id, slug, name):
    band = db.get(Band, band_id)
    genre = db.query(Genre).filter_by(slug=slug).one_or_none() or Genre(slug=slug, name=name)
    db.add(genre)
    db.flush()
    db.add(BandGenre(band=band, genre=genre))
    db.commit()


def test_search_genre_facet_restricts_band_results(client, db):
    yc_id = _create(client, name="Bold").json()["id"]
    bd_id = _create(client, name="Bulldoze").json()["id"]
    _tag_band(db, yc_id, "youth-crew", "Youth Crew")
    _tag_band(db, bd_id, "beatdown", "Beatdown")

    # Both bands match the text query "b"; the facet keeps only the youth-crew one.
    facet = client.get("/search/?q=b&genre=youth-crew").json()
    assert [b["name"] for b in facet["bands"]] == ["Bold"]

    # Unknown slug matches nothing.
    assert client.get("/search/?q=b&genre=nope").json()["bands"] == []


def test_search_matches_band_by_genre_name(client, db):
    band_id = _create(client, name="Bold").json()["id"]
    _tag_band(db, band_id, "youth-crew", "Youth Crew")
    # "youth" hits neither name nor location, only the genre name.
    assert [b["name"] for b in client.get("/search/?q=youth").json()["bands"]] == ["Bold"]
