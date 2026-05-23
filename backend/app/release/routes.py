import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app import schemas
from app.database import get_db
from app.models import Album, Band

router = APIRouter()


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
