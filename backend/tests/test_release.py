from tests.test_band import BAND


def _band(client):
    return client.post("/band/new", json=BAND).json()["id"]


RELEASE = {
    "name": "Out of Step",
    "release_type": "Album",
    "label": "Dischord",
    "year": 1983,
    "length": 1110,
    "art": None,
}


def test_create_release_and_nest_under_band(client):
    band_id = _band(client)
    res = client.post(f"/release/new?band={band_id}", json=RELEASE)
    assert res.status_code == 200

    band = client.get(f"/band/{band_id}").json()
    assert len(band["releases"]) == 1
    rel = band["releases"][0]
    # Contract fields, including reviews-out-of-MVP defaults and type alias.
    assert rel["avg_review"] == 0
    assert rel["review_count"] == 0
    assert rel["type"] == rel["release_type"] == "Album"
    assert rel["year"] == 1983


def test_release_detail_nests_band_and_tracks(client):
    band_id = _band(client)
    rel_id = client.post(f"/release/new?band={band_id}", json=RELEASE).json()["id"]
    body = client.get(f"/release/{rel_id}").json()
    assert body["band"]["name"] == "Minor Threat"
    assert body["band_id"] == band_id
    assert body["tracks"] == []


def test_create_release_unknown_band_404(client):
    assert client.post("/release/new?band=999", json=RELEASE).status_code == 404


def test_delete_release(client):
    band_id = _band(client)
    rel_id = client.post(f"/release/new?band={band_id}", json=RELEASE).json()["id"]
    assert client.request("DELETE", f"/release/{rel_id}/delete").status_code == 200
    assert client.get(f"/release/{rel_id}").status_code == 404


def test_deleting_band_cascades_releases(client):
    band_id = _band(client)
    rel_id = client.post(f"/release/new?band={band_id}", json=RELEASE).json()["id"]
    client.request("DELETE", f"/band/{band_id}/delete")
    assert client.get(f"/release/{rel_id}").status_code == 404
