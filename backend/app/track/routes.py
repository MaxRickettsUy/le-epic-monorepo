from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Album, Track

router = APIRouter()


@router.post("/new")
def create(
    payload: schemas.TrackCreate,
    release: int = Query(..., description="Release id to attach the track to"),
    db: Session = Depends(get_db),
):
    release_row = db.get(Album, release)
    if release_row is None:
        raise HTTPException(status_code=404, detail="Release not found")

    track = Track(release=release_row, **payload.model_dump())
    db.add(track)
    db.commit()
    return {"message": "track created", "id": track.id}


@router.get("/{id}", response_model=schemas.TrackOut)
def get(id: int, db: Session = Depends(get_db)):
    track = db.get(Track, id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.post("/{id}/update")
def update(id: int, payload: schemas.TrackCreate, db: Session = Depends(get_db)):
    track = db.get(Track, id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    for field, value in payload.model_dump().items():
        setattr(track, field, value)
    db.commit()
    return "track updated"


@router.delete("/{id}/delete")
def delete(id: int, db: Session = Depends(get_db)):
    track = db.get(Track, id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    db.delete(track)
    db.commit()
    return "track deleted"
