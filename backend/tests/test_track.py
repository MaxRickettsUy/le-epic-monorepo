from tests.test_band import BAND
from tests.test_release import RELEASE


def _release(client):
    band_id = client.post("/band/new", json=BAND).json()["id"]
    return client.post(f"/release/new?band={band_id}", json=RELEASE).json()["id"]


TRACK = {"name": "Betray", "track_number": 5, "length": 188, "lyrics": None}


def test_create_track_and_nest_under_release(client):
    rel_id = _release(client)
    res = client.post(f"/track/new?release={rel_id}", json=TRACK)
    assert res.status_code == 200

    tracks = client.get(f"/release/{rel_id}").json()["tracks"]
    assert len(tracks) == 1
    assert tracks[0]["name"] == "Betray"
    assert tracks[0]["track_number"] == 5


def test_create_track_unknown_release_404(client):
    assert client.post("/track/new?release=999", json=TRACK).status_code == 404


def test_deleting_release_cascades_tracks(client):
    rel_id = _release(client)
    track_id = client.post(f"/track/new?release={rel_id}", json=TRACK).json()["id"]
    client.request("DELETE", f"/release/{rel_id}/delete")
    assert client.get(f"/track/{track_id}").status_code == 404
