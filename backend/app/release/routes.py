from typing import Literal

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app import schemas
from app.database import get_db
from app.models import Album, Band
from app.settings import settings

router = APIRouter()


@router.get("/", response_model=schemas.ReleaseList)
def get_all(
    page: int = Query(1, ge=1),
    sort: Literal["recent", "year"] = Query("recent"),
    db: Session = Depends(get_db),
):
    """Paginated catalogue listing of releases, ordered for discovery.

    `recent` (default) orders by `created_at desc` — newest seeded first.
    `year` orders by release year desc, nulls last, then by name.
    """
    per_page = settings.releases_per_page

    total = db.scalar(sa.select(sa.func.count()).select_from(Album))
    if sort == "year":
        order = (Album.year.is_(None), Album.year.desc(), Album.name.asc(), Album.id.asc())
    else:
        order = (Album.created_at.desc(), Album.id.desc())

    albums = db.scalars(
        sa.select(Album)
        .options(joinedload(Album.band))
        .order_by(*order)
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()

    has_next = page * per_page < total
    return schemas.ReleaseList(
        releases=[
            schemas.ReleaseListItem(
                id=a.id,
                name=a.name,
                year=a.year,
                art=a.art,
                band_id=a.band_id,
                band_name=a.band.name,
            )
            for a in albums
        ],
        next=page + 1 if has_next else None,
        prev=page - 1 if page > 1 else None,
    )


@router.post("/new")
def create(
    payload: schemas.ReleaseCreate,
    band: int = Query(..., description="Band id to attach the release to"),
    db: Session = Depends(get_db),
):
    band_row = db.get(Band, band)
    if band_row is None:
        raise HTTPException(status_code=404, detail="Band not found")

    album = Album(band=band_row, **payload.model_dump())
    db.add(album)
    db.commit()
    return {"message": "Release created", "id": album.id}


@router.get("/{id}", response_model=schemas.ReleaseDetail)
def get(id: int, db: Session = Depends(get_db)):
    album = db.scalar(
        sa.select(Album)
        .options(joinedload(Album.band), selectinload(Album.tracks))
        .where(Album.id == id)
    )
    if album is None:
        raise HTTPException(status_code=404, detail="Release not found")
    album.tracks.sort(key=lambda t: (t.position is None, t.position))
    return album


@router.post("/{id}/update")
def update(id: int, payload: schemas.ReleaseCreate, db: Session = Depends(get_db)):
    album = db.get(Album, id)
    if album is None:
        raise HTTPException(status_code=404, detail="Release not found")
    for field, value in payload.model_dump().items():
        setattr(album, field, value)
    db.commit()
    return "release update successful"


@router.delete("/{id}/delete")
def delete(id: int, db: Session = Depends(get_db)):
    album = db.get(Album, id)
    if album is None:
        raise HTTPException(status_code=404, detail="Release not found")
    db.delete(album)
    db.commit()
    return "release delete successful"
