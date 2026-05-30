from app.settings import settings
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


# --- listing (`GET /release/`) ---------------------------------------------


def test_release_list_recent_orders_newest_first_and_includes_band(client):
    band_id = _band(client)
    older = client.post(f"/release/new?band={band_id}", json={**RELEASE, "name": "Older"}).json()[
        "id"
    ]
    newer = client.post(f"/release/new?band={band_id}", json={**RELEASE, "name": "Newer"}).json()[
        "id"
    ]

    body = client.get("/release/?sort=recent").json()
    ids = [r["id"] for r in body["releases"]]
    assert ids == [newer, older]
    # Each item carries the band identity for linking, not the nested band.
    item = body["releases"][0]
    assert item["band_id"] == band_id
    assert item["band_name"] == "Minor Threat"
    assert item["name"] == "Newer"
    assert body["next"] is None
    assert body["prev"] is None


def test_release_list_pagination(client):
    band_id = _band(client)
    per_page = settings.releases_per_page
    total = per_page + 2
    for i in range(total):
        client.post(f"/release/new?band={band_id}", json={**RELEASE, "name": f"R{i:02d}"})

    p1 = client.get("/release/?page=1").json()
    assert len(p1["releases"]) == per_page
    assert p1["next"] == (2 if total > per_page else None)
    assert p1["prev"] is None

    p2 = client.get("/release/?page=2").json()
    assert len(p2["releases"]) == total - per_page
    assert p2["next"] is None
    assert p2["prev"] == 1


def test_release_list_sort_by_year_desc_nulls_last(client):
    band_id = _band(client)
    client.post(f"/release/new?band={band_id}", json={**RELEASE, "name": "Yless", "year": None})
    client.post(f"/release/new?band={band_id}", json={**RELEASE, "name": "Y1990", "year": 1990})
    client.post(f"/release/new?band={band_id}", json={**RELEASE, "name": "Y2000", "year": 2000})

    body = client.get("/release/?sort=year").json()
    assert [r["name"] for r in body["releases"]] == ["Y2000", "Y1990", "Yless"]


def test_release_list_empty_catalogue(client):
    body = client.get("/release/").json()
    assert body == {"releases": [], "next": None, "prev": None}
