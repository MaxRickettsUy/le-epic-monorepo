"""Phase 3 schema cleanup

- Drop legacy `review` / `user` tables (reviews out of MVP).
- Rename `release` -> `album`; `mbid` -> `release_group_mbid`.
- Recreate band/track FKs with ON DELETE CASCADE.
- Add created_at / updated_at to band, album, track.
- Add `member` + `band_member` (membership with role).

Revision ID: c1d2e3f4a5b6
Revises: 7b725d5c40b4
Create Date: 2026-05-21
"""
import sqlalchemy as sa
from alembic import op

revision = "c1d2e3f4a5b6"
down_revision = "7b725d5c40b4"
branch_labels = None
depends_on = None

NOW = sa.text("now()")


def upgrade():
    # 1. Drop legacy review/user tables (review references both user and release).
    op.drop_table("review")
    op.drop_table("user")

    # 2. Rename release -> album and its identity objects.
    op.rename_table("release", "album")
    op.execute("ALTER SEQUENCE release_id_seq RENAME TO album_id_seq")
    op.execute("ALTER INDEX release_pkey RENAME TO album_pkey")
    op.execute("ALTER INDEX ix_release_band_id RENAME TO ix_album_band_id")

    # 3. mbid -> release_group_mbid (one row per release-group, not pressing).
    op.alter_column("album", "mbid", new_column_name="release_group_mbid")
    op.drop_index("ix_release_mbid", table_name="album")
    op.create_index(
        "ix_album_release_group_mbid", "album", ["release_group_mbid"], unique=True
    )

    # 4. Recreate FKs with ON DELETE CASCADE.
    op.drop_constraint("release_band_id_fkey", "album", type_="foreignkey")
    op.create_foreign_key(
        "album_band_id_fkey", "album", "band", ["band_id"], ["id"], ondelete="CASCADE"
    )
    op.drop_constraint("track_release_id_fkey", "track", type_="foreignkey")
    op.create_foreign_key(
        "track_release_id_fkey",
        "track",
        "album",
        ["release_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. Timestamps on existing tables.
    for table in ("band", "album", "track"):
        op.add_column(
            table,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=NOW,
                nullable=False,
            ),
        )
        op.add_column(
            table,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=NOW,
                nullable=False,
            ),
        )

    # 6. Member + band_member.
    op.create_table(
        "member",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("mbid", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_member_name", "member", ["name"])
    op.create_index("ix_member_mbid", "member", ["mbid"], unique=True)

    op.create_table(
        "band_member",
        sa.Column(
            "band_id",
            sa.Integer(),
            sa.ForeignKey("band.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "member_id",
            sa.Integer(),
            sa.ForeignKey("member.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )


def downgrade():
    op.drop_table("band_member")
    op.drop_index("ix_member_mbid", table_name="member")
    op.drop_index("ix_member_name", table_name="member")
    op.drop_table("member")

    for table in ("track", "album", "band"):
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")

    op.drop_constraint("track_release_id_fkey", "track", type_="foreignkey")
    op.drop_constraint("album_band_id_fkey", "album", type_="foreignkey")

    op.drop_index("ix_album_release_group_mbid", table_name="album")
    op.alter_column("album", "release_group_mbid", new_column_name="mbid")
    op.create_index("ix_release_mbid", "album", ["mbid"], unique=True)

    op.execute("ALTER INDEX ix_album_band_id RENAME TO ix_release_band_id")
    op.execute("ALTER INDEX album_pkey RENAME TO release_pkey")
    op.execute("ALTER SEQUENCE album_id_seq RENAME TO release_id_seq")
    op.rename_table("album", "release")

    op.create_foreign_key(
        "release_band_id_fkey", "release", "band", ["band_id"], ["id"]
    )
    op.create_foreign_key(
        "track_release_id_fkey", "track", "release", ["release_id"], ["id"]
    )

    # Recreate legacy user/review tables.
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=True),
        sa.Column("token", sa.String(32), nullable=True),
        sa.Column("token_expiration", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_user_username", "user", ["username"], unique=True)
    op.create_index("ix_user_email", "user", ["email"], unique=True)
    op.create_index("ix_user_token", "user", ["token"], unique=True)

    op.create_table(
        "review",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.String(500), nullable=False),
        sa.Column(
            "release_id",
            sa.Integer(),
            sa.ForeignKey("release.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
        ),
    )
    op.create_index("ix_review_release_id", "review", ["release_id"])
    op.create_index("ix_review_user_id", "review", ["user_id"])
