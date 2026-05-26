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


def test_similar_no_matches_returns_empty(client):
    # A band with nothing in common with anyone scores 0 everywhere.
    base_id = _create(client).json()["id"]
    _create(
        client,
        name="Discharge",
        location="Stoke-on-Trent",
        country="United Kingdom",
        label="Clay",
    )
    assert client.get(f"/band/{base_id}/similar").json() == []


def test_similar_weights_and_factors(client):
    # Base: "Washington, D.C." / "United States" / "Dischord".
    base_id = _create(client).json()["id"]
    scene = _create(client, name="Bad Brains").json()["id"]  # loc+label+country
    label_only = _create(
        client, name="SOA", location="Arlington, VA", country="United States"
    ).json()["id"]  # label+country
    country_only = _create(
        client, name="Black Flag", location="Hermosa Beach, CA", label="SST"
    ).json()["id"]  # country only

    similar = {b["id"]: b for b in client.get(f"/band/{base_id}/similar").json()}
    ids = [b["id"] for b in client.get(f"/band/{base_id}/similar").json()]

    assert base_id not in similar  # self excluded
    # location(4)+label(2)+country(1)=7 > label(2)+country(1)=3 > country(1)=1
    assert ids == [scene, label_only, country_only]
    assert similar[scene]["score"] == 7
    assert similar[scene]["same_location"] is True
    assert similar[country_only]["score"] == 1
    assert similar[country_only]["same_label"] is False


def test_similar_counts_shared_members(client, db):
    from app.models import BandMember, Member

    base_id = _create(client).json()["id"]
    # Different location, but same label + country, plus a shared member below.
    other_id = _create(
        client,
        name="Fugazi",
        location="Arlington, VA",
        country="United States",
        label="Dischord",
    ).json()["id"]

    ian = Member(name="Ian MacKaye")
    db.add(ian)
    db.flush()
    db.add_all(
        [
            BandMember(band_id=base_id, member_id=ian.id, role="vocals"),
            BandMember(band_id=other_id, member_id=ian.id, role="guitar"),
        ]
    )
    db.commit()

    similar = {b["id"]: b for b in client.get(f"/band/{base_id}/similar").json()}
    assert similar[other_id]["shared_members"] == 1
    # shared member(5) + same label(2) + same country(1) = 8
    assert similar[other_id]["score"] == 8
