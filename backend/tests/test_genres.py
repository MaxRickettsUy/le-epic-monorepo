"""Step 1 of the sub-genre plan: curated vocabulary + Genre/BandGenre models."""

from app.genres import ALIAS_TO_SLUG, CURATED_GENRES, slug_for_tag
from app.models import Band, BandGenre, Genre


def test_alias_variants_collapse_to_one_slug():
    # Several MB tag spellings of NYHC map to the single curated slug.
    assert slug_for_tag("nyhc") == "nyhc"
    assert slug_for_tag("New York Hardcore") == "nyhc"
    assert slug_for_tag("  N.Y.H.C.  ") == "nyhc"


def test_non_curated_tag_is_ignored():
    assert slug_for_tag("shoegaze") is None
    assert slug_for_tag("") is None


def test_alias_map_is_consistent_with_curated_genres():
    # Every alias points back at a real slug, and slugs are unique.
    for alias, slug in ALIAS_TO_SLUG.items():
        assert slug in CURATED_GENRES, alias
    # No alias is claimed by two genres.
    all_aliases = [a for _name, aliases in CURATED_GENRES.values() for a in aliases]
    assert len(all_aliases) == len(set(all_aliases))


def test_band_genre_relationship_round_trips(db):
    band = Band(
        name="Mindset",
        status="active",
        location="Washington, D.C.",
        country="United States",
        label="React!",
    )
    genre = Genre(slug="youth-crew", name="Youth Crew")
    db.add_all([band, genre])
    db.flush()
    db.add(BandGenre(band=band, genre=genre, vote_count=3))
    db.commit()

    fetched = db.get(Band, band.id)
    assert len(fetched.genres) == 1
    link = fetched.genres[0]
    # Convenience properties read straight off the linked Genre.
    assert link.slug == "youth-crew"
    assert link.name == "Youth Crew"
    assert link.vote_count == 3


def test_vote_count_defaults_to_zero(db):
    band = Band(name="X", status="active", location="", country="US", label="")
    genre = Genre(slug="beatdown", name="Beatdown")
    db.add_all([band, genre])
    db.flush()
    db.add(BandGenre(band=band, genre=genre))
    db.commit()
    assert db.get(Band, band.id).genres[0].vote_count == 0


# --- Step 3: genres on the band API (list + detail) ------------------------


def _seed_band_with_genres(db, *links):
    """links: (slug, name, vote_count) tuples. Returns the band id."""
    band = Band(
        name="Bold", status="split-up", location="New York", country="US", label="Revelation"
    )
    db.add(band)
    db.flush()
    for slug, name, votes in links:
        genre = Genre(slug=slug, name=name)
        db.add(genre)
        db.flush()
        db.add(BandGenre(band=band, genre=genre, vote_count=votes))
    db.commit()
    return band.id


def test_detail_exposes_genres_ordered_by_votes(client, db):
    band_id = _seed_band_with_genres(db, ("nyhc", "NYHC", 2), ("youth-crew", "Youth Crew", 9))
    body = client.get(f"/band/{band_id}").json()
    # Strongest-voted genre first; only {slug, name} is exposed.
    assert body["genres"] == [
        {"slug": "youth-crew", "name": "Youth Crew"},
        {"slug": "nyhc", "name": "NYHC"},
    ]


def test_list_includes_genres(client, db):
    band_id = _seed_band_with_genres(db, ("nyhc", "NYHC", 1))
    item = next(b for b in client.get("/band/").json()["bands"] if b["id"] == band_id)
    assert item["genres"] == [{"slug": "nyhc", "name": "NYHC"}]


def test_band_without_genres_returns_empty_list(client):
    band_id = client.post(
        "/band/new",
        json={
            "name": "Minor Threat",
            "status": "split-up",
            "location": "Washington, D.C.",
            "country": "US",
            "label": "Dischord",
        },
    ).json()["id"]
    assert client.get(f"/band/{band_id}").json()["genres"] == []
    item = client.get("/band/").json()["bands"][0]
    assert item["genres"] == []
