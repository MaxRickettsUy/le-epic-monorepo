from typing import Literal

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app import schemas
from app.database import get_db
from app.models import Band, BandGenre, BandMember
from app.services import musicbrainz
from app.settings import settings

router = APIRouter()

# Weights for the similar-bands score. No real similarity model exists yet, so
# we combine the locally-stored signals; higher = stronger pull. Tune freely —
# the per-factor contributions are returned on each result so the effect of a
# change is visible in the UI. (MusicBrainz artist relations would be a natural
# extra signal but aren't stored; that needs new modelling + seed work first.)
SIMILARITY_WEIGHTS = {
    "shared_member": 5,  # per member the two bands have in common
    "location": 4,  # same local scene
    "shared_genre": 3,  # per curated sub-genre the two bands have in common
    "label": 2,  # same record label
    "country": 1,  # same country (weak tie-breaker)
}


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
        sa.select(Band)
        .options(selectinload(Band.genres).selectinload(BandGenre.genre))
        .order_by(*order)
        .offset((page - 1) * per_page)
        .limit(per_page)
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
            selectinload(Band.genres).selectinload(BandGenre.genre),
        )
        .where(Band.id == id)
    )
    if band is None:
        raise HTTPException(status_code=404, detail="Band not found")
    return band


@router.get("/{id}/similar", response_model=list[schemas.SimilarBand])
def get_similar(id: int, db: Session = Depends(get_db)):
    band = db.get(Band, id)
    if band is None:
        raise HTTPException(status_code=404, detail="Band not found")

    w = SIMILARITY_WEIGHTS

    # How many members each candidate shares with this band.
    target_member_ids = (
        sa.select(BandMember.member_id).where(BandMember.band_id == band.id).scalar_subquery()
    )
    shared_members = (
        sa.select(sa.func.count())
        .select_from(BandMember)
        .where(BandMember.band_id == Band.id, BandMember.member_id.in_(target_member_ids))
        .correlate(Band)
        .scalar_subquery()
    )

    # How many curated sub-genres each candidate shares with this band.
    target_genre_ids = (
        sa.select(BandGenre.genre_id).where(BandGenre.band_id == band.id).scalar_subquery()
    )
    shared_genres = (
        sa.select(sa.func.count())
        .select_from(BandGenre)
        .where(BandGenre.band_id == Band.id, BandGenre.genre_id.in_(target_genre_ids))
        .correlate(Band)
        .scalar_subquery()
    )

    # Per-factor 0/1 flags (label only counts when it is actually set).
    same_location = sa.case((Band.location == band.location, 1), else_=0)
    same_label = sa.case(((Band.label == band.label) & (Band.label != ""), 1), else_=0)
    same_country = sa.case((Band.country == band.country, 1), else_=0)

    score = (
        w["shared_member"] * shared_members
        + w["location"] * same_location
        + w["shared_genre"] * shared_genres
        + w["label"] * same_label
        + w["country"] * same_country
    )

    rows = db.execute(
        sa.select(
            Band,
            shared_members.label("shared_members"),
            shared_genres.label("shared_genres"),
            same_location.label("same_location"),
            same_label.label("same_label"),
            same_country.label("same_country"),
            score.label("score"),
        )
        .where(Band.id != band.id, score > 0)
        .order_by(score.desc(), Band.name)
        .limit(settings.bands_per_page)
    ).all()

    return [
        schemas.SimilarBand(
            id=cand.id,
            name=cand.name,
            location=cand.location,
            country=cand.country,
            score=total,
            shared_members=members,
            shared_genres=genres,
            same_location=bool(loc),
            same_label=bool(label),
            same_country=bool(country),
        )
        for cand, members, genres, loc, label, country, total in rows
    ]


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
