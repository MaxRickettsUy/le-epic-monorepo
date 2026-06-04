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


def _create_with_mbid(client, db, mbid: str, **overrides) -> int:
    from app.models import Band

    band_id = _create(client, **overrides).json()["id"]
    band = db.get(Band, band_id)
    band.mbid = mbid
    db.commit()
    return band_id


def test_delete_blacklists_mbid_by_default(client, db):
    from app.models import BandBlacklist

    band_id = _create_with_mbid(client, db, "mt-gid")
    res = client.request("DELETE", f"/band/{band_id}/delete", params={"reason": "off-genre"})
    assert res.status_code == 200

    entry = db.get(BandBlacklist, "mt-gid")
    assert entry is not None
    assert entry.name == "Minor Threat"
    assert entry.reason == "off-genre"


def test_delete_blacklist_opt_out(client, db):
    from app.models import BandBlacklist

    band_id = _create_with_mbid(client, db, "mt-gid")
    res = client.request("DELETE", f"/band/{band_id}/delete?blacklist=false")
    assert res.status_code == 200
    assert db.get(BandBlacklist, "mt-gid") is None


def test_delete_band_without_mbid_does_not_blacklist(client, db):
    from app.models import BandBlacklist

    # Default BAND fixture has no mbid; nothing to blacklist by.
    band_id = _create(client).json()["id"]
    assert client.request("DELETE", f"/band/{band_id}/delete").status_code == 200
    assert db.query(BandBlacklist).count() == 0


def test_delete_appends_to_blacklist_json(client, db, tmp_path, monkeypatch):
    import json as _json

    import seed.blacklist as bl

    path = tmp_path / "blacklist.json"
    monkeypatch.setattr(bl, "BLACKLIST_PATH", path)

    band_id = _create_with_mbid(client, db, "mt-gid")
    res = client.request("DELETE", f"/band/{band_id}/delete", params={"reason": "off-genre"})
    assert res.status_code == 200
    assert _json.loads(path.read_text()) == [
        {"mbid": "mt-gid", "name": "Minor Threat", "reason": "off-genre"}
    ]


def test_redelete_without_reason_keeps_existing_reason(client, db, tmp_path, monkeypatch):
    """A re-delete without ?reason= must NOT strip the reason from the JSON or DB.

    Reproduces the bug where the second delete passed reason=None into
    `append_entry`, which rewrote the entry and dropped the reason key
    because None values are skipped on write.
    """
    import json as _json

    import seed.blacklist as bl

    path = tmp_path / "blacklist.json"
    monkeypatch.setattr(bl, "BLACKLIST_PATH", path)

    # First delete establishes the reason on both DB and JSON.
    band_id = _create_with_mbid(client, db, "mt-gid")
    client.request("DELETE", f"/band/{band_id}/delete", params={"reason": "off-genre"})

    # Simulate a re-seed bringing the same MBID back, then re-delete without reason.
    band_id2 = _create_with_mbid(client, db, "mt-gid")
    res = client.request("DELETE", f"/band/{band_id2}/delete")
    assert res.status_code == 200

    from app.models import BandBlacklist

    assert db.get(BandBlacklist, "mt-gid").reason == "off-genre"
    assert _json.loads(path.read_text()) == [
        {"mbid": "mt-gid", "name": "Minor Threat", "reason": "off-genre"}
    ]


def test_delete_blacklist_false_does_not_touch_json(client, db, tmp_path, monkeypatch):
    import seed.blacklist as bl

    path = tmp_path / "blacklist.json"
    monkeypatch.setattr(bl, "BLACKLIST_PATH", path)

    band_id = _create_with_mbid(client, db, "mt-gid")
    client.request("DELETE", f"/band/{band_id}/delete?blacklist=false")
    assert not path.exists()


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
    assert similar[other_id]["shared_genres"] == 0
    # shared member(5) + same label(2) + same country(1) = 8
    assert similar[other_id]["score"] == 8


def test_similar_counts_shared_genres(client, db):
    from app.models import BandGenre, Genre

    base_id = _create(client).json()["id"]
    # Only the country tie in common, plus two shared genres seeded below.
    other_id = _create(client, name="Black Flag", location="Hermosa Beach, CA", label="SST").json()[
        "id"
    ]

    nyhc = Genre(slug="nyhc", name="NYHC")
    yc = Genre(slug="youth-crew", name="Youth Crew")
    db.add_all([nyhc, yc])
    db.flush()
    db.add_all(
        [
            BandGenre(band_id=base_id, genre_id=nyhc.id),
            BandGenre(band_id=base_id, genre_id=yc.id),
            BandGenre(band_id=other_id, genre_id=nyhc.id),
            BandGenre(band_id=other_id, genre_id=yc.id),
        ]
    )
    db.commit()

    similar = {b["id"]: b for b in client.get(f"/band/{base_id}/similar").json()}
    assert similar[other_id]["shared_genres"] == 2
    # 2 shared genres(3 each) + same country(1) = 7
    assert similar[other_id]["score"] == 7


# -------- auto-flag / allowlist review flow --------


def _flag(db, band_id):
    """Mark a band as auto-flagged (simulates what seed.mb_dump does)."""
    from app.models import Band

    db.query(Band).filter(Band.id == band_id).update({"auto_flagged": True})
    db.commit()


def test_list_hides_auto_flagged_bands(client, db):
    keep = _create(client, name="Keep").json()["id"]
    flagged = _create(client, name="Flagged").json()["id"]
    _flag(db, flagged)

    names = [b["name"] for b in client.get("/band/").json()["bands"]]
    assert names == ["Keep"]
    # Detail still resolves so the review queue can deep-link.
    assert client.get(f"/band/{flagged}").status_code == 200


def test_countries_excludes_flagged(client, db):
    _create(client, name="Visible", country="United States")
    flagged = _create(client, name="Hidden", country="Sweden").json()["id"]
    _flag(db, flagged)

    countries = [r["country"] for r in client.get("/band/countries").json()]
    assert "United States" in countries
    assert "Sweden" not in countries


def test_similar_excludes_flagged(client, db):
    base = _create(client, name="Base").json()["id"]
    other = _create(client, name="Other").json()["id"]  # same country, would score
    flagged = _create(client, name="Flagged").json()["id"]
    _flag(db, flagged)

    ids = [b["id"] for b in client.get(f"/band/{base}/similar").json()]
    assert other in ids
    assert flagged not in ids


def test_needs_review_lists_only_unresolved_flagged(client, db):
    from datetime import UTC, datetime

    from app.models import Band

    a = _create(client, name="ToReview").json()["id"]
    b = _create(client, name="AlreadyAllowlisted").json()["id"]
    _create(client, name="Unflagged")
    _flag(db, a)
    _flag(db, b)
    db.query(Band).filter(Band.id == b).update(
        {"allowlisted_at": datetime.now(UTC), "auto_flagged": False}
    )
    db.commit()

    queue = client.get("/band/needs-review").json()
    assert [r["name"] for r in queue] == ["ToReview"]

    widened = client.get("/band/needs-review?include_resolved=true").json()
    assert {"ToReview", "AlreadyAllowlisted"}.issubset({r["name"] for r in widened})


def test_allowlist_endpoint_clears_flag_and_stamps(client, db):
    from app.models import Band

    band_id = _create(client).json()["id"]
    _flag(db, band_id)

    res = client.post(f"/band/{band_id}/allowlist")
    assert res.status_code == 200

    db.expire_all()
    band = db.get(Band, band_id)
    assert band.auto_flagged is False
    assert band.allowlisted_at is not None
    # Now visible to the public listing.
    assert [b["name"] for b in client.get("/band/").json()["bands"]] == ["Minor Threat"]


def test_allowlist_endpoint_404s_for_unknown(client):
    assert client.post("/band/999/allowlist").status_code == 404
