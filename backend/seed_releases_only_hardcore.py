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
    # throttle to 1 request/sec (so lookup calls are rate-limited)
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
                # Browse releases (we only need release-group data here to check type)
                resp = musicbrainzngs.browse_releases(
                    artist=mbid,
                    includes=["release-groups"],  # fetch release-group type here
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
                rel_type     = (relgroup.get("type") or "").strip()

                # ─── 1) Lookup the full release to inspect tags (no "release-events" include) ───────
                try:
                    detailed = musicbrainzngs.get_release_by_id(
                        release_mbid,
                        includes=["tags", "release-groups"]  # "release-events" removed
                    )
                except musicbrainzngs.WebServiceError as e:
                    print(f"    ⚠️  Could not lookup release details for {title} ({release_mbid}): {e}")
                    time.sleep(1)
                    continue

                # 1a) Check if this release has the "hardcore punk" tag
                tag_list = detailed.get("release", {}).get("tag-list", [])
                tag_names = {t.get("name", "").lower() for t in tag_list}
                if "hardcore punk" not in tag_names:
                    print(f"  - Skipping (no 'hardcore punk' tag): {title} (type: {rel_type})")
                    continue

                # ─── 2) Extract year from release-event-list (first event). No extra include needed
                year = None
                event_list = detailed.get("release", {}).get("release-event-list", [])
                if event_list:
                    first_event = event_list[0]
                    date_str = first_event.get("date")  # e.g. "1995-07-21" or "1995"
                    if date_str:
                        year = date_str.split("-")[0]

                # ─── 3) Upsert logic ───────────────────────────────────────────────
                # 3a) Check by MBID
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

                # 3b) Fallback: Check by (name, band_id)
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
                        print(f"  - Skipping (title match, MBID and year already set): {title}")
                    continue

                # 3c) No existing row — create a new Release
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

                # Respect rate-limit before processing next tagged release
                time.sleep(1)

            # ─── 4) Pagination: if fewer than 100 releases, we’re done ──────────
            if len(releases) < 100:
                break

            offset += 100
            time.sleep(1)  # respect 1 req/sec

    print("\n✅ Release seeding complete.")
