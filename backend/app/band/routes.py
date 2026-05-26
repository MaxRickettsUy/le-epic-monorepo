from typing import Literal

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app import schemas
from app.database import get_db
from app.models import Band, BandMember
from app.services import musicbrainz
from app.settings import settings

router = APIRouter()


@router.get("/", response_model=schemas.BandList)
@router.get("/index", response_model=schemas.BandList, include_in_schema=False)
def get_all(
    page: int = Query(1, ge=1),
    sort: Literal["name", "recent"] = Query("name"),
    db: Session = Depends(get_db),
):
    per_page = settings.bands_per_page
    total = db.scalar(sa.select(sa.func.count()).select_from(Band))
    order = (
        (Band.created_at.desc(), Band.id.desc())
        if sort == "recent"
        else (Band.name.asc(), Band.id.asc())
    )
    bands = db.scalars(
        sa.select(Band).order_by(*order).offset((page - 1) * per_page).limit(per_page)
    ).all()

    has_next = page * per_page < total
    return schemas.BandList(
        bands=[schemas.BandListItem.model_validate(b) for b in bands],
        next=page + 1 if has_next else None,
        prev=page - 1 if page > 1 else None,
    )


@router.post("/new")
def create(payload: schemas.BandCreate, db: Session = Depends(get_db)):
    band = Band(**payload.model_dump())
    db.add(band)
    db.commit()
    return {"message": "Band created", "id": band.id}


@router.get("/search")
def search_artist(name: str = Query(...)):
    try:
        return musicbrainz.search_hardcore_artists(name)
    except musicbrainz.WebServiceError as e:
        raise HTTPException(status_code=503, detail=f"MusicBrainz API error: {e}") from e


@router.get("/search_releases")
def search_releases(mbid: str = Query(...)):
    try:
        return musicbrainz.get_releases_by_artist_id(mbid)
    except LookupError as e:
        raise HTTPException(status_code=404, detail="Band not found") from e
    except musicbrainz.WebServiceError as e:
        raise HTTPException(status_code=503, detail=f"MusicBrainz API error: {e}") from e


@router.get("/{id}", response_model=schemas.BandDetail)
def get(id: int, db: Session = Depends(get_db)):
    band = db.scalar(
        sa.select(Band)
        .options(
            selectinload(Band.releases),
            selectinload(Band.members).selectinload(BandMember.member),
        )
        .where(Band.id == id)
    )
    if band is None:
        raise HTTPException(status_code=404, detail="Band not found")
    return band


@router.post("/{id}/update")
def update(id: int, payload: schemas.BandCreate, db: Session = Depends(get_db)):
    band = db.get(Band, id)
    if band is None:
        raise HTTPException(status_code=404, detail="Band not found")
    for field, value in payload.model_dump().items():
        setattr(band, field, value)
    db.commit()
    return "band updated"


@router.delete("/{id}/delete")
def delete(id: int, db: Session = Depends(get_db)):
    band = db.get(Band, id)
    if band is None:
        raise HTTPException(status_code=404, detail="Band not found")
    db.delete(band)
    db.commit()
    return "band deleted"
