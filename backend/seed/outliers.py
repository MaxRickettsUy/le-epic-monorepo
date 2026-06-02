"""Surface bands in the catalogue that look off-genre.

Every band in the app DB was seeded because MusicBrainz tagged it with
``settings.seed_tag`` ("hardcore punk") — but tag strength varies wildly. A
band with a single "hardcore punk" vote drowning in 20 votes of "indie rock"
is almost certainly a false positive; a band with 30 votes of "hardcore punk"
and 5 of "metalcore" is the real deal.

This script joins the app DB against the MB dump and ranks each band by a
"hardcore-punk share" of its total tag votes. Low share => likely outlier.

Run::

    python -m seed.outliers              # print top 50 candidate outliers
    python -m seed.outliers --limit 200  # print more
    python -m seed.outliers --csv > outliers.csv

The output is human-curation input — the script does *not* delete anything or
write ``inclusion_reason``. The intent is: review the list, drop bands that
don't belong, and write a short ``inclusion_reason`` on the ones that do.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Band
from app.settings import settings

# All tags + vote counts for the given artist MBIDs, joined to the app's bands
# via MBID so we don't need to assume app/MB share an integer artist id.
_TAGS_BY_MBID_SQL = text(
    """
    SELECT a.gid AS mbid, t.name AS tag_name, atag.count AS votes
    FROM artist a
    JOIN artist_tag atag ON atag.artist = a.id
    JOIN tag t ON t.id = atag.tag
    WHERE a.gid IN :mbids
    """
).bindparams(bindparam("mbids", expanding=True))


@dataclass
class OutlierRow:
    band_id: int
    name: str
    country: str
    seed_votes: int
    total_votes: int
    top_tags: list[tuple[str, int]]  # (tag, votes) — strongest first, excluding seed_tag

    @property
    def seed_share(self) -> float:
        return (self.seed_votes / self.total_votes) if self.total_votes else 0.0


def collect(app_session: Session, mb_engine, seed_tag: str) -> list[OutlierRow]:
    bands = app_session.query(Band).filter(Band.mbid.isnot(None)).all()
    by_mbid: dict[str, Band] = {b.mbid: b for b in bands if b.mbid}
    if not by_mbid:
        return []

    seed_key = seed_tag.strip().lower()
    per_band_tags: dict[str, list[tuple[str, int]]] = {mbid: [] for mbid in by_mbid}

    with mb_engine.connect() as mb:
        rows = mb.execute(_TAGS_BY_MBID_SQL, {"mbids": list(by_mbid.keys())}).mappings().all()
    for row in rows:
        per_band_tags[row["mbid"]].append((row["tag_name"], int(row["votes"] or 0)))

    out: list[OutlierRow] = []
    for mbid, band in by_mbid.items():
        tags = per_band_tags.get(mbid, [])
        seed_votes = sum(v for n, v in tags if n.strip().lower() == seed_key)
        total = sum(v for _, v in tags)
        other = sorted(
            ((n, v) for n, v in tags if n.strip().lower() != seed_key),
            key=lambda x: -x[1],
        )[:5]
        out.append(
            OutlierRow(
                band_id=band.id,
                name=band.name,
                country=band.country or "",
                seed_votes=seed_votes,
                total_votes=total,
                top_tags=other,
            )
        )
    # Lowest seed-share first; then bands with the most "other" votes (loudest
    # off-genre signal). Bands with no MB tags at all sink to the bottom — we
    # can't say anything about them.
    out.sort(key=lambda r: (r.total_votes == 0, r.seed_share, -r.total_votes))
    return out


def _format_tags(tags: list[tuple[str, int]]) -> str:
    return ", ".join(f"{n} ({v})" for n, v in tags) or "—"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--limit", type=int, default=50, help="How many candidates to print")
    p.add_argument("--csv", action="store_true", help="Emit CSV instead of a table")
    args = p.parse_args(argv)

    mb_engine = create_engine(settings.mb_database_url)
    session = SessionLocal()
    try:
        rows = collect(session, mb_engine, settings.seed_tag)
    finally:
        session.close()
        mb_engine.dispose()

    rows = rows[: args.limit]

    if args.csv:
        w = csv.writer(sys.stdout)
        w.writerow(
            [
                "band_id",
                "name",
                "country",
                "seed_share",
                "seed_votes",
                "total_votes",
                "top_other_tags",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.band_id,
                    r.name,
                    r.country,
                    f"{r.seed_share:.2f}",
                    r.seed_votes,
                    r.total_votes,
                    "; ".join(f"{n}={v}" for n, v in r.top_tags),
                ]
            )
        return 0

    print(f"{'id':>6}  {'share':>6}  {'seed/total':>10}  {'name':<40}  top other tags")
    print("-" * 110)
    for r in rows:
        print(
            f"{r.band_id:>6}  {r.seed_share:>5.0%}  "
            f"{r.seed_votes:>4}/{r.total_votes:<5}  {r.name[:40]:<40}  {_format_tags(r.top_tags)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
