#!/usr/bin/env python3
import os
import time
import json
import musicbrainzngs
from app import create_app
from app.models import Band

# ─── Setup Flask app context ───────────────────────────────────────────────────
app = create_app()

with app.app_context():
    print("Generating block list using release-group tags…")
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])

    # ─── Configure MusicBrainz client ───────────────────────────────────────────
    musicbrainzngs.set_useragent("HardchivesSeeder", "0.1", "you@example.com")
    musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    # ─── Ensure /app/data exists ─────────────────────────────────────────────────
    os.makedirs("data", exist_ok=True)
    path = "data/block_list.json"

    # ─── Load any existing entries so we can append instead of overwrite ─────────
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing_block_list = json.load(f)
            if not isinstance(existing_block_list, list):
                existing_block_list = []
    except (FileNotFoundError, json.JSONDecodeError):
        existing_block_list = []

    # ─── Prepare block list ───────────────────────────────────────────────────────
    new_block_list = []

    # ─── Fetch all bands that have an MBID ────────────────────────────────────────
    bands = Band.query.filter(Band.mbid.isnot(None)).all()
    print(f"Found {len(bands)} bands with MBIDs.\n")

    for band in bands:
        mbid = band.mbid
        print(f"Processing band: {band.name} (MBID: {mbid})")

        offset = 0
        has_punk_release = False

        while True:
            print(f"  → Browsing release-groups for offset={offset}")

            try:
                # Fetch up to 100 release-groups, including their tag-lists
                resp = musicbrainzngs.browse_release_groups(
                    artist=mbid,
                    includes=["tags"],
                    limit=100,
                    offset=offset
                )
            except musicbrainzngs.WebServiceError as e:
                print(f"  ⚠️  Error browsing release-groups for {band.name}: {e}")
                break

            rg_list = resp.get("release-group-list", [])
            print(f"    • Retrieved {len(rg_list)} release-groups")

            if not rg_list:
                print("    → No more release-groups, ending pagination")
                break

            for idx, rg in enumerate(rg_list, start=1):
                rg_mbid = rg.get("id")
                print(f"    • Checking release-group {idx}/{len(rg_list)}: {rg_mbid}")

                # Tags are already included in the browse response:
                tag_list = rg.get("tag-list", [])
                tag_names = {t.get("name", "").lower() for t in tag_list}
                if "hardcore punk" in tag_names:
                    print("      ✅ Found 'hardcore punk' tag on this release-group")
                    has_punk_release = True
                    break
                else:
                    print("      – No 'hardcore punk' tag on this release-group")

            if has_punk_release:
                print("    → Exiting loop: band has at least one hardcore-punk release-group")
                break

            # If fewer than 100 release-groups were returned, we've reached the end
            if len(rg_list) < 100:
                print("    → Fewer than 100 release-groups fetched, ending pagination")
                break

            offset += 100
            print("    → Moving to next page of release-groups\n")
            # Respect rate-limit before fetching the next page
            time.sleep(1)

        if not has_punk_release:
            print(f"  ⚠️ No hardcore-punk release-groups found → block {band.name}\n")
            new_block_list.append({
                "mbid": mbid,
                "name": band.name
            })
        else:
            print(f"  ✅ Found at least one hardcore-punk release-group → keep {band.name}\n")

    # ─── Merge new entries with existing, avoiding duplicates ─────────────────────
    existing_mbids = {entry["mbid"] for entry in existing_block_list if "mbid" in entry}
    merged_block_list = existing_block_list.copy()
    for entry in new_block_list:
        if entry["mbid"] not in existing_mbids:
            merged_block_list.append(entry)

    # ─── Write updated list back to JSON ─────────────────────────────────────────
    if merged_block_list:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(merged_block_list, f, indent=2, ensure_ascii=False)
            total = len(merged_block_list)
            added = len(merged_block_list) - len(existing_block_list)
            print(f"✅ Appended {added} new band(s); total blocked bands now: {total}")
        except IOError as e:
            print(f"❌ Failed to write {path}: {e}")
    else:
        print(f"✅ No bands to block; {path} remains unchanged.")

    print("\nDone.")
