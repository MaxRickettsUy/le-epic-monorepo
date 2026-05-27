from tests.test_band import _create


def _release(client, band_id, **overrides):
    payload = {"name": "Out of Step", "release_type": "Album", "year": 1983}
    return client.post(f"/release/new?band={band_id}", json={**payload, **overrides})


def test_search_empty_query_rejected(client):
    # min_length=1 on the query param.
    assert client.get("/search/?q=").status_code == 422
    assert client.get("/search/").status_code == 422


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
