"""Create album table

Revision ID: 002
Revises: 001
Create Date: 2026-07-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import BigInteger


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "album",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.Column("cover_url", sa.String(512), nullable=True),
        sa.Column("deezer_id", BigInteger(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["artist_id"], ["artist.id"]),
        sa.UniqueConstraint("deezer_id"),
    )
    op.create_index(op.f("ix_album_title"), "album", ["title"])


def downgrade() -> None:
    op.drop_index(op.f("ix_album_title"), table_name="album")
    op.drop_table("album")
