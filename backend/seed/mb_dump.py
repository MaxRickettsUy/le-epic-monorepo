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
from app.models import Album, Band, BandMember, Member
from app.settings import settings

logger = logging.getLogger("seed.mb_dump")

# MusicBrainz link_type gid for "member of band".
MEMBER_OF_BAND_GID = "5be4c609-9afa-4ea0-910b-12ffb71e3821"

_ARTIST_SQL = text(
    """
    SELECT a.id AS artist_id, a.gid AS mbid, a.name AS name,
           ar.name AS area_name, a.ended AS ended
    FROM artist a
    JOIN artist_tag atag ON atag.artist = a.id
    JOIN tag t ON t.id = atag.tag
    LEFT JOIN area ar ON ar.id = a.area
    WHERE t.name = :tag
    """
)

_RELEASE_GROUP_SQL = text(
    """
    SELECT acn.artist AS artist_id, rg.gid AS rg_mbid, rg.name AS rg_name,
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
    SELECT laa.entity1 AS band_id, m.gid AS member_mbid, m.name AS member_name,
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


@dataclass
class SeedStats:
    bands_inserted: int = 0
    bands_updated: int = 0
    albums_inserted: int = 0
    albums_updated: int = 0
    members_inserted: int = 0
    links_inserted: int = 0
    links_updated: int = 0
    skipped: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "bands_inserted": self.bands_inserted,
            "bands_updated": self.bands_updated,
            "albums_inserted": self.albums_inserted,
            "albums_updated": self.albums_updated,
            "members_inserted": self.members_inserted,
            "links_inserted": self.links_inserted,
            "links_updated": self.links_updated,
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

    with mb_engine.connect() as mb:
        artist_rows = mb.execute(_ARTIST_SQL, {"tag": tag}).mappings().all()
        if not artist_rows:
            logger.warning("No artists found for tag %r", tag)
            return stats

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
