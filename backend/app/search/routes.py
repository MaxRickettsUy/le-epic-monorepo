import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app import schemas
from app.database import get_db
from app.models import Album, Band, BandGenre, Genre

router = APIRouter()

# Cap per result type so an empty/loose query can't return the whole catalogue.
RESULTS_PER_TYPE = 20


def _contains(column, query: str):
    """Case-insensitive substring match, with LIKE wildcards in `query` escaped
    so a literal `%` or `_` typed by the user matches itself, not anything."""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


@router.get("/", response_model=schemas.SearchResults)
def search(
    q: str = Query(..., min_length=1, description="Free-text query matched against names"),
    genre: str | None = Query(None, description="Restrict band results to this genre slug"),
    db: Session = Depends(get_db),
):
    term = q.strip()
    if not term:
        raise HTTPException(status_code=422, detail="Query must not be blank")

    # A band matches the text query by name, location, or one of its genre names.
    band_match = sa.or_(
        _contains(Band.name, term),
        _contains(Band.location, term),
        Band.genres.any(BandGenre.genre.has(_contains(Genre.name, term))),
    )

    band_query = (
        sa.select(Band)
        .options(selectinload(Band.genres).selectinload(BandGenre.genre))
        .where(band_match)
    )
    if genre is not None:
        # Facet: keep only bands carrying the given curated slug.
        band_query = band_query.where(Band.genres.any(BandGenre.genre.has(Genre.slug == genre)))

    bands = db.scalars(
        band_query.order_by(Band.name.asc(), Band.id.asc()).limit(RESULTS_PER_TYPE)
    ).all()

    albums = db.scalars(
        sa.select(Album)
        .options(joinedload(Album.band))
        .where(_contains(Album.name, term))
        .order_by(Album.name.asc(), Album.id.asc())
        .limit(RESULTS_PER_TYPE)
    ).all()

    return schemas.SearchResults(
        query=term,
        bands=[schemas.BandSearchItem.model_validate(b) for b in bands],
        albums=[
            schemas.AlbumSearchItem(
                id=a.id,
                name=a.name,
                year=a.year,
                art=a.art,
                band_id=a.band_id,
                band_name=a.band.name,
            )
            for a in albums
        ],
    )
