"""Populate `band.band_picture` and `band.logo` from Wikidata.

The MB dump has no images, but artists often link to Wikidata, which carries
P18 (image) and P154 (logo image) pointing to Wikimedia Commons files. We store
`Special:FilePath` URLs — Commons' stable redirect to the actual file on
upload.wikimedia.org.

Run after `seed.mb_dump` (and any time afterward to backfill new bands):

    python -m seed.band_art

Idempotent: only touches bands missing the relevant field.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Band
from app.settings import settings

logger = logging.getLogger("seed.band_art")

# MB link_type gid for artist→URL "wikidata".
WIKIDATA_LINK_GID = "689870a4-a1e4-4912-b17f-7b2664215698"
COMMONS_FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "Hardchives/0.1 (mrucoding@gmail.com)"
BATCH_SIZE = 50  # wbgetentities accepts up to 50 ids per call

_WIKIDATA_LINKS_SQL = text(
    """
    SELECT a.gid AS mbid, u.url AS url
    FROM artist a
    JOIN l_artist_url lau ON lau.entity0 = a.id
    JOIN link l ON l.id = lau.link
    JOIN link_type lt ON lt.id = l.link_type
    JOIN url u ON u.id = lau.entity1
    WHERE lt.gid = :wd_gid AND a.gid IN :mbids
    """
).bindparams(bindparam("mbids", expanding=True))


@dataclass
class BandArtStats:
    checked: int = 0
    picture_set: int = 0
    logo_set: int = 0
    missing: int = 0  # had a wikidata link but no usable P18/P154
    no_wikidata: int = 0  # no wikidata URL on MB at all

    def as_dict(self) -> dict:
        return {
            "checked": self.checked,
            "picture_set": self.picture_set,
            "logo_set": self.logo_set,
            "missing": self.missing,
            "no_wikidata": self.no_wikidata,
        }


def commons_url(filename: str) -> str:
    """Build the stable Special:FilePath URL for a Commons file."""
    # MediaWiki normalizes spaces to underscores; the path segment is then
    # percent-encoded.
    return COMMONS_FILEPATH + urllib.parse.quote(filename.replace(" ", "_"), safe="")


def _parse_qid(url: str) -> str | None:
    tail = url.rstrip("/").split("#", 1)[0].split("?", 1)[0].rsplit("/", 1)[-1]
    if tail.startswith("Q") and tail[1:].isdigit():
        return tail
    return None


def _first_filename(claims: list | None) -> str | None:
    if not claims:
        return None
    for claim in claims:
        try:
            value = claim["mainsnak"]["datavalue"]["value"]
        except (KeyError, TypeError):
            continue
        if isinstance(value, str) and value:
            return value
    return None


def _default_resolve(qids: list[str]) -> dict[str, dict[str, str | None]]:
    """Fetch P18 / P154 for each QID from the Wikidata API."""
    if not qids:
        return {}
    params = urllib.parse.urlencode(
        {
            "action": "wbgetentities",
            "ids": "|".join(qids),
            "props": "claims",
            "format": "json",
        }
    )
    req = urllib.request.Request(f"{WIKIDATA_API}?{params}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        logger.warning("Wikidata batch failed: %s", e)
        return {}
    out: dict[str, dict[str, str | None]] = {}
    for qid, entity in (data.get("entities") or {}).items():
        claims = entity.get("claims") or {}
        out[qid] = {
            "image": _first_filename(claims.get("P18")),
            "logo": _first_filename(claims.get("P154")),
        }
    return out


def fetch_band_art(
    mb_engine: Engine,
    session: Session,
    *,
    resolve: Callable[[list[str]], dict[str, dict[str, str | None]]] = _default_resolve,
    limit: int | None = None,
) -> BandArtStats:
    """Set `band_picture` / `logo` on bands using Wikidata's P18 / P154."""
    query = (
        session.query(Band)
        .filter(
            Band.mbid.isnot(None),
            (Band.band_picture.is_(None)) | (Band.logo.is_(None)),
        )
        .order_by(Band.id.asc())
    )
    if limit is not None:
        query = query.limit(limit)
    bands = query.all()

    stats = BandArtStats()
    if not bands:
        return stats

    bands_by_mbid = {b.mbid: b for b in bands}
    with mb_engine.connect() as mb:
        link_rows = (
            mb.execute(
                _WIKIDATA_LINKS_SQL,
                {"wd_gid": WIKIDATA_LINK_GID, "mbids": list(bands_by_mbid)},
            )
            .mappings()
            .all()
        )

    qid_by_mbid: dict[str, str] = {}
    for row in link_rows:
        qid = _parse_qid(row["url"])
        if qid is not None:
            qid_by_mbid[row["mbid"]] = qid

    all_qids = list({qid for qid in qid_by_mbid.values()})
    resolved: dict[str, dict[str, str | None]] = {}
    for i in range(0, len(all_qids), BATCH_SIZE):
        resolved.update(resolve(all_qids[i : i + BATCH_SIZE]))

    for band in bands:
        stats.checked += 1
        qid = qid_by_mbid.get(band.mbid)
        if qid is None:
            stats.no_wikidata += 1
            continue
        info = resolved.get(qid)
        if info is None:
            stats.missing += 1
            continue
        image = info.get("image")
        logo = info.get("logo")
        got_anything = False
        if image and band.band_picture is None:
            band.band_picture = commons_url(image)
            stats.picture_set += 1
            got_anything = True
        if logo and band.logo is None:
            band.logo = commons_url(logo)
            stats.logo_set += 1
            got_anything = True
        if not got_anything:
            stats.missing += 1

    session.commit()
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mb_engine = create_engine(settings.mb_database_url)
    session = SessionLocal()
    try:
        stats = fetch_band_art(mb_engine, session)
        logger.info("Band art complete: %s", stats.as_dict())
    finally:
        session.close()
        mb_engine.dispose()


if __name__ == "__main__":
    main()
