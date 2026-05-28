from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as so

from app.database import Base

# NOTE: User and Review are intentionally not modeled — reviews are out of MVP.
# The legacy `user`/`review` tables are dropped in the Phase 3 migration.


class TimestampMixin:
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )


class Band(TimestampMixin, Base):
    __tablename__ = "band"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), index=True)
    status: so.Mapped[str] = so.mapped_column(sa.String(25))
    band_picture: so.Mapped[str | None] = so.mapped_column(sa.String(150))
    logo: so.Mapped[str | None] = so.mapped_column(sa.String(150))
    location: so.Mapped[str] = so.mapped_column(sa.String(100))
    country: so.Mapped[str] = so.mapped_column(sa.String(100))
    label: so.Mapped[str] = so.mapped_column(sa.String(100))
    mbid: so.Mapped[str | None] = so.mapped_column(sa.String(36), index=True, unique=True)
    begin_year: so.Mapped[int | None] = so.mapped_column(sa.Integer())
    end_year: so.Mapped[int | None] = so.mapped_column(sa.Integer())

    # Attribute kept as `releases` so the API/JSON shape is unchanged even
    # though the underlying model/table is now Album.
    releases: so.Mapped[list["Album"]] = so.relationship(
        back_populates="band",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    members: so.Mapped[list["BandMember"]] = so.relationship(
        back_populates="band",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    genres: so.Mapped[list["BandGenre"]] = so.relationship(
        back_populates="band",
        cascade="all, delete-orphan",
        passive_deletes=True,
        # Strongest-voted (primary) sub-genre first; deterministic for the API.
        order_by="desc(BandGenre.vote_count), BandGenre.genre_id",
    )


class Album(TimestampMixin, Base):
    # Renamed from Release: one row per release-group (album), not per pressing.
    __tablename__ = "album"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(200))
    length: so.Mapped[int | None] = so.mapped_column(sa.Integer())
    art: so.Mapped[str | None] = so.mapped_column(sa.String(150))
    release_type: so.Mapped[str | None] = so.mapped_column(sa.String(100))
    label: so.Mapped[str | None] = so.mapped_column(sa.String(100))
    year: so.Mapped[int | None] = so.mapped_column(sa.Integer())
    release_group_mbid: so.Mapped[str | None] = so.mapped_column(
        sa.String(36), index=True, unique=True
    )

    band_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("band.id", ondelete="CASCADE"), index=True
    )

    band: so.Mapped["Band"] = so.relationship(back_populates="releases")
    tracks: so.Mapped[list["Track"]] = so.relationship(
        back_populates="release",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Track(TimestampMixin, Base):
    __tablename__ = "track"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    track_number: so.Mapped[int] = so.mapped_column(sa.Integer())
    length: so.Mapped[int | None] = so.mapped_column(sa.Integer())
    lyrics: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    mbid: so.Mapped[str | None] = so.mapped_column(sa.String(36), index=True, unique=True)
    position: so.Mapped[int | None] = so.mapped_column(sa.Integer())

    # Column/attribute kept as release_id/release so the API is unchanged.
    release_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("album.id", ondelete="CASCADE"), index=True
    )

    release: so.Mapped["Album"] = so.relationship(back_populates="tracks")


class Member(TimestampMixin, Base):
    __tablename__ = "member"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(150), index=True)
    mbid: so.Mapped[str | None] = so.mapped_column(sa.String(36), index=True, unique=True)

    band_links: so.Mapped[list["BandMember"]] = so.relationship(
        back_populates="member",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Genre(TimestampMixin, Base):
    """A curated hardcore sub-genre (e.g. NYHC, youth crew).

    Rows are seeded from `app.genres.CURATED_GENRES`, which is the source of
    truth; this table is a queryable cache of that vocabulary.
    """

    __tablename__ = "genre"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    slug: so.Mapped[str] = so.mapped_column(sa.String(50), index=True, unique=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))

    band_links: so.Mapped[list["BandGenre"]] = so.relationship(
        back_populates="genre",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class BandGenre(TimestampMixin, Base):
    """Association between a Band and a Genre, carrying the MB tag vote count."""

    __tablename__ = "band_genre"

    band_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("band.id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True
    )
    # MusicBrainz tag vote count; lets us rank a band's primary genre / facets.
    vote_count: so.Mapped[int] = so.mapped_column(sa.Integer(), default=0, server_default="0")

    band: so.Mapped["Band"] = so.relationship(back_populates="genres")
    genre: so.Mapped["Genre"] = so.relationship(back_populates="band_links")

    @property
    def slug(self) -> str:
        # Lets the {slug, name} response schema validate straight off the link.
        return self.genre.slug

    @property
    def name(self) -> str:
        return self.genre.name


class BandMember(TimestampMixin, Base):
    """Association between a Band and a Member, carrying the member's role."""

    __tablename__ = "band_member"

    band_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("band.id", ondelete="CASCADE"), primary_key=True
    )
    member_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("member.id", ondelete="CASCADE"), primary_key=True
    )
    role: so.Mapped[str | None] = so.mapped_column(sa.String(100))

    band: so.Mapped["Band"] = so.relationship(back_populates="members")
    member: so.Mapped["Member"] = so.relationship(back_populates="band_links")

    @property
    def name(self) -> str:
        # Lets the {name, role} response schema validate straight off the link.
        return self.member.name
