"""MusicBrainz web-API access, isolated from the HTTP layer.

This is the web-API fill-in path. The bulk seed comes from the MB database dump
(resurrection plan, Phase 4); this module is for single-band lookups and search.
"""

import uuid

import musicbrainzngs

from app.settings import settings

musicbrainzngs.set_useragent("Hardchives", "0.1", settings.musicbrainz_contact_email)
musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

WebServiceError = musicbrainzngs.WebServiceError

# Tags we treat as "hardcore enough" for the genre-scoped catalogue.
HARDCORE_TAGS = {"hardcore-punk", "hardcore", "punk", "punk rock", "post-hardcore"}


def search_hardcore_artists(name: str, limit: int = 10) -> dict:
    """Search artists named `name`, scoped to the hardcore-punk tag."""
    return musicbrainzngs.search_artists(artist=name, tag="hardcore-punk", limit=limit)


def get_releases_by_artist_id(mbid: str) -> dict:
    """Browse the releases for the artist identified by `mbid`.

    Returns a dict with `isNotHardcore` (bool) and `releases` (list). Raises
    LookupError if `mbid` is not a valid MBID or no such artist exists.
    """
    try:
        uuid.UUID(mbid)
    except ValueError as e:
        raise LookupError("Invalid MusicBrainz ID") from e

    try:
        artist_info = musicbrainzngs.get_artist_by_id(mbid, includes=["tags"])
    except WebServiceError as e:
        if getattr(e.cause, "code", None) == 404:
            raise LookupError("No such artist") from e
        raise
    tags = [t["name"].lower() for t in artist_info["artist"].get("tag-list", [])]
    is_not_hardcore = not any(tag in HARDCORE_TAGS for tag in tags)

    releases_response = musicbrainzngs.browse_releases(
        artist=mbid, includes=["release-groups"], limit=100
    )
    return {
        "isNotHardcore": is_not_hardcore,
        "releases": releases_response.get("release-list", []),
    }
