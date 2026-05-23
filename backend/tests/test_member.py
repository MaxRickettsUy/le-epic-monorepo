from app.models import Band, BandMember, Member
from tests.conftest import TestingSessionLocal
from tests.test_band import BAND


def test_band_members_surface_in_detail(client):
    band_id = client.post("/band/new", json=BAND).json()["id"]

    # No member write endpoint yet (members come from the Phase 4 seed), so
    # insert membership directly and confirm the {name, role} shape surfaces.
    with TestingSessionLocal() as db:
        band = db.get(Band, band_id)
        ian = Member(name="Ian MacKaye")
        band.members.append(BandMember(member=ian, role="vocals"))
        db.add(band)
        db.commit()

    body = client.get(f"/band/{band_id}").json()
    assert body["members"] == [{"name": "Ian MacKaye", "role": "vocals"}]


def test_band_members_default_empty(client):
    band_id = client.post("/band/new", json=BAND).json()["id"]
    assert client.get(f"/band/{band_id}").json()["members"] == []
