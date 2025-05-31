#!/usr/bin/env python3
import time
import musicbrainzngs
from app import create_app, db
from app.models import Band
import logging

max_bands = 10
added_count = 0

# ─── Setup Flask app context ───────────────────────────────────────────────────
app = create_app()

with app.app_context():
    print("Seeding into:", app.config['SQLALCHEMY_DATABASE_URI'])

    # Configure MusicBrainz client
    musicbrainzngs.set_useragent("Hardchives","0.1","mrucoding@mgmail.com")
    # throttle to 1 request/sec
    musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    IGNORE_BAND_MBIDS = {
        "8dcd04e4-7695-4d80-bae9-1d7d680a38ef" , # 'Captain Beefheart & His Magic Band'
        "1501f6bb-07c6-4555-95d7-e83eef2e7f56",  # 'Frenchy and the Punk'
        "46e63d3b-d91b-4791-bb73-e9f638a45ea0", # 'Joan Jett & The Blackhearts'
        "b10db9ad-b4c3-47f3-a7a4-37864b134f65", # 'Soul Asylum'
        "1253e5e9-eaa7-4ce6-81b8-09725e8cee43", # 'Iggy and the Stooges'
    }

    # ─── Seeding parameters ─────────────────────────────────────────────────────
    tag_query = "tag:*punk*"
    prefixes  = list("a")
    # prefixes  = list("abcdefghijklmnopqrstuvwxyz")

    # ─── Seed loop ────────────────────────────────────────────────────────────────
    for prefix in prefixes:
        offset = 0
        while True:
            lucene = f'{tag_query} AND artist:{prefix}* AND country:us'
            print(f"Searching: {lucene} (offset={offset})")

            resp = musicbrainzngs.search_artists(
                query=lucene,
                limit=100,
                offset=offset
            )
            # print(f"Found {resp.get('artist-count', 0)} artists.")
            # print(f"Artists: {resp.get('artist-list', [])}")

            artists = resp.get("artist-list", [])

            if not artists:
                break

            for a in artists:
                if added_count >= max_bands:
                    break
                mbid = a.get("id")
                name    = a.get("name")
                country = a.get("country", "")

                # if mbid in IGNORE_BAND_MBIDS: continue
                if mbid in IGNORE_BAND_MBIDS:
                    print(f"  - Ignoring band (on ignore list): {name} ({mbid})")
                    continue

                # upsert by mbid
                band = Band.query.filter_by(mbid=mbid).first()

                print(f"Processing band: {name} (country: {country})")
                print(f"Existing band: {band}")

                if not band:
                    band = Band(
                        mbid=mbid,
                        name=name,
                        status="",           # default/unknown
                        band_picture=None,
                        location="",
                        country=country,
                        label=""
                    )
                    print(f"Creating new band: {name}")
                    db.session.add(band)
                    added_count += 1
                else:
                    band.country = country

            try:
                db.session.commit()
            except Exception as e:
                print("Commit failed:", e)
                db.session.rollback()
            if added_count >= max_bands:
                break
            # pagination break
            if len(artists) < 100:
                break
            offset += 100
            time.sleep(1)

    print("✅ Seeding complete.")
