import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app import schemas
from app.database import get_db
from app.models import Album, Band

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
    db: Session = Depends(get_db),
):
    term = q.strip()
    if not term:
        raise HTTPException(status_code=422, detail="Query must not be blank")

    bands = db.scalars(
        sa.select(Band)
        .where(sa.or_(_contains(Band.name, term), _contains(Band.location, term)))
        .order_by(Band.name.asc(), Band.id.asc())
        .limit(RESULTS_PER_TYPE)
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
