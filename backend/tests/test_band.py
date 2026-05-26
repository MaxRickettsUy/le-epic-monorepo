BAND = {
    "name": "Minor Threat",
    "status": "split-up",
    "band_picture": None,
    "location": "Washington, D.C.",
    "country": "United States",
    "label": "Dischord",
}


def _create(client, **overrides):
    return client.post("/band/new", json={**BAND, **overrides})


def test_list_empty(client):
    res = client.get("/band/")
    assert res.status_code == 200
    assert res.json() == {"bands": [], "next": None, "prev": None}


def test_create_and_list(client):
    res = _create(client)
    assert res.status_code == 200
    assert res.json()["message"] == "Band created"

    listing = client.get("/band/").json()
    assert len(listing["bands"]) == 1
    assert listing["bands"][0]["name"] == "Minor Threat"


def test_detail_shape_matches_contract(client):
    band_id = _create(client).json()["id"]
    body = client.get(f"/band/{band_id}").json()
    # Frontend contract fields.
    assert body["members"] == []
    assert body["releases"] == []
    assert body["status"] == "split-up"


def test_detail_404(client):
    assert client.get("/band/999").status_code == 404


def test_pagination(client):
    for i in range(12):  # bands_per_page defaults to 10
        _create(client, name=f"Band {i:02d}")
    page1 = client.get("/band/?page=1").json()
    assert len(page1["bands"]) == 10
    assert page1["next"] == 2
    assert page1["prev"] is None
    page2 = client.get("/band/?page=2").json()
    assert len(page2["bands"]) == 2
    assert page2["prev"] == 1
    assert page2["next"] is None


def test_update_and_delete(client):
    band_id = _create(client).json()["id"]
    upd = client.post(f"/band/{band_id}/update", json={**BAND, "status": "active"})
    assert upd.status_code == 200
    assert client.get(f"/band/{band_id}").json()["status"] == "active"

    assert client.request("DELETE", f"/band/{band_id}/delete").status_code == 200
    assert client.get(f"/band/{band_id}").status_code == 404


def test_similar_404(client):
    assert client.get("/band/999/similar").status_code == 404


def test_similar_ranks_same_location_then_country(client):
    base_id = _create(client).json()["id"]  # D.C. / United States
    same_loc = _create(client, name="Bad Brains").json()["id"]  # same location
    same_country = _create(
        client, name="Black Flag", location="Hermosa Beach, CA"
    ).json()["id"]
    # Different country entirely — must be excluded.
    _create(client, name="Discharge", location="Stoke-on-Trent", country="United Kingdom")

    similar = client.get(f"/band/{base_id}/similar").json()
    ids = [b["id"] for b in similar]

    assert base_id not in ids  # self excluded
    assert ids == [same_loc, same_country]  # same location ranks first
    assert {"id", "name", "location", "country"} == set(similar[0].keys())
