"""Seed the app DB from a MusicBrainz database dump.

Replaces the five legacy web-API seed scripts + blocklist. Instead of paying
the 1 req/sec web API and filtering false positives after the fact, this runs a
handful of SQL queries against a local MusicBrainz Postgres
(metabrainz/musicbrainz-docker) and bulk-upserts into the app DB by MBID.

Scope: every artist tagged with `settings.seed_tag` ("hardcore punk"),
globally (no country filter).

Run once the MB Postgres is up:

    python -m seed.mb_dump

The SQL uses only portable constructs so the same queries run against the
minimal fixture used in the test suite.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.genres import CURATED_GENRES, slug_for_tag
from app.models import Album, Band, BandBlacklist, BandGenre, BandMember, Genre, Member
from app.settings import settings
from seed.blacklist import apply_blacklist
from seed.genre_allowlist import core_votes, load_allowlist
from seed.outliers import summarize_tags

logger = logging.getLogger("seed.mb_dump")

# MusicBrainz link_type gid for "member of band".
MEMBER_OF_BAND_GID = "5be4c609-9afa-4ea0-910b-12ffb71e3821"

# MBIDs are cast to text on the way out: psycopg2 returns MB's `uuid` columns
# as `UUID` objects, but the app schema stores them as `String(36)`. Without
# this cast the existing-row lookups (`existing_bands.get(row["mbid"])`)
# miss on re-runs and the seed tries to re-insert every row. `CAST(... AS text)`
# is portable across both Postgres and the SQLite fixture the tests use.
_ARTIST_SQL = text(
    """
    SELECT a.id AS artist_id, CAST(a.gid AS text) AS mbid, a.name AS name,
           ar.name AS area_name, a.ended AS ended,
           a.begin_date_year AS begin_year, a.end_date_year AS end_year
    FROM artist a
    JOIN artist_tag atag ON atag.artist = a.id
    JOIN tag t ON t.id = atag.tag
    LEFT JOIN area ar ON ar.id = a.area
    WHERE t.name = :tag AND atag.count > 0
    """
)

_RELEASE_GROUP_SQL = text(
    """
    SELECT acn.artist AS artist_id, CAST(rg.gid AS text) AS rg_mbid, rg.name AS rg_name,
           rgpt.name AS primary_type, rgm.first_release_date_year AS year
    FROM release_group rg
    JOIN artist_credit_name acn ON acn.artist_credit = rg.artist_credit
    LEFT JOIN release_group_primary_type rgpt ON rgpt.id = rg.type
    LEFT JOIN release_group_meta rgm ON rgm.id = rg.id
    WHERE acn.artist IN :artist_ids AND acn.position = 0
    """
).bindparams(bindparam("artist_ids", expanding=True))

_MEMBER_SQL = text(
    """
    SELECT laa.entity1 AS band_id, CAST(m.gid AS text) AS member_mbid, m.name AS member_name,
           MIN(lat.name) AS role
    FROM l_artist_artist laa
    JOIN link l ON l.id = laa.link
    JOIN link_type lt ON lt.id = l.link_type
    JOIN artist m ON m.id = laa.entity0
    LEFT JOIN link_attribute la ON la.link = l.id
    LEFT JOIN link_attribute_type lat ON lat.id = la.attribute_type
    WHERE lt.gid = :member_link_gid AND laa.entity1 IN :band_ids
    GROUP BY laa.entity1, m.gid, m.name
    """
).bindparams(bindparam("band_ids", expanding=True))

# All *positively-voted* tags on the in-scope artists; mapped to curated
# sub-genres in run_seed. MB tag counts can be negative (downvoted to refute
# the tag, e.g. Bathory's "hardcore punk"=-1 / "oi"=-1) or zero — treating
# those as present links bands to genres the community has explicitly rejected.
_ARTIST_TAGS_SQL = text(
    """
    SELECT atag.artist AS artist_id, t.name AS tag_name, atag.count AS votes
    FROM artist_tag atag
    JOIN tag t ON t.id = atag.tag
    WHERE atag.artist IN :artist_ids AND atag.count > 0
    """
).bindparams(bindparam("artist_ids", expanding=True))


@dataclass
class SeedStats:
    bands_inserted: int = 0
    bands_updated: int = 0
    bands_blacklisted: int = 0
    albums_inserted: int = 0
    albums_updated: int = 0
    members_inserted: int = 0
    links_inserted: int = 0
    links_updated: int = 0
    genres_linked: int = 0
    genre_links_updated: int = 0
    skipped: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "bands_inserted": self.bands_inserted,
            "bands_updated": self.bands_updated,
            "bands_blacklisted": self.bands_blacklisted,
            "albums_inserted": self.albums_inserted,
            "albums_updated": self.albums_updated,
            "members_inserted": self.members_inserted,
            "links_inserted": self.links_inserted,
            "links_updated": self.links_updated,
            "genres_linked": self.genres_linked,
            "genre_links_updated": self.genre_links_updated,
            "skipped": len(self.skipped),
        }


def _status_from_ended(ended) -> str:
    return "split-up" if ended in (True, 1, "t", "true") else "active"


def run_seed(mb_engine: Engine, app_session: Session, *, tag: str | None = None) -> SeedStats:
    """Read hardcore-punk artists from `mb_engine`, upsert into `app_session`.

    Idempotent: re-running upserts by MBID rather than duplicating rows.
    """
    tag = tag or settings.seed_tag
    stats = SeedStats()

    # Apply the checked-in blacklist first so the table is at least as broad as
    # the source of truth before we read it back to filter artist rows.
    apply_blacklist(app_session)
    allowlist = load_allowlist()

    with mb_engine.connect() as mb:
        # --- Genres (curated vocabulary) --------------------------------
        # Upsert the curated vocabulary (idempotent by slug); CURATED_GENRES
        # is the source of truth, this table a cache of it. Run before the
        # no-artists early return so the vocabulary is seeded regardless.
        existing_genres = {g.slug: g for g in app_session.query(Genre)}
        for slug, (name, _aliases) in CURATED_GENRES.items():
            genre = existing_genres.get(slug)
            if genre is None:
                genre = Genre(slug=slug, name=name)
                app_session.add(genre)
                existing_genres[slug] = genre
            else:
                genre.name = name
        app_session.flush()  # assign genre ids

        artist_rows = mb.execute(_ARTIST_SQL, {"tag": tag}).mappings().all()
        if not artist_rows:
            logger.warning("No artists found for tag %r", tag)
            app_session.commit()
            return stats

        # Skip MBIDs a curator has previously removed; otherwise every MB dump
        # re-runs would silently resurrect the off-genre bands they cleaned out.
        blacklist = {b.mbid for b in app_session.query(BandBlacklist)}
        if blacklist:
            kept: list = []
            for row in artist_rows:
                if row["mbid"] in blacklist:
                    stats.bands_blacklisted += 1
                else:
                    kept.append(row)
            artist_rows = kept

        # --- Bands -------------------------------------------------------
        existing_bands = {b.mbid: b for b in app_session.query(Band).filter(Band.mbid.isnot(None))}
        # MB artist.id -> app Band (so release-groups/members can link back).
        band_by_mb_id: dict[int, Band] = {}

        for row in artist_rows:
            area = row["area_name"] or ""
            band = existing_bands.get(row["mbid"])
            if band is None:
                band = Band(mbid=row["mbid"])
                app_session.add(band)
                stats.bands_inserted += 1
            else:
                stats.bands_updated += 1
            band.name = row["name"]
            band.status = _status_from_ended(row["ended"])
            band.begin_year = row["begin_year"]
            band.end_year = row["end_year"]
            band.location = area
            band.country = area
            band.label = band.label or ""
            band_by_mb_id[row["artist_id"]] = band

        app_session.flush()  # assign band ids

        mb_artist_ids = list(band_by_mb_id.keys())

        # --- Albums (release-groups) ------------------------------------
        rg_rows = mb.execute(_RELEASE_GROUP_SQL, {"artist_ids": mb_artist_ids}).mappings().all()
        existing_albums = {
            a.release_group_mbid: a
            for a in app_session.query(Album).filter(Album.release_group_mbid.isnot(None))
        }
        for row in rg_rows:
            band = band_by_mb_id.get(row["artist_id"])
            if band is None:
                stats.skipped.append(f"rg {row['rg_mbid']} (orphan artist)")
                continue
            album = existing_albums.get(row["rg_mbid"])
            if album is None:
                album = Album(release_group_mbid=row["rg_mbid"])
                app_session.add(album)
                stats.albums_inserted += 1
            else:
                stats.albums_updated += 1
            album.name = row["rg_name"]
            album.release_type = row["primary_type"]
            album.year = row["year"]
            album.band = band

        # --- Members ----------------------------------------------------
        member_rows = (
            mb.execute(
                _MEMBER_SQL,
                {"band_ids": mb_artist_ids, "member_link_gid": MEMBER_OF_BAND_GID},
            )
            .mappings()
            .all()
        )
        existing_members = {
            m.mbid: m for m in app_session.query(Member).filter(Member.mbid.isnot(None))
        }
        existing_links = {(bm.band_id, bm.member_id): bm for bm in app_session.query(BandMember)}
        for row in member_rows:
            band = band_by_mb_id.get(row["band_id"])
            if band is None:
                continue
            member = existing_members.get(row["member_mbid"])
            if member is None:
                member = Member(mbid=row["member_mbid"], name=row["member_name"])
                app_session.add(member)
                app_session.flush()
                existing_members[row["member_mbid"]] = member
                stats.members_inserted += 1
            else:
                member.name = row["member_name"]
            link = existing_links.get((band.id, member.id))
            if link is None:
                link = BandMember(band=band, member=member, role=row["role"])
                app_session.add(link)
                existing_links[(band.id, member.id)] = link
                stats.links_inserted += 1
            elif link.role != row["role"]:
                link.role = row["role"]
                stats.links_updated += 1

        # --- Genres (curated sub-genres) --------------------------------
        # The curated vocabulary was upserted above; here we link bands to it.
        # Map each artist tag onto a curated slug, dropping anything not curated
        # (including the broad scope tag itself), and link it to the band.
        tag_rows = mb.execute(_ARTIST_TAGS_SQL, {"artist_ids": mb_artist_ids}).mappings().all()
        # Group tags per MB artist once; we use the grouped form both to link
        # curated genres below and to compute the per-band outlier-audit
        # signals (seed_share et al.) at the bottom of this function.
        tags_by_artist: dict[int, list[tuple[str, int]]] = {}
        for row in tag_rows:
            tags_by_artist.setdefault(row["artist_id"], []).append(
                (row["tag_name"], int(row["votes"] or 0))
            )

        # One-shot heal of bad rows the pre-fix seed wrote: any link whose
        # vote_count is non-positive came from a downvoted MB tag (e.g.
        # Bathory's "oi"=-1). The current SQL filters those out at source, so
        # we'll never recreate them — drop them here so the public band page
        # stops surfacing community-refuted sub-genres.
        bad_link_count = (
            app_session.query(BandGenre)
            .filter(BandGenre.vote_count <= 0)
            .delete(synchronize_session=False)
        )
        if bad_link_count:
            logger.info("Purged %d non-positive-vote genre links", bad_link_count)
        app_session.flush()

        existing_genre_links = {
            (bg.band_id, bg.genre_id): bg for bg in app_session.query(BandGenre)
        }
        for row in tag_rows:
            band = band_by_mb_id.get(row["artist_id"])
            if band is None:
                continue
            slug = slug_for_tag(row["tag_name"])
            if slug is None:
                continue
            genre = existing_genres[slug]
            votes = row["votes"] or 0
            link = existing_genre_links.get((band.id, genre.id))
            if link is None:
                link = BandGenre(band=band, genre=genre, vote_count=votes)
                app_session.add(link)
                existing_genre_links[(band.id, genre.id)] = link
                stats.genres_linked += 1
            elif votes > link.vote_count:
                # A second alias of the same genre, or a refreshed vote count;
                # keep the strongest signal.
                link.vote_count = votes
                stats.genre_links_updated += 1

        # --- Outlier audit signals --------------------------------------
        # Persist (seed_votes, total_tag_votes, seed_share) onto each band
        # so /band/needs-review can rank candidate outliers without touching
        # the MB dump. Bands with no tag rows get zeros / a null share.
        for mb_artist_id, band in band_by_mb_id.items():
            tags = tags_by_artist.get(mb_artist_id, [])
            seed_votes, total, _other = summarize_tags(tags, tag)
            band.seed_votes = seed_votes
            band.total_tag_votes = total
            band.seed_share = (seed_votes / total) if total else None
            # Split rule: only flag when MB users *did* tag the band but with
            # nothing in the core allowlist. Bands with no MB tags at all
            # (total == 0) stay unflagged — "no signal" gets a different
            # review surface, not an off-genre verdict.
            band.auto_flagged = total > 0 and core_votes(tags, allowlist) == 0
            # Snapshot the full tag list (votes desc) so curators can audit the
            # raw signal without the MB dump on hand. Empty list (not null) when
            # MB has no tags, so the UI can distinguish "seeded, no tags" from
            # "never seeded".
            band.mb_tags = [
                {"name": n, "votes": v}
                for n, v in sorted(tags, key=lambda x: -x[1])
            ]

    app_session.commit()
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mb_engine = create_engine(settings.mb_database_url)
    session = SessionLocal()
    try:
        stats = run_seed(mb_engine, session, tag=settings.seed_tag)
        logger.info("Seed complete: %s", stats.as_dict())
    finally:
        session.close()
        mb_engine.dispose()


if __name__ == "__main__":
    main()
