#!/usr/bin/env python3
import time
import json
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

    # ─── 1) Load the block list JSON and extract MBIDs ──────────────────────────
    try:
        with open("data/block_list.json", "r", encoding="utf-8") as f:
            raw_block = json.load(f)
            # raw_block is a list of {"mbid": "...", "name": "..."}
            IGNORE_BAND_MBIDS = { entry["mbid"] for entry in raw_block }
            print(f"Loaded {len(IGNORE_BAND_MBIDS)} MBIDs from block_list.json")
    except FileNotFoundError:
        IGNORE_BAND_MBIDS = set()
        print("block_list.json not found → IGNORE_BAND_MBIDS is empty")
    except (ValueError, KeyError) as e:
        IGNORE_BAND_MBIDS = set()
        print(f"Error parsing block_list.json ({e}) → IGNORE_BAND_MBIDS is empty")

    # ─── 2) Configure MusicBrainz client ────────────────────────────────────────
    musicbrainzngs.set_useragent("Hardchives","0.1","mrucoding@mgmail.com")
    musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    # ─── 3) Seeding parameters ─────────────────────────────────────────────────
    tag_query = "tag:*punk*"
    prefixes  = list("a")   # or list("abcdefghijklmnopqrstuvwxyz")

    # ─── 4) Seed loop ──────────────────────────────────────────────────────────
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
            artists = resp.get("artist-list", [])
            if not artists:
                break

            for a in artists:
                if added_count >= max_bands:
                    break

                mbid    = a.get("id")
                name    = a.get("name")
                country = a.get("country", "")

                # ── Skip if this MBID is in the block list ───────────────────────
                if mbid in IGNORE_BAND_MBIDS:
                    print(f"  - Ignoring band (blocked): {name} ({mbid})")
                    continue

                # ── Upsert by MBID ───────────────────────────────────────────────
                band = Band.query.filter_by(mbid=mbid).first()
                print(f"Processing band: {name} (country: {country})  Existing: {band}")

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
                    print(f"  + Creating new band: {name}")
                    db.session.add(band)
                    added_count += 1
                else:
                    # Update country if it changed
                    band.country = country

            try:
                db.session.commit()
            except Exception as e:
                print("Commit failed:", e)
                db.session.rollback()

            if added_count >= max_bands:
                break

            # ── Pagination break ────────────────────────────────────────────────
            if len(artists) < 100:
                break
            offset += 100
            time.sleep(1)

    print("✅ Seeding complete.")
