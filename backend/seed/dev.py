"""Seed a small set of dev data straight into the app DB.

Unlike `seed.mb_dump`, this needs no MusicBrainz Postgres — it inserts a
handful of hand-written hardcore-punk bands (with albums, tracks, and members)
so the app has something to render locally. Idempotent by band name: re-running
skips bands that already exist.

    python -m seed.dev
"""

from __future__ import annotations

import logging

from app.database import SessionLocal
from app.models import Album, Band, BandMember, Member, Track

logger = logging.getLogger("seed.dev")

# name, status, location, country, label, [ (album, year, type, [tracks]) ], [ (member, role) ]
BANDS = [
    {
        "name": "Minor Threat",
        "status": "split-up",
        "location": "Washington, D.C.",
        "country": "United States",
        "label": "Dischord Records",
        "albums": [
            ("Out of Step", 1983, "lp", ["Betray", "It Follows", "Out of Step", "Sob Story"]),
            ("Minor Threat", 1981, "ep", ["Filler", "I Don't Wanna Hear It", "Seeing Red"]),
        ],
        "members": [
            ("Ian MacKaye", "vocals"),
            ("Lyle Preslar", "guitar"),
            ("Brian Baker", "bass"),
            ("Jeff Nelson", "drums"),
        ],
    },
    {
        "name": "Black Flag",
        "status": "split-up",
        "location": "Hermosa Beach, California",
        "country": "United States",
        "label": "SST Records",
        "albums": [
            ("Damaged", 1981, "lp", ["Rise Above", "Six Pack", "TV Party", "Damaged I"]),
            ("My War", 1984, "lp", ["My War", "Can't Decide", "Beat My Head Against the Wall"]),
        ],
        "members": [
            ("Henry Rollins", "vocals"),
            ("Greg Ginn", "guitar"),
            ("Chuck Dukowski", "bass"),
        ],
    },
    {
        "name": "Bad Brains",
        "status": "active",
        "location": "Washington, D.C.",
        "country": "United States",
        "label": "ROIR",
        "albums": [
            ("Bad Brains", 1982, "lp", ["Sailin' On", "Attitude", "Banned in D.C.", "Pay to Cum"]),
            ("I Against I", 1986, "lp", ["Intro", "I Against I", "House of Suffering"]),
        ],
        "members": [
            ("H.R.", "vocals"),
            ("Dr. Know", "guitar"),
            ("Darryl Jenifer", "bass"),
            ("Earl Hudson", "drums"),
        ],
    },
    {
        "name": "Gorilla Biscuits",
        "status": "on-hold",
        "location": "New York City",
        "country": "United States",
        "label": "Revelation Records",
        "albums": [
            ("Start Today", 1989, "lp", ["New Direction", "Hold Your Ground", "Start Today"]),
            ("Gorilla Biscuits", 1988, "ep", ["High Hopes", "Big Mouth", "No Reason Why"]),
        ],
        "members": [
            ("Civ", "vocals"),
            ("Walter Schreifels", "guitar"),
        ],
    },
    {
        "name": "Discharge",
        "status": "active",
        "location": "Stoke-on-Trent",
        "country": "United Kingdom",
        "label": "Clay Records",
        "albums": [
            (
                "Hear Nothing See Nothing Say Nothing",
                1982,
                "lp",
                ["Hear Nothing See Nothing Say Nothing", "The Possibility of Life's Destruction"],
            ),
        ],
        "members": [
            ("Cal", "vocals"),
            ("Bones", "guitar"),
        ],
    },
]


def run_seed(session) -> dict:
    existing = {name for (name,) in session.query(Band.name).all()}
    members_by_name: dict[str, Member] = {m.name: m for m in session.query(Member).all()}
    stats = {"bands": 0, "albums": 0, "tracks": 0, "members": 0, "skipped": 0}

    for spec in BANDS:
        if spec["name"] in existing:
            stats["skipped"] += 1
            continue

        band = Band(
            name=spec["name"],
            status=spec["status"],
            location=spec["location"],
            country=spec["country"],
            label=spec["label"],
        )
        session.add(band)
        stats["bands"] += 1

        for album_name, year, rtype, track_names in spec["albums"]:
            album = Album(name=album_name, year=year, release_type=rtype, band=band)
            session.add(album)
            stats["albums"] += 1
            for i, track_name in enumerate(track_names, start=1):
                session.add(
                    Track(name=track_name, track_number=i, position=i, release=album)
                )
                stats["tracks"] += 1

        for member_name, role in spec["members"]:
            member = members_by_name.get(member_name)
            if member is None:
                member = Member(name=member_name)
                session.add(member)
                session.flush()
                members_by_name[member_name] = member
                stats["members"] += 1
            session.add(BandMember(band=band, member=member, role=role))

    session.commit()
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = SessionLocal()
    try:
        stats = run_seed(session)
        logger.info("Dev seed complete: %s", stats)
    finally:
        session.close()


if __name__ == "__main__":
    main()
