#!/usr/bin/env python3
import time
import musicbrainzngs
from app import create_app, db
from app.models import Band
import logging

# ─── Setup Flask app context ───────────────────────────────────────────────────
app = create_app()

with app.app_context():
    print("Seeding into:", app.config['SQLALCHEMY_DATABASE_URI'])

    # Configure MusicBrainz client
    musicbrainzngs.set_useragent("Hardchives","0.1","mrucoding@mgmail.com")
    # throttle to 1 request/sec
    musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    # ─── Seeding parameters ─────────────────────────────────────────────────────
    tag_query = "tag:hardcore-punk"
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
                name    = a.get("name")
                country = a.get("country", "")
                # upsert by name

                band = Band.query.filter_by(name=name).first()

                print(f"Processing band: {name} (country: {country})")
                print(f"Existing band: {band}")

                if not band:
                    band = Band(
                        name=name,
                        status="",           # default/unknown
                        band_picture=None,
                        location="",
                        country=country,
                        label=""
                    )
                    print(f"Creating new band: {name}")
                    db.session.add(band)
                else:
                    band.country = country

            try:
                db.session.commit()
            except Exception as e:
                print("Commit failed:", e)
                db.session.rollback()
            # pagination break
            if len(artists) < 100:
                break
            offset += 100
            time.sleep(1)

    print("✅ Seeding complete.")
