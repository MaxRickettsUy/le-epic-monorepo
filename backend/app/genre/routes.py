from fastapi import APIRouter

from app import schemas
from app.genres import CURATED_GENRES

router = APIRouter()


@router.get("/", response_model=list[schemas.GenreOut])
def list_genres():
    """The curated sub-genre vocabulary, alphabetical by display name. Served from
    `app.genres.CURATED_GENRES` (the source of truth), so it is available even
    before the seed populates `band_genre`."""
    return [
        schemas.GenreOut(slug=slug, name=name)
        for slug, (name, _aliases) in sorted(
            CURATED_GENRES.items(), key=lambda kv: kv[1][0].lower()
        )
    ]
