"""Enrich curated genre coverage with Last.fm tags.

The MB dump is a clean entity backbone but a thin genre signal for newer bands
(many popular 2010s acts are barely tagged on MB, or not tagged as hardcore at
all). This pass runs *after* `seed.mb_dump`: for each band MB has seeded with
an MBID, it asks Last.fm for top tags, funnels them through the same
`slug_for_tag` chokepoint the MB seed uses, and writes `BandGenre` rows tagged
`source="lastfm"`.

Run after `seed.mb_dump` (and any time afterward to backfill):

    python -m seed.lastfm_tags

Idempotent: keyed by `(band_id, genre_id)`. Re-running upserts vote counts and
does not duplicate links.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.genres import slug_for_tag
from app.models import Band, BandGenre, Genre
from app.services.lastfm import LastfmError, top_tags
from app.settings import settings
from seed.genre_allowlist import decide_auto_flag, load_allowlist

logger = logging.getLogger("seed.lastfm_tags")

# Last.fm weight floor. Below this, tags are noise (long tail of stray votes
# like one user tagging a hardcore band "metalcore"). Keep this in sync with
# plans/genre-enrichment.md.
WEIGHT_FLOOR = 10

# Last.fm allows ~5 req/s; throttle to a conservative pace.
DEFAULT_SLEEP_SECONDS = 0.25


@dataclass
class LastfmStats:
    bands_checked: int = 0
    bands_with_tags: int = 0
    links_inserted: int = 0
    links_updated: int = 0
    links_skipped_mb_owned: int = 0
    flags_cleared: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "bands_checked": self.bands_checked,
            "bands_with_tags": self.bands_with_tags,
            "links_inserted": self.links_inserted,
            "links_updated": self.links_updated,
            "links_skipped_mb_owned": self.links_skipped_mb_owned,
            "flags_cleared": self.flags_cleared,
            "errors": len(self.errors),
        }


def bucket_weight(weight: int) -> int:
    """Compress Last.fm's 0–100 weight onto MB's small-integer vote scale.

    MB vote counts are single digits in practice. Storing raw 100s would swamp
    the `order_by(desc(vote_count))` primary-genre sort. `round(weight / 20)`
    yields 0–5, sitting alongside MB magnitudes with one shared sort key.

    The floor (`WEIGHT_FLOOR`) is enforced upstream — by the time we bucket,
    any input has cleared it, so the minimum bucket value is 1.
    """
    return max(1, round(weight / 20))


def _mb_tag_pairs(band: Band) -> list[tuple[str, int]]:
    """Reconstruct the `(name, votes)` list mb_dump persisted on the band."""
    return [(t["name"], int(t.get("votes", 0))) for t in (band.mb_tags or [])]


def enrich_lastfm_tags(
    session: Session,
    *,
    fetch_top_tags: Callable[[str], list[tuple[str, int]]] | None = None,
    sleep_seconds: float = DEFAULT_SLEEP_SECONDS,
    limit: int | None = None,
) -> LastfmStats:
    """Enrich `BandGenre` with Last.fm tags. Returns a stats summary.

    `fetch_top_tags(mbid) -> [(name, weight)]` is injectable for tests. By
    default it calls `app.services.lastfm.top_tags`, which itself fans out to
    the configured `LASTFM_API_KEY`.
    """
    stats = LastfmStats()

    if fetch_top_tags is None:
        if not settings.lastfm_api_key:
            logger.warning("LASTFM_API_KEY unset; skipping Last.fm enrichment")
            return stats
        fetch_top_tags = top_tags

    allowlist = load_allowlist()

    query = (
        session.query(Band)
        .filter(Band.mbid.isnot(None))
        .order_by(Band.id.asc())
    )
    if limit is not None:
        query = query.limit(limit)
    bands = query.all()
    if not bands:
        return stats

    genres_by_slug = {g.slug: g for g in session.query(Genre)}
    band_ids = [b.id for b in bands]
    existing_links: dict[tuple[int, int], BandGenre] = {
        (bg.band_id, bg.genre_id): bg
        for bg in session.query(BandGenre).filter(BandGenre.band_id.in_(band_ids))
    }

    for band in bands:
        stats.bands_checked += 1
        try:
            raw = fetch_top_tags(band.mbid)
        except LastfmError as e:
            stats.errors.append(f"{band.mbid}: {e}")
            continue

        # Floor + curate. A Last.fm tag passes only when it both clears the
        # noise floor and maps onto a curated slug.
        curated: dict[int, int] = {}  # genre_id -> bucketed vote_count
        for name, weight in raw:
            if weight < WEIGHT_FLOOR:
                continue
            slug = slug_for_tag(name)
            if slug is None:
                continue
            genre = genres_by_slug.get(slug)
            if genre is None:
                # Genre table is missing the curated row — mb_dump seeds it,
                # so this only fires if enrichment is run on a virgin DB.
                continue
            v = bucket_weight(weight)
            # Multiple aliases of the same genre can both pass the floor; keep
            # the strongest.
            if v > curated.get(genre.id, 0):
                curated[genre.id] = v

        if curated:
            stats.bands_with_tags += 1

        wrote_any_enrichment = False
        for genre_id, votes in curated.items():
            link = existing_links.get((band.id, genre_id))
            if link is None:
                link = BandGenre(
                    band_id=band.id,
                    genre_id=genre_id,
                    vote_count=votes,
                    source="lastfm",
                )
                session.add(link)
                existing_links[(band.id, genre_id)] = link
                stats.links_inserted += 1
                wrote_any_enrichment = True
            elif link.source == "mb":
                # Don't flip provenance: an MB link is community-voted, keep it
                # as MB even if Last.fm corroborates. Bump vote_count only if
                # Last.fm's bucketed score actually exceeds it.
                if votes > link.vote_count:
                    link.vote_count = votes
                    stats.links_updated += 1
                else:
                    stats.links_skipped_mb_owned += 1
            else:  # already "lastfm" (re-run)
                if votes > link.vote_count:
                    link.vote_count = votes
                    stats.links_updated += 1
                wrote_any_enrichment = True

        # Re-flag in-pass. If this band gained an enrichment link, recompute
        # auto_flagged with has_enrichment_core=True so the off-genre verdict
        # clears immediately, not on the next mb_dump run. Skip allowlisted
        # bands — that verdict belongs to the human curator.
        if wrote_any_enrichment and band.allowlisted_at is None:
            new_flag = decide_auto_flag(
                _mb_tag_pairs(band),
                allowlist,
                seed_tag=settings.seed_tag,
                has_enrichment_core=True,
            )
            if band.auto_flagged and not new_flag:
                stats.flags_cleared += 1
            band.auto_flagged = new_flag

        if sleep_seconds:
            time.sleep(sleep_seconds)

    session.commit()
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = SessionLocal()
    try:
        stats = enrich_lastfm_tags(session)
        logger.info("Last.fm enrichment complete: %s", stats.as_dict())
    finally:
        session.close()


if __name__ == "__main__":
    main()
