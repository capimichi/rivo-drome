"""Create track table

Revision ID: 003
Revises: 002
Create Date: 2026-07-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "track",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.Column("album_id", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("track_number", sa.Integer(), nullable=True),
        sa.Column("deezer_id", sa.Integer(), nullable=True),
        sa.Column("local_path", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["artist_id"], ["artist.id"]),
        sa.ForeignKeyConstraint(["album_id"], ["album.id"]),
        sa.UniqueConstraint("deezer_id"),
    )
    op.create_index(op.f("ix_track_title"), "track", ["title"])


def downgrade() -> None:
    op.drop_index(op.f("ix_track_title"), table_name="track")
    op.drop_table("track")
