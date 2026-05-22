#!/usr/bin/env python3
import time
import musicbrainzngs
from sqlalchemy.exc import IntegrityError
from app import create_app, db
from app.models import Band, Release

# ─── Setup Flask app context ───────────────────────────────────────────────────
app = create_app()

with app.app_context():
    print("Seeding releases into:", app.config['SQLALCHEMY_DATABASE_URI'])

    # Configure MusicBrainz client
    musicbrainzngs.set_useragent("HardchivesSeeder", "0.1", "mrucoding@mgmail.com")
    # throttle to 1 request/sec (so lookup calls are also rate-limited)
    musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    # ─── Fetch all bands that have an MBID ────────────────────────────────────────
    bands = Band.query.filter(Band.mbid.isnot(None)).all()
    print(f"Found {len(bands)} bands with MBIDs.")

    for band in bands:
        mbid = band.mbid
        print(f"\nProcessing releases for band: {band.name} (MBID: {mbid})")

        offset = 0
        while True:
            try:
                # Only include "release-groups" in the browse call
                resp = musicbrainzngs.browse_releases(
                    artist=mbid,
                    includes=["release-groups"],
                    limit=100,
                    offset=offset
                )
            except musicbrainzngs.WebServiceError as e:
                print(f"  ⚠️  MusicBrainz error browsing releases for {band.name}: {e}")
                break

            releases = resp.get("release-list", [])
            if not releases:
                print("  → No more releases found.")
                break

            for r in releases:
                release_mbid = r.get("id")
                title        = r.get("title")
                relgroup     = r.get("release-group", {})
                rel_type     = relgroup.get("type", "") or ""

                # ─── Fetch release-event-list via lookup (no includes needed) ───────────
                year = None
                try:
                    # Do NOT request "release-events" here—just call get_release_by_id()
                    detailed = musicbrainzngs.get_release_by_id(release_mbid)
                    event_list = detailed.get("release", {}).get("release-event-list", [])
                    if event_list:
                        first = event_list[0]
                        date_str = first.get("date")  # e.g. "1995-07-21" or "1995"
                        if date_str:
                            year = date_str.split("-")[0]
                except musicbrainzngs.WebServiceError as e:
                    # If lookup fails, proceed without a year
                    print(f"    ⚠️  Could not lookup events for {title} ({release_mbid}): {e}")

                # ─── 1) Check by MBID ────────────────────────────────────────────────
                existing = Release.query.filter_by(mbid=release_mbid).first()
                if existing:
                    updated = False

                    # Update release_type if changed
                    if existing.release_type != rel_type:
                        existing.release_type = rel_type
                        updated = True
                        print(f"  * Updated type for: {title} → {rel_type}")

                    # Update year if we fetched one and it's different
                    if year and existing.year != year:
                        existing.year = year
                        updated = True
                        print(f"  * Updated year for: {title} → {year}")

                    if updated:
                        try:
                            db.session.commit()
                        except IntegrityError:
                            db.session.rollback()
                            print(f"  ! Conflict updating existing release: {title}")
                    else:
                        print(f"  - Skipping (up-to-date MBID): {title}")
                    continue

                # ─── 2) Fallback: Check by (name, band_id) ───────────────────────────
                existing = Release.query.filter_by(name=title, band_id=band.id).first()
                if existing:
                    changed = False

                    # If MBID was missing, set it
                    if existing.mbid != release_mbid:
                        existing.mbid = release_mbid
                        changed = True
                        print(f"  * Set MBID for existing release: {title} → {release_mbid}")

                    # If year is available and differs, set it
                    if year and existing.year != year:
                        existing.year = year
                        changed = True
                        print(f"  * Set year for existing release: {title} → {year}")

                    if changed:
                        try:
                            db.session.commit()
                        except IntegrityError:
                            db.session.rollback()
                            print(f"  ! Conflict updating existing release: {title}")
                    else:
                        print(f"  - Skipping (release title match, MBID and year already set): {title}")
                    continue

                # ─── 3) No existing row — create a new Release ───────────────────────
                new_rel = Release(
                    mbid=release_mbid,
                    name=title,
                    length=None,
                    art=None,
                    release_type=rel_type,
                    year=year,
                    band_id=band.id
                )
                db.session.add(new_rel)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    print(f"  ! Skipped duplicate MBID insert: {title} ({release_mbid})")
                else:
                    print(f"  + Added release: {title} (MBID: {release_mbid}, type: {rel_type}, year: {year})")

            # ─── Pagination: if fewer than 100 releases, we’re done ─────────────────
            if len(releases) < 100:
                break

            offset += 100
            time.sleep(1)  # respect 1 req/sec

    print("\n✅ Release seeding complete.")
