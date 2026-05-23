"""Populate `album.art` from the Cover Art Archive.

Separate from the dump seed (the dump has no cover images). Reads albums that
have a release_group_mbid but no art yet, and asks the Cover Art Archive for a
front image at the release-group level. CAA redirects the `front` endpoint to
the actual image, so the stored URL is stable and browser-friendly.

Run after seeding:

    python -m seed.cover_art
"""

from __future__ import annotations

import logging
import urllib.error
import urllib.request
from collections.abc import Callable

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Album

logger = logging.getLogger("seed.cover_art")

CAA_BASE = "https://coverartarchive.org/release-group"
USER_AGENT = "Hardchives/0.1 (mrucoding@gmail.com)"


def cover_art_url(release_group_mbid: str) -> str:
    return f"{CAA_BASE}/{release_group_mbid}/front"


def _default_check(url: str) -> bool:
    """Return True if the Cover Art Archive has a front image (follows 307)."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 400
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        logger.warning("CAA error %s for %s", e.code, url)
        return False
    except urllib.error.URLError as e:
        logger.warning("CAA unreachable for %s: %s", url, e)
        return False


def fetch_cover_art(
    session,
    *,
    check: Callable[[str], bool] = _default_check,
    limit: int | None = None,
) -> dict:
    """Set `art` on albums that have a release-group MBID but no art yet."""
    query = (
        select(Album)
        .where(Album.release_group_mbid.isnot(None), Album.art.is_(None))
        .order_by(Album.id.asc())
    )
    if limit is not None:
        query = query.limit(limit)
    albums = session.scalars(query).all()

    stats = {"checked": 0, "set": 0, "missing": 0}
    for album in albums:
        stats["checked"] += 1
        url = cover_art_url(album.release_group_mbid)
        if check(url):
            album.art = url
            stats["set"] += 1
        else:
            stats["missing"] += 1
    session.commit()
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = SessionLocal()
    try:
        stats = fetch_cover_art(session)
        logger.info("Cover art complete: %s", stats)
    finally:
        session.close()


if __name__ == "__main__":
    main()
