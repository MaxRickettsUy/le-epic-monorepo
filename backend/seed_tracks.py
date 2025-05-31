#!/usr/bin/env python3
import time
import musicbrainzngs
from sqlalchemy.exc import IntegrityError
from app import create_app, db
from app.models import Release, Track

# ─── Setup Flask app context ───────────────────────────────────────────────────
app = create_app()

with app.app_context():
    print("Seeding tracks into:", app.config['SQLALCHEMY_DATABASE_URI'])

    # Configure MusicBrainz client
    musicbrainzngs.set_useragent("HardchivesTrackSeeder", "0.1", "mrucoding@mgmail.com")
    # throttle to 1 request/sec
    musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    # ─── Fetch all Release rows that have an MBID ────────────────────────────────
    releases = Release.query.filter(Release.mbid.isnot(None)).all()
    print(f"Found {len(releases)} releases with MBIDs to process.")

    for release in releases:
        rel_mbid = release.mbid
        rel_name = release.name
        print(f"\nProcessing tracks for release: {rel_name} (MBID: {rel_mbid})")

        try:
            # Fetch full release info, including track listings
            detailed = musicbrainzngs.get_release_by_id(
                rel_mbid,
                includes=["recordings"]
            )
        except musicbrainzngs.WebServiceError as e:
            print(f"  ⚠️  Could not lookup release {rel_name} ({rel_mbid}): {e}")
            time.sleep(1)
            continue

        # The "medium-list" contains discs/mediums; each has a "track-list"
        medium_list = detailed.get("release", {}).get("medium-list", [])
        if not medium_list:
            print(f"  → No media/track-list found for {rel_name}.")
            time.sleep(1)
            continue

        for medium in medium_list:
            # Each medium represents a disc/side; "position" is disc number (as str, e.g. "1")
            disc_number_str = medium.get("position")
            try:
                disc_number = int(disc_number_str)
            except (TypeError, ValueError):
                disc_number = None

            track_list = medium.get("track-list", [])

            for track_info in track_list:
                # Each track_info dict has "position" and a nested "recording" dict
                track_num_str = track_info.get("position") or ""
                try:
                    track_number = int(track_num_str)
                except (TypeError, ValueError):
                    track_number = None

                recording = track_info.get("recording", {})
                recording_id = recording.get("id")
                track_title  = recording.get("title")
                track_length = recording.get("length")  # in milliseconds

                # Skip if no recording MBID
                if not recording_id:
                    print(f"    • Skipping track without recording MBID: '{track_title}'")
                    continue

                # Check for existing Track row by (mbid + release_id)
                existing_track = Track.query.filter_by(
                    mbid=recording_id,
                    release_id=release.id
                ).first()

                if existing_track:
                    # Optionally update name, length, track_number if changed
                    updated = False
                    if existing_track.name != track_title:
                        existing_track.name = track_title
                        updated = True
                    if track_length and existing_track.length != track_length:
                        existing_track.length = track_length
                        updated = True
                    if track_number is not None and existing_track.track_number != track_number:
                        existing_track.track_number = track_number
                        updated = True

                    if updated:
                        try:
                            db.session.commit()
                            print(f"    * Updated track: {track_number}. {track_title} (MBID: {recording_id})")
                        except IntegrityError:
                            db.session.rollback()
                            print(f"    ! Conflict updating track: {track_title} ({recording_id})")
                    else:
                        print(f"    - Skipping (track up-to-date): {track_number}. {track_title}")
                    continue

                # If no existing track, create a new one
                new_track = Track(
                    mbid=recording_id,
                    name=track_title,
                    length=track_length,
                    track_number=track_number,
                    release_id=release.id
                )
                db.session.add(new_track)
                try:
                    db.session.commit()
                    print(f"    + Added track: {track_number}. {track_title} (MBID: {recording_id})")
                except IntegrityError:
                    db.session.rollback()
                    print(f"    ! Skipped duplicate track insert: {track_title} ({recording_id})")

        # Respect MusicBrainz rate-limiting
        time.sleep(1)

    print("\n✅ Track seeding complete.")
