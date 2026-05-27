"""Pydantic response/request schemas.

Shapes mirror the frontend contract in ../app/lib/types.ts. Reviews are out of
MVP, so `avg_review`/`review_count` are always 0 and `members` is always []
(the `Member` table arrives in Phase 3).
"""

from pydantic import BaseModel, ConfigDict, computed_field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseInput(BaseModel):
    """Base for request bodies; rejects unknown fields with a 422."""

    model_config = ConfigDict(extra="forbid")


# --- Track -----------------------------------------------------------------


class TrackOut(ORMModel):
    id: int
    name: str
    length: int | None = None
    lyrics: str | None = None
    track_number: int | None = None
    position: int | None = None
    mbid: str | None = None


class TrackCreate(BaseInput):
    name: str
    track_number: int
    length: int | None = None
    lyrics: str | None = None


# --- Release ---------------------------------------------------------------


class ReleaseBase(ORMModel):
    id: int
    name: str
    length: int | None = None
    art: str | None = None
    release_type: str | None = None
    label: str | None = None
    year: int | None = None
    release_group_mbid: str | None = None
    band_id: int

    # Reviews are out of MVP; the frontend still reads these fields.
    avg_review: float = 0
    review_count: int = 0

    @computed_field
    @property
    def type(self) -> str | None:
        # Frontend type alias for release_type.
        return self.release_type


class ReleaseInBand(ReleaseBase):
    """Release as nested under a band (no back-reference to avoid recursion)."""


class BandSummary(ORMModel):
    """Band as nested under a release detail response."""

    id: int
    name: str
    location: str
    country: str
    label: str


class ReleaseDetail(ReleaseBase):
    band: BandSummary
    tracks: list[TrackOut] = []


class ReleaseCreate(BaseInput):
    name: str
    length: int | None = None
    art: str | None = None
    release_type: str | None = None
    label: str | None = None
    year: int | None = None


# --- Band ------------------------------------------------------------------


class Member(ORMModel):
    # Validates off a BandMember association object (`name` is a property there).
    name: str
    role: str | None = None


class BandBase(ORMModel):
    id: int
    name: str
    status: str
    band_picture: str | None = None
    logo: str | None = None
    location: str
    country: str
    label: str
    mbid: str | None = None
    begin_year: int | None = None
    end_year: int | None = None


class BandListItem(BandBase):
    pass


class BandList(BaseModel):
    bands: list[BandListItem]
    next: int | None = None
    prev: int | None = None


class BandDetail(BandBase):
    members: list[Member] = []
    releases: list[ReleaseInBand] = []


class SimilarBand(ORMModel):
    """A band scored as similar to another, with the contributing factors.

    `score` is a weighted sum (see `band.routes.SIMILARITY_WEIGHTS`); the
    boolean/count fields expose *why* it matched so the UI can explain it.
    """

    id: int
    name: str
    location: str
    country: str
    score: int
    shared_members: int
    same_location: bool
    same_label: bool
    same_country: bool


class BandCreate(BaseInput):
    name: str
    status: str
    band_picture: str | None = None
    logo: str | None = None
    location: str
    country: str
    label: str


# --- Search ----------------------------------------------------------------


class BandSearchItem(ORMModel):
    """A band matched by a catalogue search."""

    id: int
    name: str
    location: str
    country: str


class AlbumSearchItem(ORMModel):
    """An album matched by a catalogue search, carrying its band for linking."""

    id: int
    name: str
    year: int | None = None
    art: str | None = None
    band_id: int
    band_name: str


class SearchResults(BaseModel):
    """Combined results of a catalogue search across bands and albums."""

    query: str
    bands: list[BandSearchItem]
    albums: list[AlbumSearchItem]
